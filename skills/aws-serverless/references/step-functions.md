# Step Functions — detalhes

Ler quando a tarefa cria ou altera um fluxo Step Functions.

## Padrão SQS → DynamoDB sem Lambda
1. `aws-sdk:sqs:receiveMessage` (`MaxNumberOfMessages` ≤ 10, `WaitTimeSeconds` 0).
2. Choice: sem `Messages` → Succeed.
3. Map inline (`MaxConcurrency` ≤ 10) por mensagem:
   - Ler o corpo: `Parallel` de um ramo só com um `Pass` `$parse($states.input.Body)` dentro e o `Catch` `States.QueryEvaluationError` **no `Parallel`** → caminho de inválida (padrão abaixo). Nunca `Catch` no `Pass`: o ASL fica inválido.
   - Choice de validação (ex.: `$type(body) = "object" and $exists(body.id)`).
   - `arn:aws:states:::dynamodb:putItem` com `ConditionExpression attribute_not_exists(<pk>)`; `Catch DynamoDB.ConditionalCheckFailedException` = já existe (idempotente).
   - `aws-sdk:sqs:deleteMessage` com o `ReceiptHandle` da própria leitura, só depois da escrita.
   - Inválida: `aws-sdk:sqs:sendMessage` para a DLQ e depois `deleteMessage`; falha no envio → não remover (a redrive leva à DLQ).
   - Saída do item: identificadores e `status`, nunca o corpo.
4. Choice: algum status de falha → Fail com `Cause` = `$string({...identificadores...})`.

## Capturar erro de expressão (`Pass` não aceita `Catch`)
`Catch` e `Retry` só existem em `Task`, `Parallel` e `Map`. Para tratar falha de uma expressão JSONata (ex.: corpo que não é JSON), envolva o `Pass` num `Parallel` de um ramo e leia o resultado em `$states.result[0]` (a saída do `Parallel` é uma lista, uma posição por ramo):
```json
"ParseBody": {
  "Type": "Parallel",
  "Branches": [{
    "StartAt": "Parse",
    "States": { "Parse": { "Type": "Pass", "Output": "{% $parse($states.input.Body) %}", "End": true } }
  }],
  "Assign": { "messageId": "{% $states.input.MessageId %}", "body": "{% $states.result[0] %}" },
  "Catch": [{
    "ErrorEquals": ["States.QueryEvaluationError"],
    "Assign": { "messageId": "{% $states.input.MessageId %}", "body": null },
    "Next": "SendToDlq"
  }],
  "Next": "IsValid"
}
```
- Usado na feature 001 (execução 3): passou no `terraform test` (estrutura), no reviewer e no caminho de sucesso do QA no LocalStack.
- `> Não verificado: o Catch do Parallel capturando o States.QueryEvaluationError do ramo na AWS real — no LocalStack 4.9 o erro vira States.Runtime e nenhum Catch o captura. Verificar com aws stepfunctions test-state (estado ParseBody, corpo "nao-json") ou validate-state-machine-definition antes de fixar.`

## Conversão JSON → atributos DynamoDB (JSONata)
Função recursiva no próprio estado, por tipo: string → `{"S": v}`; number → `{"N": $string(v)}`; boolean → `{"BOOL": v}`; null → `{"NULL": true}`; array → `{"L": [$map(v, f)]}`; object → `{"M": $merge([$each(v, function($x, $k){ {$k: f($x)} })])}` (objeto vazio → `{"M": {}}`).
Comprovar com `test-state` antes de usar: aninhamento, objeto/lista vazios, números decimais e grandes.

## Nomes de erro
- Integração otimizada DynamoDB: `DynamoDB.<Exceção>` (ex.: `DynamoDB.ConditionalCheckFailedException`).
- Integrações `aws-sdk`: `<Serviço>.<Exceção>` com o prefixo do serviço do SDK; confirme o nome exato com `test-state` antes de fixar no `Catch`.
- Avaliação JSONata: `States.QueryEvaluationError`; tempo: `States.Timeout`; genérico: `States.ALL` (sempre por último).

## Testes
- `terraform test` (plan + mock): tipo, `QueryLanguage`, `jsondecode(definition)` com os estados esperados, ausência de `Resource` Lambda.
- `aws stepfunctions validate-state-machine-definition --definition file://...` (precisa de credenciais, não cria recurso).
- `aws stepfunctions test-state --definition <estado> --role-arn <role> --input <json>` para estados com integração, inclusive os caminhos de `Catch`.
- Ponta a ponta (QA): enviar mensagens à fila, `start-execution`, conferir tabela, filas e `describe-execution` (`status`, `error`, `cause`).

## Custos (referência)
STANDARD cobra por transição de estado (cada estado do Map conta por item). Estime transições × execuções/dia no `research.md`.
