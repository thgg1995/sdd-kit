---
name: terraform
description: Como escrever, versionar, testar e aplicar IaC com Terraform no padrão do time — estrutura da raiz, versões, estado e ambientes, código HCL, proteção de dados, segredos, refatoração, testes e pipeline. Use quando o repositório tem stack terraform ou a tarefa cria ou altera arquivos .tf.
---

# Terraform

Complementa `aws-infra` (o que a AWS exige de cada recurso: IAM, segredos, criptografia, rede, tags, SQS) e `aws-serverless` (Lambda, Step Functions, agendamento). Em conflito, vale a constitution.

## Estrutura do repositório (constitution §20)
- Layouts (detalhe em `references/estrutura-e-ambientes.md`):
  - serviço com infra: a raiz Terraform fica em `infra/`, ao lado do código da aplicação;
  - repositório só de IaC: com um componente, a raiz do repositório; com mais de um, uma pasta por componente;
  - repositório de módulos: `modules/<nome>/` (`references/modulos.md`).
- Arquivos da raiz: `versions.tf`, `providers.tf`, `backend.tf`, `variables.tf`, `outputs.tf`, `locals.tf`, um `.tf` por grupo de recursos (ex.: `fila.tf`, `tabela.tf`), `envs/<env>.tfvars`, `envs/<env>.backend.hcl` e `tests/`.

## Versões (constitution §20)
- Terraform 1.11 ou mais novo: a skill usa o lock nativo do estado no S3 e os argumentos write-only.
- Raiz: `required_version` com a versão exata em uso (ex.: `= 1.11.4`), a mesma da pipeline. Módulo: `>= 1.11`.
- Provider em `required_providers`, com `source` e `version = "~> <major>.<minor>"`.
- `.terraform.lock.hcl` versionado, com os hashes das plataformas do time e da CI (`terraform providers lock -platform=linux_amd64 -platform=windows_amd64 -platform=darwin_arm64`).

## Estado e ambientes
- Backend `s3` com configuração parcial: `backend.tf` só com `use_lockfile = true` e `encrypt = true`; bucket, chave e região em `envs/<env>.backend.hcl`.
- Um estado por componente e ambiente. O mesmo código serve a todos os ambientes; o que muda entre eles fica em `envs/<env>.tfvars`.
- O provider recusa a conta errada: `allowed_account_ids = [var.conta_id]`.
- Tags pelo `default_tags` do provider, com as chaves obrigatórias da `aws-infra`.
- Valor que vem de outro repositório: `references/entre-repositorios.md`.

## Código
- Variável com `type` e `description`; com `validation` quando o valor tem domínio restrito (lista, formato, faixa).
- Conta, região, ARN e nome de ambiente nunca escritos no `.tf`: vêm de variável, de `data` ou de outro recurso.
- Nome de recurso a partir do prefixo de `locals.tf` (`"${local.servico}-${var.ambiente}"`).
- `for_each` para coleções, com chave estável; `count` só para ligar ou desligar um recurso (`var.x ? 1 : 0`).
- Política IAM por `jsonencode` de um objeto HCL, no próprio recurso, para o teste conseguir lê-la (`references/testes.md`). O conteúdo (ações, recursos, quando cabe `*`) segue a `aws-infra`.
- `depends_on` e `ignore_changes` só com o motivo em comentário.

## Proteção de dados (constitution §33)
- Recurso que guarda dado persistente (banco, tabela, bucket, volume, cofre de backup e a chave KMS que cifra esses dados) tem, em todos os ambientes:
  - `lifecycle { prevent_destroy = true }`;
  - a proteção do próprio serviço, quando existe: `deletion_protection` no RDS, `deletion_protection_enabled` no DynamoDB; bucket sem `force_destroy`.
- Destruir recurso protegido leva dois PRs: o primeiro só remove a proteção; o segundo remove o recurso.

## Segredos (constitution §21)
- O estado guarda em texto o valor de todo argumento, variável e output: segredo nunca vai em `tfvars`, `default`, output nem argumento comum.
- Segredo criado e guardado pelo próprio serviço quando ele oferece (ex.: `manage_master_user_password = true` no RDS); senão, por argumento write-only (`*_wo` com `*_wo_version`), alimentado por valor efêmero (`ephemeral`).
- Variável que recebe valor sensível: `sensitive = true`; se só alimenta argumento write-only, também `ephemeral = true`.

## Refatoração (constitution §20)
- Renomear ou mover recurso: bloco `moved`. Adotar recurso existente: bloco `import`. Tirar do estado sem destruir: bloco `removed` com `destroy = false`. Detalhe em `references/estado.md`.
- `-target` só no contorno registrado pelo QA (`qa-integration`, `references/localstack.md`).

## Testes (constitution §26, §29)
- `terraform test` com `mock_provider "aws"` e `command = plan` em todo `run`: nada é criado (`references/testes.md`).
- Cada `run` nomeado pelo requisito que verifica (`run "FR001_<caso>"`).
- Testa: cada `validation` (com `expect_failures`), cada política IAM, a proteção do serviço nos recursos do §33 e cada valor que vira contrato.
- `terraform fmt -check -recursive`, `terraform validate` e `terraform test` sem erro nem warning novo.

## Plan e apply (constitution §20)
- `plan` no PR. Em conta AWS, `apply` só pela pipeline, a partir do plano salvo (`terraform apply <arquivo>`); o QA aplica no ambiente de integração (`qa-integration`).
- Exclusão ou substituição de recurso aparece no resumo do PR.
- Pipeline no GitHub Actions, com credencial por OIDC: `references/pipeline.md`.

## No Desenho técnico (tech lead)
- `Estrutura`: o layout, os estados (componente × ambiente) e os arquivos.
- `Padrões`: módulos consumidos ou criados, com a versão.
- `Contratos`: valores publicados ou lidos de outros repositórios.
- `Convenções`: o prefixo dos nomes e os recursos protegidos (§33).

## Proibido
- Em conta AWS, recurso criado ou alterado fora do código (console, CLI da AWS) e estado alterado à mão (`terraform state`, `terraform import` pela linha de comando) (§20).
- Workspace do CLI para separar ambientes.
- `terraform_remote_state` entre repositórios de donos diferentes, e valor copiado à mão de outro estado.
- Segredo em `tfvars`, `default`, output ou argumento comum (§21).
- Bloco `provider` ou `backend` dentro de módulo.
- `apply` em conta AWS fora da pipeline ou de plano não revisado.

## Referências
- `references/estrutura-e-ambientes.md` — ler ao criar um repositório de IaC, a pasta `infra/` de um serviço ou um ambiente novo.
- `references/estado.md` — ler ao configurar o backend, migrar o estado, adotar recurso existente, ou renomear, mover ou esquecer um recurso.
- `references/modulos.md` — ler ao criar, consumir ou versionar um módulo.
- `references/testes.md` — ler ao escrever ou alterar um `terraform test`.
- `references/pipeline.md` — ler ao criar ou alterar a pipeline de IaC.
- `references/entre-repositorios.md` — ler quando um repositório publica ou lê valor de outro estado Terraform.
