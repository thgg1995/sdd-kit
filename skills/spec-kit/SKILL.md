---
name: spec-kit
description: GitHub Spec Kit (CLI `specify` e comandos /speckit.*) — versão validada, verificação, instalação, atualização, inicialização, integrações por agente, comandos, arquivos e problemas conhecidos, e como este kit usa cada comando. Use na preparação do workspace, ao executar qualquer comando do Spec Kit e diante de qualquer erro dele.
---

# Spec Kit

Ferramenta do GitHub que implementa o SDD: um CLI (`specify`, pacote `specify-cli`) que cria a estrutura `.specify/` e instala, para o agente de IA em uso, os comandos `/speckit.*` que geram e verificam os artefatos.

## Versão
- **Validada neste kit: `1.2.4.dev0`** (2026-10-28). Última estável conhecida: `v1.2.5` (2026-10-30).
- Fixe a versão do time no comando de instalação (`...spec-kit.git@vX.Y.Z`): os templates do `init` vêm da versão instalada, e workspaces criados com versões diferentes geram artefatos diferentes.
- Ao adotar uma versão nova: rode uma feature de teste, atualize a linha "Validada" acima e os pontos de `references/comandos.md` que mudarem.

## Verificar, instalar, atualizar (resumo)
```
specify version                      # versão do CLI, Python e sistema
specify self check                   # há versão mais nova? (somente leitura)
specify check                        # ferramentas e CLIs de agentes disponíveis
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z
pipx install git+https://github.com/github/spec-kit.git@vX.Y.Z     # alternativa
specify self upgrade --tag vX.Y.Z    # atualizar o CLI para uma versão fixa
specify integration upgrade <agente> # atualizar os comandos instalados num projeto
```
Sem `uv` nem `pipx`, sem `specify` no PATH (Windows: `~/.local/bin`) e outras situações: `references/instalacao.md`.

## Inicializar um workspace (regras deste kit)
```
specify init --here --force --non-interactive --integration <agente> --script py
```
- `--here --force`: no diretório atual, mesmo não vazio. Sem git: o workspace não é repositório (a extensão git é opcional e não é usada).
- `--script py`: scripts em Python, que rodam em qualquer sistema operacional.
- `--integration <agente>`: chave de `specify integration list` (ex.: `claude`, `copilot`, `codex`, `gemini`, `cursor-agent`); sem chave própria → `generic` com `--integration-options="--commands-dir <pasta>"`.
- CLI do agente fora do PATH (ex.: Claude Code rodando dentro de uma IDE) → acrescente `--ignore-agent-tools`.
- Outro agente no mesmo workspace → `specify integration install <agente> --script py` (vários podem conviver; `use` define o padrão).

## Comandos e como este kit os usa
| Comando | Faz | Uso neste kit |
|---|---|---|
| `constitution` | cria/atualiza `.specify/memory/constitution.md` | só se a constitution estiver vazia (a do kit substitui o template) |
| `specify` | cria `specs/NNN-<nome>/spec.md`, o checklist de qualidade e `.specify/feature.json` | etapa 2; antes, extrair `stack.md` da spec de entrada |
| `clarify` | varredura de cobertura e até 5 perguntas, gravadas em `## Clarifications` | etapa 3 em **modo lote**, somado às perguntas do gate (stack à parte) |
| `plan` | `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, Constitution Check | etapa 5; Technical Context só de `stack.md`/`workspace.yaml` |
| `tasks` | `tasks.md` em fases por história, formato checklist | etapa 7; marcar `[repo:<nome>]` e dividir por repositório |
| `analyze` | relatório só de leitura de consistência e cobertura | etapa 8; gravar em `reports/analyze.md`; corrigir críticos uma vez |
| `converge` | compara o código com os artefatos e **acrescenta** tarefas `Phase N: Convergence` | etapa 13; resolver caminhos dentro de cada repositório |
| `implement` | executa o `tasks.md` com um único agente | **não usado**: o fluxo de subagentes implementa |
| `checklist` | checklists de qualidade dos requisitos por tema | opcional |
| `taskstoissues` | tarefas → issues | descontinuado; não usar |

Detalhes de entradas, scripts, saídas e gates de cada comando: `references/comandos.md`.

## Regras de ouro
1. Chame o comando na forma que o agente expõe: o separador está em `invoke_separator` de `.specify/integration.json` (`/speckit-plan` no Claude Code, `/speckit.plan` em outros).
2. Comandos recém-instalados podem só aparecer numa nova sessão do agente. Até lá, execute os passos do arquivo do comando (ex.: `.claude/skills/speckit-<cmd>/SKILL.md`), sem mudar o fluxo.
3. Verifique hooks em `.specify/extensions.yml` antes e depois de cada comando (`hooks.before_<cmd>` / `after_<cmd>`); hook obrigatório é executado, opcional é só informado.
4. Os scripts imprimem JSON com caminhos absolutos (`--json`); use esses valores em vez de supor diretórios.
5. Não edite os templates de `.specify/templates/` para mudar o processo: o processo está no `orquestrador.md` e nos papéis; personalização de template vai em preset (`specify preset`).

## Referências
- `references/instalacao.md` — ler quando o `specify` não existir, estiver desatualizado, fora do PATH, ou a instalação falhar.
- `references/comandos.md` — ler antes de executar um comando pela primeira vez na sessão ou quando a saída dele não for a esperada.
- `references/estrutura.md` — ler quando precisar localizar ou interpretar um arquivo de `.specify/`, da integração do agente ou de hooks.
- `references/problemas.md` — ler diante de erro do Spec Kit ou comportamento inesperado.
