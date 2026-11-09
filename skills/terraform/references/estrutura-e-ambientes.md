# Estrutura e ambientes

Aplica-se ao criar um repositório de IaC, a pasta `infra/` de um serviço ou um ambiente novo.

> Não verificado: os blocos HCL deste arquivo — numa pasta com eles, `terraform init -backend=false`, `terraform fmt -check` e `terraform validate`.

## Layouts
Serviço com infra (a aplicação segue a skill da stack):
```text
<repo>/
  src/  tests/  ...            # aplicação
  infra/                       # raiz Terraform do serviço
    versions.tf  providers.tf  backend.tf  variables.tf  outputs.tf  locals.tf
    fila.tf  tabela.tf  ...    # um arquivo por grupo de recursos
    envs/dev.tfvars  envs/dev.backend.hcl  envs/prd.tfvars  envs/prd.backend.hcl
    tests/tabela.tftest.hcl
```
- Repositório só de IaC: com um componente, os arquivos de `infra/` ficam na raiz do repositório; com mais de um, uma pasta por componente (`<componente>/`), cada uma com o próprio estado.
- Repositório de módulos: `modules/<nome>/` (`references/modulos.md`).

| Arquivo | Contém |
|---|---|
| `versions.tf` | `required_version` e `required_providers` |
| `providers.tf` | o provider: região, conta permitida e tags padrão |
| `backend.tf` | o backend `s3` parcial |
| `variables.tf` / `outputs.tf` | todas as variáveis / todos os outputs da raiz |
| `locals.tf` | nome do serviço, dono e prefixo dos nomes |
| `<grupo>.tf` | os recursos de um grupo (fila e DLQ, tabela, função) e as políticas deles |
| `envs/<env>.tfvars` | o que muda entre ambientes: conta, região, tamanhos; nunca segredo |
| `envs/<env>.backend.hcl` | bucket, chave e região do estado do ambiente |

## Arquivos-base
```hcl
# versions.tf
terraform {
  required_version = "= 1.11.4" # a versão exata em uso; a pipeline usa a mesma

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

```hcl
# providers.tf
provider "aws" {
  region              = var.regiao
  allowed_account_ids = [var.conta_id]

  default_tags {
    tags = {
      service = local.servico
      env     = var.ambiente
      owner   = local.dono
    }
  }
}
```

```hcl
# backend.tf: bucket, chave e região vêm de envs/<env>.backend.hcl
terraform {
  backend "s3" {
    use_lockfile = true
    encrypt      = true
  }
}
```

```hcl
# variables.tf
variable "ambiente" {
  type        = string
  description = "Ambiente de destino."

  validation {
    condition     = contains(["dev", "hml", "prd"], var.ambiente) # TIME: nomes dos ambientes
    error_message = "ambiente deve ser dev, hml ou prd."
  }
}

variable "conta_id" {
  type        = string
  description = "Conta AWS do ambiente; o provider recusa qualquer outra."

  validation {
    condition     = can(regex("^[0-9]{12}$", var.conta_id))
    error_message = "conta_id deve ter 12 dígitos."
  }
}

variable "regiao" {
  type        = string
  description = "Região AWS do ambiente."
}
```

```hcl
# locals.tf
locals {
  servico = "<servico>"
  dono    = "<time>"
  prefixo = "${local.servico}-${var.ambiente}"
}
```

```hcl
# envs/dev.tfvars
ambiente = "dev"
conta_id = "000000000000"
regiao   = "<regiao>"
```

```hcl
# envs/dev.backend.hcl
bucket = "<bucket de estado da conta>"
key    = "<componente>/terraform.tfstate"
region = "<regiao>"
```

## Comandos
- Por ambiente: `terraform init -input=false -backend-config=envs/dev.backend.hcl` e `terraform plan -input=false -var-file=envs/dev.tfvars -out=tfplan`.
- Trocar de ambiente na mesma pasta: `terraform init -reconfigure -backend-config=envs/<env>.backend.hcl`.
- Sem credenciais, só para validar e testar: `terraform init -backend=false`.

## Ambiente novo
1. `envs/<env>.tfvars` e `envs/<env>.backend.hcl`.
2. O nome do ambiente na `validation` de `ambiente`.
3. O bucket de estado da conta, se ainda não existe (`references/estado.md`).
4. As roles da pipeline na conta e os jobs do ambiente (`references/pipeline.md`).
