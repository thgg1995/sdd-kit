# Testes do Terraform

Aplica-se ao escrever ou alterar um `terraform test`.

> Não verificado: os blocos deste arquivo, inclusive o `override_during = plan` — numa raiz com eles e com os arquivos-base de `references/estrutura-e-ambientes.md`, `terraform init -backend=false` e `terraform test` (Terraform 1.11+).

## Como rodar
- Sem credenciais: `terraform init -backend=false`, depois `terraform validate` e `terraform test`.
- Um arquivo por grupo de recursos: `tests/<grupo>.tftest.hcl`.

## Provider simulado e `command = plan`
- `mock_provider "aws" {}` no topo do arquivo: nenhuma chamada à AWS.
- Todo `run` com `command = plan`. Nada é criado, nem no simulado, então o arquivo não tem limpeza no fim; a limpeza de um `run` que aplica esbarraria no `prevent_destroy` dos recursos do §33.
- No plan, atributo calculado pelo provider (ARN, id) fica desconhecido. Quando uma asserção depende dele, dê o valor com `override_resource` e `override_during = plan`.
- Data source que lê outro estado ou a conta (`aws_ssm_parameter`, `aws_caller_identity`): `override_data` com o valor do contrato, também com `override_during = plan`.

## Políticas IAM
O provider simulado também inventa a saída dos data sources: o `json` de um `aws_iam_policy_document` vira um texto aleatório, que o `jsondecode` não lê. Por isso a skill monta as políticas com `jsonencode` no próprio recurso, e o teste lê o atributo com `jsondecode`.

## O que cada raiz testa
- cada `validation` de variável, com um valor inválido e `expect_failures`;
- cada política IAM: as ações e os recursos;
- a proteção do serviço em cada recurso com dado persistente (§33). O `prevent_destroy` não aparece no plano: quem confere é o review;
- cada valor que vira contrato (output, parâmetro).

## Exemplo
```hcl
# tabela.tf
resource "aws_dynamodb_table" "pedidos" {
  name                        = "${local.prefixo}-pedidos"
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "id"
  deletion_protection_enabled = true

  attribute {
    name = "id"
    type = "S"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_iam_role" "leitor" {
  name = "${local.prefixo}-leitor"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "leitura_pedidos" {
  name = "leitura-pedidos"
  role = aws_iam_role.leitor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:GetItem", "dynamodb:Query"]
      Resource = [aws_dynamodb_table.pedidos.arn]
    }]
  })
}
```

```hcl
# tests/tabela.tftest.hcl
mock_provider "aws" {}

override_resource {
  target          = aws_dynamodb_table.pedidos
  override_during = plan
  values = {
    arn = "arn:aws:dynamodb:<regiao>:000000000000:table/exemplo-dev-pedidos"
  }
}

variables {
  ambiente = "dev"
  conta_id = "000000000000"
  regiao   = "<regiao>"
}

run "FR001_ambiente_desconhecido_e_recusado" {
  command = plan

  variables {
    ambiente = "qa"
  }

  expect_failures = [var.ambiente]
}

run "FR002_leitor_so_le_a_tabela_de_pedidos" {
  command = plan

  assert {
    condition     = jsondecode(aws_iam_role_policy.leitura_pedidos.policy).Statement[0].Action == ["dynamodb:GetItem", "dynamodb:Query"]
    error_message = "o leitor deve ter só GetItem e Query"
  }

  assert {
    condition     = jsondecode(aws_iam_role_policy.leitura_pedidos.policy).Statement[0].Resource == [aws_dynamodb_table.pedidos.arn]
    error_message = "a leitura deve se limitar à tabela de pedidos"
  }
}

run "FR003_tabela_protegida_contra_exclusao" {
  command = plan

  assert {
    condition     = aws_dynamodb_table.pedidos.deletion_protection_enabled
    error_message = "tabela com dado persistente precisa de proteção contra exclusão (§33)"
  }
}
```
