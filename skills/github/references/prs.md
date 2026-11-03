# PRs para a base com todas as verificações verdes e sem aprovação

Usado no passo 5 de "Preparar a base": se houver algum, o humano é avisado e o fluxo PARA até ele decidir.

## Comando
```
gh pr list --repo <owner>/<repo> --base main --state open --limit 100 \
  --json number,title,url,isDraft,reviewDecision,statusCheckRollup \
  --jq '.[]
    | select(.isDraft | not)
    | select(.reviewDecision != "APPROVED")
    | select((.statusCheckRollup | length) > 0)
    | select(all(.statusCheckRollup[]; ((.conclusion // .state) as $s
        | $s == "SUCCESS" or $s == "NEUTRAL" or $s == "SKIPPED")))
    | "#\(.number) \(.title) \(.url) [revisão: \(if .reviewDecision == "" then "não exigida" else .reviewDecision end)]"'
```
> Não verificado: o filtro `--jq` (escrito com os campos de `gh pr list --json` do gh 2.103.3, sem autenticação para executar) — verificar na primeira execução contra um PR conhecido, comparando com `gh pr checks <n>` e `gh pr view <n> --json reviewDecision`.

## Como interpretar
- `statusCheckRollup`: uma entrada por verificação do último commit do PR.
  - execução de Actions (CheckRun): `status` (`QUEUED`, `IN_PROGRESS`, `COMPLETED`) e `conclusion` (`SUCCESS`, `FAILURE`, `NEUTRAL`, `SKIPPED`, `CANCELLED`, `TIMED_OUT`, `ACTION_REQUIRED`, `STALE`; vazio enquanto roda);
  - status de commit externo (StatusContext): `state` (`SUCCESS`, `FAILURE`, `ERROR`, `PENDING`, `EXPECTED`).
  - "todas verdes" = toda entrada concluída com `SUCCESS`, `NEUTRAL` ou `SKIPPED`. Qualquer pendente ou falha → o PR não entra na lista.
- `reviewDecision`: `APPROVED`, `CHANGES_REQUESTED`, `REVIEW_REQUIRED`, ou vazio quando o repositório não exige revisão. Entra na lista tudo que não é `APPROVED`.
- PR em rascunho (`isDraft`) não entra: ainda não pediu revisão.
- PR sem nenhuma verificação não entra: não há o que estar verde. Registre à parte, se houver.

## Conferir um PR específico
- Verificações: `gh pr checks <n> --repo <owner>/<repo> --json name,bucket,link` (`bucket`: `pass`, `fail`, `pending`, `skipping`, `cancel`; saída `8` = pendente).
- Revisão: `gh pr view <n> --repo <owner>/<repo> --json reviewDecision,reviews,mergeStateStatus`.

## Aviso ao humano
```
Antes de criar feature/<f> a partir de main em <owner>/<repo>, há PRs para main com todas as verificações verdes e sem aprovação:
#<n> <título> <url> [revisão: <REVIEW_REQUIRED|CHANGES_REQUESTED|não exigida>]
Se algum deles for mesclado depois, a feature nasce de uma base desatualizada.
Responda: "seguir" (cria a branch da base atual) ou "aguardar" (você aprova/mescla e eu atualizo a base antes de criar a branch).
```
