---
name: aws-serverless
description: Padrões para aplicações serverless AWS com Terraform — função Lambda (Python), fluxo Step Functions com integrações diretas, agendamento (EventBridge Scheduler) e troca de valores entre repositórios. Use quando a tarefa cria ou altera uma função Lambda, um fluxo Step Functions, um agendamento ou valores compartilhados entre estados Terraform.
---

# AWS serverless (Lambda, Step Functions, Scheduler)

Complementa `aws-infra` (IaC, IAM, segredos, criptografia) e `python-backend` (código Python). Em conflito, vale a constitution.

## Estrutura do repositório
- Repositório de serviço (código + infra): `src/<pacote>/`, `tests/`, `infra/` (raiz Terraform), `docs/arquitetura.md`.
- Repositório só de IaC: a raiz é a raiz Terraform; um `.tf` por grupo de recursos; definições de fluxo em `state_machine/*.asl.json`.
- `versions.tf` com `required_version` exato da stack e `.terraform.lock.hcl` versionado; backend `s3` com configuração parcial (`-backend-config` por ambiente).
- Tags por `default_tags` do provider.

## Função Lambda (Python)
- Handler fino (`handler.py`): lê configuração, cria clientes, chama a regra, registra o resultado. Regra pura em módulo próprio, com portas `typing.Protocol`; adaptadores boto3 em `aws.py`.
- Configuração só por variáveis de ambiente definidas no Terraform; validada no início da invocação; ausente → erro sem efeito colateral.
- Clientes boto3 com `botocore.config.Config(connect_timeout, read_timeout, retries)` explícitos (§9). Retentativa do SDK só quando a operação é idempotente e o requisito permite.
- Sem async: para paralelismo de chamadas AWS, `ThreadPoolExecutor` com um cliente compartilhado e `max_pool_connections` ≥ workers.
- Logs: `logging` da stdlib com `extra`, e `logging_config { log_format = "JSON" }` na função. Nunca logar evento, payload nem respostas completas da AWS.
- Erro de negócio que deve aparecer na métrica `Errors` → levantar exceção depois de registrar.
- Empacotamento: `archive_file` de `src/`; sem dependências de runtime quando o `boto3` do runtime basta (o dev testa com o `boto3` travado no lockfile). Dependência nativa → build para a arquitetura da função (`uv pip install --python-platform`).
- Log group declarado no Terraform com retenção; função com `timeout` e `memory_size` explícitos; `arm64` salvo dependência que impeça.
- Invocação assíncrona (Scheduler, EventBridge, S3, SNS): declare `aws_lambda_function_event_invoke_config` com `maximum_retry_attempts` decidido no plano (o padrão da AWS é 2).

## Agendamento
- `aws_scheduler_schedule` com `rate(...)`/`cron(...)`, `flexible_time_window { mode = "OFF" }` e `retry_policy` explícito.
- Role do Scheduler só com `lambda:InvokeFunction` no ARN da função.

## Step Functions
- `QueryLanguage: JSONata`; ASL em arquivo JSON renderizado por `templatefile`; nada inline em HCL.
- Prefira integrações diretas (`arn:aws:states:::dynamodb:*`, `arn:aws:states:::aws-sdk:*`) a Lambda quando não há regra além de mapear dados.
- STANDARD quando é preciso status consultável por execução, histórico ou início exatamente uma vez; EXPRESS para alto volume e curta duração com observabilidade por logs.
- Toda Task com `TimeoutSeconds`; `TimeoutSeconds` na execução.
- `Retry` só em erro transitório de operação idempotente; `Catch` com nomes de erro exatos e um `States.ALL` final que leve a um estado explícito.
- `Catch` e `Retry` só existem em `Task`, `Parallel` e `Map`. Expressão que pode falhar num `Pass` (ex.: `$parse`) → `Parallel` de um ramo com o `Catch` nele (`references/step-functions.md`).
- Falha de lote: processe todos os itens e termine em `Fail` com `Error` fixo e `Cause` estruturado só com identificadores.
- Dados pessoais: sem `includeExecutionData`; lembre que o histórico do STANDARD guarda entradas/saídas por 90 dias.
- Detalhes (padrões SQS → DynamoDB, nomes de erro, conversão para atributos DynamoDB, testes): `references/step-functions.md`.
- Limites de serviço (256 KiB entre estados, precisão numérica do JSONata, SQS, Lambda, DynamoDB): o tech lead confere o pior caso de cada contrato com `references/limites.md` **antes** de congelá-lo.

## SQS
- Redrive (`maxReceiveCount`) é o mecanismo de tentativas; `redrive_allow_policy` na DLQ.
- Visibilidade > duração máxima do processamento de uma leitura.
- Retenção: na fila standard, a expiração na DLQ conta do envio original.
- Alarme da DLQ em `ApproximateNumberOfMessagesVisible` (não `NumberOfMessagesSent`, que ignora a redrive).

## Valores entre repositórios
- Produtor grava `aws_ssm_parameter` (String) sob `/<dominio>/<env>/v<major>/...`; consumidor lê por `data "aws_ssm_parameter"` no Terraform e injeta na função por variável de ambiente.
- Nunca `terraform_remote_state` entre repositórios de donos diferentes; nunca valores copiados à mão.
- Quebra → novo prefixo `v<major+1>` convivendo com o anterior.

## IAM (complementa `aws-infra`)
- Políticas por `data "aws_iam_policy_document"`; teste por `jsondecode` em `terraform test`.
- Ações que não aceitam recurso específico (`cloudwatch:PutMetricData`, `logs:*LogDelivery*`, `xray:Put*`) e o sufixo `:log-stream:*` exigem `*`: só com exceção registrada no plano.

## Testes
- Terraform: `terraform test` com `mock_provider "aws"` em modo `plan`; `override_data` para entradas de contrato; `run` nomeado com o ID do requisito.
- Python: `pytest` com `botocore.stub.Stubber` ou fakes das portas; sem rede.
- Fluxo: `aws stepfunctions validate-state-machine-definition` e `aws stepfunctions test-state` por estado; ponta a ponta no QA contra AWS real. Step Functions Local não é usado (sem JSONata).
