# Módulos da lib

Desenho recomendado de cada módulo. Assinaturas são ponto de partida: o que vale é o `CATALOGO.md` da lib. Os trechos de código abaixo foram executados com Python 3.14, boto3 1.43 e `Stubber`.

## Layout
```
src/<pacote>/
  __init__.py      # __version__ e reexportação pública (__all__)
  clients.py       # fábrica de clientes com configuração padrão; error_code()
  logs.py          # JsonFormatter, configure_logging()
  sqs.py  s3.py  dynamodb.py  secrets.py  ssm.py  sts.py
  py.typed
tests/             # um test_<módulo>.py por módulo + test_catalogo.py
CATALOGO.md  CHANGELOG.md
```
Um módulo por serviço. Crie o módulo só quando a primeira função dele for necessária.

## clients — configuração única de timeouts e retentativas
```python
DEFAULT_CONFIG = Config(connect_timeout=2, read_timeout=5, retries={"mode": "standard", "max_attempts": 3})

def client(service: str, *, config: Config | None = None, region_name: str | None = None) -> Any:
    return boto3.client(service, config=config or DEFAULT_CONFIG, region_name=region_name)

def error_code(exc: BaseException) -> str:
    if isinstance(exc, ClientError):
        return str(exc.response.get("Error", {}).get("Code", "ClientError"))
    return type(exc).__name__
```
- O consumidor que precisa de outra política (ex.: uma tentativa só, como na feature 001) passa `config=`; a lib não decide por ele.
- `error_code` é o que vai para log e métrica: nunca a mensagem nem a resposta da AWS.
- Cache de cliente (`functools.cache` sobre `client`) só se o catálogo disser, com `client.cache_clear()` nos testes.

## sqs
- `send_batch(queue_url, bodies, *, client) -> list[SendFailure]`: lotes de 10 (`SendMessageBatch`), ids = posição em `bodies`, devolve `Failed`.
```python
def send_batch(queue_url: str, bodies: Sequence[str], *, client: SQSClient) -> list[SendFailure]:
    failures: list[SendFailure] = []
    for offset, chunk in enumerate(_chunks(bodies, 10)):
        entries = [{"Id": str(offset * 10 + i), "MessageBody": b} for i, b in enumerate(chunk)]
        resp = client.send_message_batch(QueueUrl=queue_url, Entries=entries)
        failures += [SendFailure(f["Id"], f["Code"]) for f in resp.get("Failed", [])]
    return failures
```
- Limites: 10 mensagens por lote; 256 KiB por mensagem e por lote (a lib não divide mensagem; recusa ou documenta).
- Receber e apagar: `receive(queue_url, *, client, max_messages=10, wait_seconds=20)` e `delete_batch(queue_url, receipt_handles, *, client)`, este também em lotes de 10 e devolvendo as falhas.
- FIFO: `MessageGroupId`/`MessageDeduplicationId` como parâmetros opcionais por nome, nunca derivados de conteúdo de negócio pela lib.

## s3
- `get_bytes(bucket, key, *, client) -> bytes`, `put_bytes(bucket, key, data, *, client, content_type=None)`, `get_json`/`put_json` sobre elas (UTF-8).
- `list_keys(bucket, prefix, *, client) -> Iterator[str]`: com paginador (`get_paginator("list_objects_v2")`), nunca uma página só.
- `presigned_get(bucket, key, *, client, expires_seconds=900) -> str`: expiração sempre explícita.
- Objeto ausente: `ClientError` com código `NoSuchKey` (em `get_object`) ou `404` (em `head_object`); a função documenta qual dos dois devolve.

## dynamodb
- Prefira o cliente de baixo nível (tipos explícitos) ou o `resource`, um só por lib; registre a escolha no catálogo.
- `batch_put(table, items, *, client, max_rounds=3) -> list[item]`: lotes de 25, reenvia `UnprocessedItems` até `max_rounds` e devolve o que sobrou.
```python
def batch_put(table: str, items: Sequence[Mapping[str, Any]], *, client: DynamoDBClient, max_rounds: int = 3) -> list[Mapping[str, Any]]:
    pending = [{"PutRequest": {"Item": dict(it)}} for it in items]
    rounds = 0
    while pending and rounds < max_rounds:
        rounds += 1
        nxt: list[Any] = []
        for chunk in _chunks(pending, 25):
            resp = client.batch_write_item(RequestItems={table: list(chunk)})
            nxt += resp.get("UnprocessedItems", {}).get(table, [])
        pending = nxt
    return [p["PutRequest"]["Item"] for p in pending]
```
- Reenvio de `UnprocessedItems` deve esperar entre rodadas (backoff exponencial curto) em produção; o exemplo omite a espera para o teste.
- `query_all(..., *, client) -> Iterator[item]`: segue `LastEvaluatedKey` até o fim.
- `put_if_absent(table, item, key_attr, *, client) -> bool`: `ConditionExpression="attribute_not_exists(<key_attr>)"`; `ConditionalCheckFailedException` → `False` (idempotência).

## secrets (Secrets Manager) e ssm (Parameter Store)
```python
_cache: dict[str, tuple[float, str]] = {}

def get_secret(secret_id: str, *, client: SecretsManagerClient, ttl_seconds: float = 300) -> str:
    now = time.monotonic()
    hit = _cache.get(secret_id)
    if hit and now - hit[0] < ttl_seconds:
        return hit[1]
    value = client.get_secret_value(SecretId=secret_id)["SecretString"]
    _cache[secret_id] = (now, value)
    return str(value)

def clear_secret_cache() -> None:
    _cache.clear()
```
- `get_secret_json(secret_id, *, client, ttl_seconds=300) -> dict[str, Any]` sobre `get_secret`.
- Cache com TTL por processo (Lambda reaproveita o processo entre invocações): o TTL é o atraso máximo para enxergar uma rotação; documente-o.
- Nunca registrar o valor, nem em exceção (`raise ... from None` se a mensagem puder conter o segredo).
- `ssm.get_parameter(name, *, client, decrypt=True, ttl_seconds=300) -> str` no mesmo padrão; vários parâmetros: `get_parameters_by_path` com paginador.

## sts
```python
def assume_role_session(role_arn: str, session_name: str, *, client: STSClient, duration_seconds: int = 900) -> boto3.Session:
    creds = client.assume_role(RoleArn=role_arn, RoleSessionName=session_name, DurationSeconds=duration_seconds)["Credentials"]
    return boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )
```
- `session_name` identifica quem assumiu (aparece no CloudTrail): o consumidor passa algo rastreável (aplicação + correlação), 2–64 caracteres `[\w+=,.@-]`.
- `external_id` opcional por nome, para papéis de outra conta.
- A sessão expira em `duration_seconds`: para processos longos, a função recebe o papel e recria a sessão antes de expirar (ou use credenciais renováveis do botocore — `> Não verificado: RefreshableCredentials como API pública estável — conferir na documentação do botocore antes de usar`).
- `caller_identity(*, client) -> str` (ARN) para diagnóstico; nunca registre as credenciais.

## logs — padrão de log estruturado
```python
class JsonFormatter(logging.Formatter):
    RESERVED = set(vars(logging.makeLogRecord({})))

    def format(self, record: logging.LogRecord) -> str:
        out = {"level": record.levelname, "logger": record.name, "message": record.getMessage()}
        out.update({k: v for k, v in vars(record).items() if k not in self.RESERVED and k != "message"})
        return json.dumps(out, ensure_ascii=False, default=str)
```
- Os campos de contexto vêm de `extra={...}` (como a feature 001 já faz), sempre os mesmos nomes entre aplicações: `correlation_id`, `error_code`, `error_type` e os da skill `observability`.
- `configure_logging(level="INFO")`: aplica o formatter ao logger raiz uma vez (idempotente); chamado pela aplicação no início, nunca no import da lib.
- Lambda com formato de log JSON configurado na função: o runtime já serializa `extra`. Nesse caso a aplicação não chama `configure_logging`; a lib só garante os nomes dos campos. `> Não verificado: comportamento de extra com LoggingConfig JSON do runtime Python da Lambda — conferir num deploy de teste ou na documentação da AWS.`
- Exceção: `logger.error(..., extra={"error_code": error_code(exc)})`, sem `exc_info` quando a mensagem da AWS puder conter dado sensível.
