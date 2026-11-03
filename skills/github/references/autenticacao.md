# Autenticação e acesso ao GitHub

Aplica-se quando `gh auth status` falha, o push é negado, o host é GitHub Enterprise ou não há `gh`.

## Como o gh encontra a credencial
- Ordem: `GH_TOKEN` (ou `GITHUB_TOKEN`) no ambiente → credencial gravada por `gh auth login` (no cofre do sistema).
- GitHub Enterprise: `--hostname <host>` em cada comando, ou `GH_HOST=<host>`; token em `GH_ENTERPRISE_TOKEN`.
- Repositório fora do diretório atual: `gh ... --repo owner/repo` (ou `GH_REPO`).
- Código de saída `4` = autenticação necessária.

## Autenticar (feito pelo humano, nunca pelo agente)
- Navegador: `gh auth login --hostname <host> --git-protocol https --web` — o humano roda no próprio terminal e conclui no navegador.
- Variável de ambiente: o humano define `GH_TOKEN` no ambiente em que o agente roda. O agente nunca recebe o valor pelo chat.
- Depois, para o `git push` por HTTPS usar a mesma credencial: `gh auth setup-git --hostname <host>`.
- SSH: se o `origin` é `git@<host>:...`, o push usa a chave do humano; o `gh` continua precisando de autenticação para PRs e Actions.

## Permissões necessárias
| Operação | Token clássico (escopos) | Token fine-grained (permissões do repositório) |
|---|---|---|
| ler repositório, PRs e Actions | `repo` (privado) ou nenhum (público) | Metadata: read, Contents: read, Pull requests: read, Actions: read, Commit statuses: read |
| push | `repo` | Contents: read and write |
| push que altera `.github/workflows/` | `repo` + `workflow` | Contents + Workflows: read and write |
- `gh run watch` **não funciona com token fine-grained** (não há permissão `checks:read`): acompanhe por consulta periódica (`actions.md`).
- Organização com SSO: o token precisa estar autorizado para a organização; erro 403 com menção a SSO → peça ao humano para autorizar.

## Erros comuns
| Sintoma | Causa provável | Ação |
|---|---|---|
| `gh: ... HTTP 401` ou saída 4 | sem credencial ou expirada | pedir autenticação ao humano |
| `HTTP 403` em Actions | token sem `Actions: read` | pedir a permissão ao humano |
| `HTTP 404` num repositório que existe | token sem acesso ao repositório ou à organização | pedir acesso |
| push: `Permission denied` / `403` | sem escrita, ou `workflow` ausente ao mexer em workflows | pedir a permissão |
| push: `rejected (non-fast-forward)` | a branch remota tem commits que você não tem | parar e reportar; nada de `--force` |
| push: `protected branch` | tentativa de enviar para branch protegida | erro do fluxo: só se envia `feature/<f>` |

## Sem gh: API REST
Só quando o `gh` não estiver disponível e o humano tiver definido `GH_TOKEN`:
```
curl -sS -H "Authorization: Bearer $GH_TOKEN" -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/repos/<owner>/<repo>/pulls?base=main&state=open"
```
- Enterprise: `https://<host>/api/v3/...`.
- Nunca use `-v` nem imprima os cabeçalhos: o token apareceria na saída.
