# Valores entre repositórios

Aplica-se quando um repositório publica um valor (URL de fila, nome de tabela, ARN) que outro repositório lê no próprio Terraform.

> Não verificado: os blocos HCL deste arquivo — `terraform validate` numa raiz com eles; o consumidor, com `terraform test` e `override_data` (`references/testes.md`).

## Regras
- O dono publica em `aws_ssm_parameter` do tipo `String`, sob `/<dominio>/<env>/v<major>/<nome>`. O consumidor lê por `data "aws_ssm_parameter"` e injeta onde precisa (ex.: variável de ambiente da função, na `aws-serverless`).
- O parâmetro é contrato entre repositórios: arquivo em `contracts/` com `owner`, `consumers` e `version` (§3).
- Quebra (outro formato, outro significado) → novo prefixo `v<major+1>`, convivendo com o anterior até o último consumidor migrar (§4).
- Nunca `terraform_remote_state` entre repositórios de donos diferentes: o consumidor passaria a depender da estrutura interna do estado do outro. Nunca valor copiado à mão.

## Produtor
```hcl
# A fila aws_sqs_queue.pedidos é do próprio repositório.
resource "aws_ssm_parameter" "url_fila_pedidos" {
  name  = "/exemplo/${var.ambiente}/v1/url-fila-pedidos"
  type  = "String"
  value = aws_sqs_queue.pedidos.url
}
```

## Consumidor
```hcl
data "aws_ssm_parameter" "url_fila_pedidos" {
  name = "/exemplo/${var.ambiente}/v1/url-fila-pedidos"
}

locals {
  # Vai para a função como variável de ambiente (aws-serverless).
  url_fila_pedidos = data.aws_ssm_parameter.url_fila_pedidos.value
}
```
