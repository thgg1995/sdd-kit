# GitHub Actions: saúde da base e acompanhamento depois do push

## Saúde da base (antes de criar a branch)
```
SHA=$(git -C <repo> rev-parse origin/main)
gh run list --repo <owner>/<repo> --commit "$SHA" --limit 20 \
  --json databaseId,workflowName,status,conclusion,url
```
- Nenhuma execução → o commit da base não dispara workflow (ou o repositório não tem Actions): registre "sem Actions".
- Alguma com `status` diferente de `completed` → em andamento: reporte e pare (não espere sozinho na preparação).
- Alguma `completed` com `conclusion` `failure`, `cancelled`, `timed_out` ou `startup_failure` → a base está quebrada: pare e reporte o workflow e o `url`.
- Todas `success`, `neutral` ou `skipped` → base saudável.

## Depois do push: achar as execuções
As execuções aparecem alguns segundos depois do push. Consulte a cada 10 s, por até 2 minutos:
```
gh run list --repo <owner>/<repo> --branch feature/<f> --commit <sha> --limit 20 \
  --json databaseId,workflowName,event,status,conclusion,url
```
- Nada depois de 2 minutos → os workflows não rodam em push nessa branch (ex.: só em `pull_request`). Reporte "nenhuma Action disparada pelo push" e pare de esperar.

## Esperar terminar
- OAuth (`gh auth login`) ou token clássico — uma execução por vez:
  `gh run watch <databaseId> --repo <owner>/<repo> --exit-status --compact --interval 30 > /dev/null; echo $?`
  (`0` = sucesso; diferente de `0` = falhou ou foi cancelada). Redirecione a saída: o modo watch redesenha a tela e gasta tokens.
- Token fine-grained (sem `run watch`): consulte a cada 30–60 s até `status` = `completed`:
  `gh run view <databaseId> --repo <owner>/<repo> --json status,conclusion,url`
- Limite de espera: 30 minutos por execução (ou o valor que o humano informar). Estourou → reporte "em andamento" com o `url` e pare.

## Em falha: só o trecho do erro
```
gh run view <databaseId> --repo <owner>/<repo> --json jobs \
  --jq '.jobs[] | select(.conclusion == "failure") | {job: .name, passos: [.steps[] | select(.conclusion == "failure") | .name]}'
gh run view <databaseId> --repo <owner>/<repo> --log-failed | tail -n 40
```
- Atribua a falha ao repositório e ao arquivo quando o log permitir (teste, lint, build, deploy).
- Falha de infraestrutura do runner (sem relação com o código, ex.: timeout de download) → reporte como tal; reexecutar (`gh run rerun`) só com pedido do humano.

## Campos úteis
- `gh run list --json`: `databaseId`, `workflowName`, `event`, `headBranch`, `headSha`, `status`, `conclusion`, `url`, `createdAt`.
- `gh run view --json`: os mesmos e `jobs` (com `steps`).
- `status`: `queued`, `in_progress`, `completed`, `waiting`, `requested`, `pending`, `action_required`.
