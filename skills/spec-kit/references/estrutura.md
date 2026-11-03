# Spec Kit — estrutura de arquivos e subcomandos do CLI

## No workspace
```
.specify/
  init-options.json          # ai, integration, script (py|sh|ps), feature_numbering (sequential|timestamp), speckit_version
  integration.json           # installed_integrations, default_integration, integration_settings.<agente>.{script, invoke_separator}
  integrations/*.manifest.json  # arquivos que cada integração instalou (usado em upgrade/uninstall)
  feature.json               # feature_directory da feature ativa (gravado pelo specify)
  extensions.yml             # (opcional) hooks before_/after_<comando>: extension, command, optional, enabled, condition
  memory/constitution.md     # constitution do projeto
  scripts/python/            # check_prerequisites.py, create_new_feature.py, setup_plan.py, setup_tasks.py, resolve_template.py, common.py
  scripts/powershell/        # equivalentes .ps1 (quando instalados)
  templates/                 # spec-, plan-, tasks-, checklist-, constitution-template.md
  workflows/                 # registro de workflows de automação
<pasta do agente>/           # comandos /speckit.* da integração (ex.: .claude/skills/speckit-<cmd>/SKILL.md)
specs/<NNN>-<nome>/          # artefatos de cada feature (spec, plan, tasks, checklists, contracts...)
```
- Nunca edite `integration.json` ou os manifestos à mão: use `specify integration ...`.
- `feature.json` diz aos comandos qual feature está ativa; ao trabalhar em outra feature, ele é regravado pelo `specify` (ou ajuste-o para a feature em curso).

## Hooks (`.specify/extensions.yml`)
- Chaves `hooks.before_<cmd>` e `hooks.after_<cmd>`; cada hook tem `extension`, `command`, `optional`, `enabled` (padrão: ativo) e `condition`.
- `optional: false` → executar o comando do hook (`speckit.git.commit` vira `/speckit-git-commit`); `optional: true` → só informar; `condition` não vazia → não avaliar, deixar para o executor de hooks.
- Arquivo inválido → avisar que os hooks não foram verificados e seguir.

## Subcomandos do CLI (1.2.4.dev0)
| Subcomando | Uso |
|---|---|
| `init` | inicializa o projeto (`--here`, `--force`, `--non-interactive`, `--integration`, `--script`, `--ignore-agent-tools`, `--preset`, `--extension`) |
| `check` | lista ferramentas e CLIs de agentes disponíveis |
| `version` | versão do CLI, Python e sistema |
| `self check` / `self upgrade [--tag] [--dry-run]` | verificar/atualizar o próprio CLI |
| `integration list/status/install/uninstall/switch/use/upgrade/info/search/scaffold/catalog` | integrações de agentes no projeto |
| `extension` | extensões (ex.: git) |
| `preset` | presets de templates (personalização sem editar `.specify/templates/`) |
| `workflow`, `event`, `bundle`, `artifact`, `mcp` | automação, eventos, pacotes, introspecção e servidor MCP experimental — não usados neste kit |
