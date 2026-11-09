# Pipeline de IaC (GitHub Actions)

Aplica-se ao criar ou alterar a pipeline que valida, planeja e aplica a IaC.

> Não verificado: o workflow deste arquivo — `actionlint` e uma execução num repositório de teste; confira também as versões das actions.

## Etapas
- PR: `fmt -check`, `init`, `validate`, `test` e `plan` de cada ambiente, com as exclusões e substituições no resumo da execução.
- Merge na branch principal: `plan` salvo e `apply` desse plano, ambiente por ambiente (dev → hml → prd). O ambiente do GitHub de produção exige aprovação, e quem aprova lê o resumo do plan antes.
- Credencial por OIDC, sem chave de acesso guardada. Duas roles por conta, cada uma confiando só no `sub` do seu caso:
  - plan: leitura dos recursos e do estado, mais o arquivo de lock; confia no PR e na branch principal;
  - apply: escrita; confia só no ambiente do GitHub (`environment:<env>`).
- As permissões das roles seguem a `aws-infra`.
- O plano salvo guarda valores em texto: artefato com retenção de 1 dia, nunca anexado ao PR.
- `terraform_wrapper: false` no `setup-terraform`: o wrapper altera a saída e quebra o `terraform show -json`.
- No PR, o plan roda com `-lock=false`, porque não grava estado; no merge, com lock.

## Exemplo (um ambiente)
Outros ambientes repetem o par de jobs, com o próprio `AMBIENTE` e as próprias roles, encadeados por `needs`.

```yaml
name: iac

on:
  pull_request:
    paths: ["infra/**"]
  push:
    branches: [main]
    paths: ["infra/**"]

permissions:
  contents: read
  id-token: write

env:
  TF_VERSION: "1.11.4" # a mesma do required_version
  AMBIENTE: dev

defaults:
  run:
    working-directory: infra

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
          terraform_wrapper: false
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_ROLE_PLAN_DEV }}
          aws-region: ${{ vars.AWS_REGION }}
      - run: terraform fmt -check -recursive
      - run: terraform init -input=false -backend-config=envs/$AMBIENTE.backend.hcl
      - run: terraform validate
      - run: terraform test
      - run: terraform plan -input=false -lock=${{ github.event_name == 'push' }} -var-file=envs/$AMBIENTE.tfvars -out=tfplan
      - name: Exclusões e substituições no resumo
        run: |
          echo "### Exclusões e substituições ($AMBIENTE)" >> "$GITHUB_STEP_SUMMARY"
          terraform show -json tfplan \
            | jq -r '.resource_changes[] | select(.change.actions | index("delete")) | "- \(.change.actions | join("+")) \(.address)"' \
            >> "$GITHUB_STEP_SUMMARY"
      - if: github.event_name == 'push'
        uses: actions/upload-artifact@v4
        with:
          name: tfplan-${{ env.AMBIENTE }}
          path: infra/tfplan
          retention-days: 1

  apply:
    needs: plan
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: dev # em produção, ambiente do GitHub com aprovação obrigatória
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
          terraform_wrapper: false
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ vars.AWS_ROLE_APPLY_DEV }}
          aws-region: ${{ vars.AWS_REGION }}
      - uses: actions/download-artifact@v4
        with:
          name: tfplan-${{ env.AMBIENTE }}
          path: infra
      - run: terraform init -input=false -backend-config=envs/$AMBIENTE.backend.hcl
      - run: terraform apply -input=false tfplan
```
