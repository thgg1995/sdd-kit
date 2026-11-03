# Spec Kit — instalação, verificação e atualização

## Verificar
| Pergunta | Comando | Resposta esperada |
|---|---|---|
| Está instalado? | `specify version` (ou `command -v specify`) | quadro com `CLI Version`, `Python`, `Platform` |
| Há versão nova? | `specify self check` | versão disponível e comandos de atualização (somente leitura) |
| O ambiente tem o necessário? | `specify check` | lista de ferramentas e de CLIs de agentes (`not found` para os ausentes) |
| Qual integração o workspace usa? | `specify integration status` (ou ler `.specify/integration.json`) | integrações instaladas e a padrão |

## Instalar (no espaço do usuário, sem administrador)
1. Com `uv` (preferido):
   `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z`
2. Com `pipx`:
   `pipx install git+https://github.com/github/spec-kit.git@vX.Y.Z`
3. Sem `uv` nem `pipx`: instale o `uv` via pip do Python do sistema e use-o como módulo:
   `python -m pip install --user -q uv` e depois `python -m uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z`
- Sem `@vX.Y.Z`, instala a ponta da branch padrão: evite; fixe a versão do time.
- O executável vai para `~/.local/bin` (Windows: `C:\Users\<usuário>\.local\bin`). Se não estiver no PATH: `export PATH="$HOME/.local/bin:$PATH"` (bash), `$env:PATH = "$HOME\.local\bin;$env:PATH"` (PowerShell), ou `uv tool update-shell` para torná-lo permanente.

## Atualizar
- CLI: `specify self upgrade --tag vX.Y.Z` (`--dry-run` mostra o plano antes). Alternativa: reinstalar com `uv tool install specify-cli --force --from git+...@vX.Y.Z` ou `pipx install --force ...@vX.Y.Z`.
- Projeto já inicializado: o `init` usa os templates da versão instalada no momento; workspaces antigos não mudam sozinhos. Para atualizar os comandos de um agente num workspace: `specify integration upgrade <agente>` (substitui com cuidado os arquivos modificados).
- Depois de atualizar: rode uma feature de teste e atualize a versão "Validada" no `SKILL.md`.

## Desinstalar
- `uv tool uninstall specify-cli` ou `pipx uninstall specify-cli`. A estrutura `.specify/` dos workspaces não é removida.
