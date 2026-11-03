# Testes da lib e dos consumidores

## Na lib: `botocore.stub.Stubber`, sem rede
O `Stubber` vem com o botocore (sem dependência nova) e valida os parâmetros da chamada contra o modelo do serviço.
```python
from botocore.stub import Stubber
from <pacote> import clients, sqs


def test_send_batch_divide_em_lotes_e_devolve_falhas() -> None:
    client = clients.client("sqs", region_name="us-east-1")
    with Stubber(client) as st:
        st.add_response("send_message_batch", {"Successful": [], "Failed": [{"Id": "3", "SenderFault": True, "Code": "InvalidMessageContents"}]})
        st.add_response("send_message_batch", {"Successful": [{"Id": "10", "MessageId": "m", "MD5OfMessageBody": "x"}], "Failed": []})
        falhas = sqs.send_batch("https://sqs.us-east-1.amazonaws.com/123456789012/q", [f"b{i}" for i in range(11)], client=client)
        st.assert_no_pending_responses()
    assert falhas == [sqs.SendFailure("3", "InvalidMessageContents")]
```
- Erro da AWS: `st.add_client_error("get_secret_value", service_error_code="ResourceNotFoundException", http_status_code=400)` e confira `clients.error_code(exc)`.
- Conferir parâmetros enviados: terceiro argumento de `add_response` (`expected_params`), ex.: `{"SecretId": "app/db"}`.
- Cache: duas chamadas com uma única resposta enfileirada + `assert_no_pending_responses()`; limpe o cache (`clear_*`) num fixture `autouse`.
- `region_name` sempre explícito nos testes (sem depender de `AWS_DEFAULT_REGION`); nenhuma credencial real é necessária com o `Stubber`.
- Por função pública: sucesso, erro da AWS e limite (lote cheio + 1, segunda página, `UnprocessedItems`).

## Nos consumidores
- Não reteste a lib. Teste a regra da aplicação com um *fake* da função da lib (ou do cliente injetado), como a feature 001 faz com `tests/unit/fakes.py`.
- Teste de integração (LocalStack, papel qa) exercita a lib de verdade junto com o consumidor.
- Mudou a lib na mesma feature: o consumidor roda os testes contra a versão local dela (`references/consumo.md`).
