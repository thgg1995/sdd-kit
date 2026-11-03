# LocalStack — limitações conhecidas e contornos

Observado com LocalStack Community 4.9.2 (2026-10-27). Confirme ao mudar de versão e mantenha esta lista atualizada.

## Imagem e licença
- `localstack/localstack:latest` exige `LOCALSTACK_AUTH_TOKEN` (conta LocalStack). Sem token, fixe a tag da Community (`4.9`).
- Para executar Lambdas, monte o socket do Docker no contêiner (`/var/run/docker.sock`).

## Apontar ferramentas sem editar os repositórios
- Variáveis de ambiente: `AWS_ENDPOINT_URL=http://localhost:4566`, `AWS_ACCESS_KEY_ID=test`, `AWS_SECRET_ACCESS_KEY=test`, `AWS_REGION=us-east-1`. Terraform (provider aws ≥ 5), boto3 e AWS CLI respeitam `AWS_ENDPOINT_URL`.

## O que não funciona (e o contorno)
| Limitação | Contorno | Impacto |
|---|---|---|
| Runtime Lambda `python3.14` rejeitado | validar o handler real em processo (importando o módulo) | empacotamento, agendamento e configuração de invocação não exercitados |
| CloudWatch `DescribeAlarms` devolve 500 | `terraform apply` com `-target`, excluindo os alarmes | alarmes só validados nos testes do Terraform |
| IAM não é aplicado na Community | injetar falha por outro meio (ex.: remover o recurso de destino) | permissões negadas não são testáveis |
| `aws_dynamodb_table` fica *tainted* após o apply (tabela ACTIVE) | `terraform untaint <recurso>` | nenhum |

## O que funciona
- Step Functions com `QueryLanguage: JSONata`, integração `aws-sdk:sqs` e `dynamodb:putItem` condicional.
- SQS standard com redrive para DLQ.
