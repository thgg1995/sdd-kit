# Spec Kit — problemas conhecidos e soluções

| Sintoma | Causa | Solução |
|---|---|---|
| `specify: command not found` logo após instalar | `~/.local/bin` fora do PATH | ajustar o PATH na sessão (`export PATH="$HOME/.local/bin:$PATH"`) ou `uv tool update-shell` |
| Sem `uv` e sem `pipx` | máquina sem os instaladores | `python -m pip install --user -q uv` e usar `python -m uv tool install ...` |
| `init` falha com "Agent Detection Error … not found" | o CLI do agente não está no PATH (ex.: Claude Code dentro da IDE) | repetir o `init` com `--ignore-agent-tools` |
| `init` pede confirmação e trava | diretório não vazio em sessão não interativa | `--here --force --non-interactive` |
| Comando `/speckit-<cmd>` "desconhecido" logo após o `init` | o agente só registra comandos/skills novos ao iniciar a sessão | executar os passos do arquivo do comando (`.claude/skills/speckit-<cmd>/SKILL.md`) ou reiniciar a sessão |
| Comando roda na feature errada | `.specify/feature.json` aponta outra feature | ajustar `feature_directory` para a feature em curso |
| Scripts não rodam em Linux/macOS | workspace inicializado com `--script ps` | `specify integration upgrade <agente> --script py` |
| Outro agente abre o workspace e não acha os comandos | só a integração original foi instalada | `specify integration install <agente> --script py`; se não for *multi-install safe*, confirmar com o humano antes de `--force` |
| Templates diferentes entre workspaces | versões diferentes do CLI no `init` | fixar a versão do time na instalação; `specify integration upgrade` nos antigos, se desejado |
| `specify version`/`check` com saída enorme | banner e cores no terminal | filtrar: remover códigos ANSI (`sed 's/\x1b\[[0-9;]*m//g'`) e buscar só as linhas necessárias |
| Converge não encontra o código | código fora da raiz do workspace (multi-repositório) | resolver os caminhos dentro do repositório da marcação `[repo:<nome>]` |
