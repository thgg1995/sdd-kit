# Forma silenciosa dos comandos

**Precedência:** o comando é o que o repositório ou o ambiente declaram (notas do repositório, `Teste específico`, seção `integration` do `workspace.yaml`). Desta tabela, acrescente só as opções que reduzem a saída sem mudar o que o comando faz. Quando nada foi declarado, use a forma da tabela.

A forma silenciosa mostra o resultado, os avisos e os erros, sem progresso nem banner. A coluna "Em falha" diz como ver o detalhe sem trazer o log inteiro para o contexto. Verificado em 2026-11-10 rodando cada comando, salvo onde a linha diz outra coisa. Versões: pytest 9.2.0, ruff 0.17.3, pip 26.2.2, .NET SDK 9.0.203, Terraform 1.17.1, Docker Compose 5.1.3, npm 11.13.0, git 2.49, ripgrep 14.1.

## Saída longa num arquivo
| Shell | Forma |
|---|---|
| bash | `<comando> > "${TMPDIR:-/tmp}/saida.log" 2>&1; echo "exit=$?"; tail -n 30 "${TMPDIR:-/tmp}/saida.log"` |
| PowerShell | `cmd /c "<comando> > %TEMP%\saida.log 2>&1"; "exit=$LASTEXITCODE"; Get-Content "$env:TEMP\saida.log" -Tail 30` |

- Para achar o erro no meio do log: `grep -n -i -m 20 "error\|erro\|fail" <log>` (no PowerShell, `Select-String -Path <log> -Pattern "error|erro|fail" | Select-Object -First 20`).
- No Windows PowerShell 5.1, `*>` e `2>&1` num executável transformam cada linha de stderr num registro de erro de várias linhas; o `cmd /c` grava o stderr limpo e preserva o código de saída.

## Por stack
| Stack | Tarefa | Forma silenciosa | Em falha |
|---|---|---|---|
| Python | testes | `pytest -q --tb=short --no-header` | rode só o teste que falhou (`pytest -q <arquivo>::<teste>`), com `--tb=long` se o trecho curto não bastar |
| Python | lint e formatação | `ruff check --quiet <arquivos>`; `ruff format --quiet <arquivos>` (`--check` só confere) | a saída já é só o problema |
| Python | instalação | `pip install -q --disable-pip-version-check -r requirements.txt` | log em arquivo (acima). Conferido no `--help` |
| Python | uv | `uv sync --quiet`; `uv run --quiet pytest -q` | > Não verificado: o uv não estava instalado — conferir com `uv sync --help` |
| .NET | build | `dotnet build --nologo -v q` | já mostra cada aviso e cada erro em uma linha. Não use `-clp:ErrorsOnly`: ele deixa só a contagem de avisos e esconde quais são |
| .NET | testes | `dotnet test --nologo -v q` | a forma silenciosa mostra só o nome do teste que falhou; para a mensagem, rode só ele com `--filter "FullyQualifiedName~<Teste>" --logger "console;verbosity=detailed"`, saída em arquivo, e busque `[FAIL]` |
| Terraform | init | `terraform init -input=false -no-color`, saída em arquivo | `tail` do arquivo |
| Terraform | validate e fmt | `terraform validate -no-color`; `terraform fmt -check -recursive` | o `validate` não aceita `-compact-warnings` |
| Terraform | test | `terraform test -no-color` | rode só o arquivo que falhou (`-filter=tests/<arquivo>.tftest.hcl`, conferido no `-help`) |
| Terraform | plan | `terraform plan -input=false -no-color -compact-warnings`, saída em arquivo | busque `Error:`; para o detalhe dos avisos, rode sem `-compact-warnings`. Conferido no `-help` |
| Terraform | apply no ambiente de teste | `terraform apply -auto-approve -input=false -no-color -compact-warnings`, saída em arquivo | idem. Na pipeline, o apply é do plano salvo (skill `terraform`). Conferido no `-help` |
| Docker | ambiente | o `integration.up` do `workspace.yaml`; num `docker compose up -d`, acrescente `--quiet-pull` | `docker compose logs --tail 50 <serviço>`. Conferido no `--help` |
| Node | instalação | `npm ci --no-audit --no-fund --loglevel=error` | o `--silent` esconderia também os erros. Conferido no `--help` |
| git | estado e histórico | `git status --short`; `git diff --stat`; `git log --oneline -n 20` | `git diff -- <arquivo>` |
| busca | arquivos e termos | `rg --files -g "<padrão>" <pasta>`; `rg -n -C 3 "<termo>" <pasta>` | sem `rg`, a ferramenta de busca do agente com os mesmos limites |
