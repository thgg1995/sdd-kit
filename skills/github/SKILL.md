---
name: github
description: Comunicação com o GitHub por git e GitHub CLI (gh) — acesso e autenticação, atualização da branch base, verificação de PRs pendentes de aprovação, criação da branch da feature, pull, push e acompanhamento das GitHub Actions. Use quando a tarefa envolve o remoto no GitHub: preparar a base antes de criar a branch, enviar commits ou acompanhar a pipeline de um push.
---

# GitHub (git + gh)

Complementa o processo do kit (`orquestrador.md` e os papéis em `.agents/roles/`; commits só em `feature/<f>`). Em conflito, vale o processo.
Validado com `gh` 2.103.3 e `git` 2.49.

## Regras que valem sempre
- **Ferramentas**: `git` para o repositório; `gh` para PRs e Actions. Sem `gh`, use a API REST (`references/autenticacao.md`); nunca raspe páginas web.
- **Saída curta**: sempre `--json <campos>` com `--jq`, `--compact` e `tail` em logs. Ambiente sem interação: `GH_PROMPT_DISABLED=1`, `GH_NO_UPDATE_NOTIFIER=1`, `GH_PAGER=cat`.
- **Base = `main`**, sempre: a verificação de PRs é contra `main` e a branch da feature nasce de `origin/main`. O remoto não tem `main` → pare e reporte; não use outra branch no lugar.
- **Proibido**, salvo pedido explícito do humano:
  - push na branch base, `--force` ou `--force-with-lease`, apagar branch remota, `git reset --hard` em trabalho não enviado;
  - aprovar, mesclar, fechar ou abrir PR; reexecutar ou cancelar workflow; mudar configuração do repositório, proteções de branch, secrets ou variáveis;
  - imprimir, gravar ou pedir token: nada de `gh auth status --show-token`, `--with-token` com o token na linha de comando, nem token em arquivo, log, `env.md` ou chat.
- **Commits**: nunca inclua segredos, `.env` nem artefatos de build; confira `git status --short` e `git diff --cached --stat` antes de commitar.

## 1. Acesso (antes de qualquer operação remota)
Verifique, nesta ordem, e pare no primeiro que faltar:
| Verificação | Comando | Se faltar |
|---|---|---|
| remoto é GitHub | `git -C <repo> remote get-url origin` | sem `origin` ou outro provedor → esta skill não se aplica |
| host | do URL do `origin` (`github.com` ou o host do GitHub Enterprise) | — |
| `gh` instalado | `gh --version` | é ferramenta da etapa `ambiente`, nunca do subagente |
| `gh` autenticado | `gh auth status --hostname <host> --active` | pedir ao humano (abaixo) |
| git consegue autenticar | `git -C <repo> ls-remote --heads origin main` | HTTPS: `gh auth setup-git --hostname <host>`; SSH: chave do humano |

**Pedir ao humano** (um lote só, pelo protocolo de repasse; nunca o token):
1. Confirmar o repositório `owner/repo` e a branch base de cada repositório.
2. Autenticar no próprio terminal: `gh auth login --hostname <host> --git-protocol https --web` (ou SSH, se já usa chave), ou deixar `GH_TOKEN` definido no ambiente da sessão do agente.
3. Permissões necessárias, conforme `references/autenticacao.md`: ler o repositório, PRs e Actions; escrever conteúdo (push), se o fluxo for enviar commits.
Registre no `env.md` só o resultado: `GitHub: <host>, gh <versão>, autenticado como <usuário>, protocolo <https|ssh>`.

## 2. Preparar a base (antes de criar `feature/<f>`)
1. `git -C <repo> fetch --prune --quiet origin`
2. Árvore limpa: `git -C <repo> status --porcelain` vazio. Sujo → pare e reporte (não descarte nada).
3. Base local igual à remota: `git -C <repo> rev-list --left-right --count main...origin/main`.
   - `0 0`: em dia. `0 N`: `git -C <repo> switch --quiet main && git -C <repo> merge --ff-only --quiet origin/main`.
   - `N 0` ou `N M` (commits locais na base) → pare e reporte: a base local divergiu.
4. **Saúde da base**: a última execução das Actions no commit de `origin/main` (`references/actions.md`, "Saúde da base"). Falhou ou em andamento → pare e reporte. Sem workflow → registre "sem Actions".
5. **PRs para a base com todas as verificações verdes e sem aprovação** (`references/prs.md`): havendo algum, **avise o humano com a lista e PARE**. Ele decide: seguir mesmo assim, ou aprovar e mesclar primeiro (depois, repita desde o passo 1).
6. A branch já existe (`git -C <repo> rev-parse --verify --quiet feature/<f>` ou `git -C <repo> ls-remote --heads origin feature/<f>`) → não recrie: continue nela e reporte.
7. Crie a partir da base remota atualizada: `git -C <repo> switch --quiet -c feature/<f> origin/main`.

## 3. Pull
- Atualizar a branch da feature: `git -C <repo> pull --ff-only --quiet origin feature/<f>`. Não avança rápido (alguém enviou commits) → pare e reporte, sem merge nem rebase por conta própria.
- Trazer a base para a feature, só quando pedido: `git -C <repo> merge --no-edit origin/main`; conflito → `git merge --abort` e reporte os arquivos.

## 4. Push e acompanhamento da pipeline
1. Antes: árvore limpa, branch atual = `feature/<f>`, nada na base. `git -C <repo> log --oneline origin/main..HEAD` mostra o que vai subir.
2. `git -C <repo> push --quiet -u origin feature/<f>` (sem `--force`). Rejeitado (non-fast-forward) → pare e reporte.
3. Guarde o commit: `git -C <repo> rev-parse HEAD`.
4. Acompanhe as Actions desse commit (`references/actions.md`): ache as execuções, espere terminar e, em falha, extraia só o trecho do erro.
5. Reporte uma linha por workflow: `<workflow>: <success|failure|cancelled> <url>`; em falha, o job, o passo e até 40 linhas do log.

## Retorno (para quem chamou a skill)
```
GitHub: <repo> | base main@<sha curto> <em dia|atualizada|divergente> | Actions da base: <ok|falha|sem>
PRs verdes sem aprovação: <nenhum | #n título url (um por linha)>
Branch: feature/<f> <criada|já existia> | Push: <não feito|<sha curto>> | Actions: <workflow: resultado url>
```

## Referências
- `references/autenticacao.md` — ler quando o `gh` não está autenticado, o push é negado, o host é GitHub Enterprise, ou é preciso usar a API sem `gh`.
- `references/prs.md` — ler no passo 5 de "Preparar a base": como listar e interpretar os PRs verdes sem aprovação.
- `references/actions.md` — ler para conferir a saúde da base ou acompanhar a pipeline depois de um push.
