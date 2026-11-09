# Preparação do workspace

Lida pelo orquestrador quando a seção 0 do `orquestrador.md` manda preparar o workspace.
O kit contém arquivos para copiar — `orquestrador.md`, `skills/` (com `catalog.yaml`), `roles/`, `templates/` e `bin/` (registro e painel do fluxo, em Python sem dependências) — e as **bibliotecas compartilhadas** (ex.: `python_lib/`, cada uma com o próprio `.git`), que não são copiadas: os repositórios as consomem do kit. A versão canônica do `AGENTS.md` do workspace também fica no kit.
É **idempotente**: execute cada passo só se o resultado ainda não existir, e nunca sobrescreva o que o humano editou (arquivo diferente do kit → mantenha o do workspace e registre a divergência). Não rode builds nem testes: apenas leia arquivos marcadores. Não escreva nada dentro dos repositórios de aplicação. `KIT` = `.agents/kit/`.

1. **Kit**: obtenha o kit em `KIT` (cópia do `KIT_LOCAL` sem `.git` e sem as bibliotecas compartilhadas; se inválido, clone raso de `KIT_SOURCE` em `KIT_REF`; se já existir, atualize). Na primeira vez, o `AGENTS.md` já o obteve.
2. **Repositórios**: pastas com `.git` até 2 níveis abaixo da raiz. Ignore `.agents/`, `.specify/`, `specs/`, `integration/`, `node_modules/`, `bin/`, `obj/`, `.venv/`.
   **Bibliotecas do kit**: pastas de primeiro nível do `KIT_LOCAL` com `.git` e `py.typed` no pacote (`src/<pacote>/py.typed` ou `<pacote>/py.typed`) → uma entrada com `kind: lib`, `source: kit` e `path` relativo à raiz do workspace (ex.: `../sdd-kit/python_lib`). Sem `KIT_LOCAL` válido, não há lib: registre para o resumo.
3. **Stack por marcadores** (sem ler código):

| Marcador | Stack |
|---|---|
| `*.sln`, `*.csproj` | `dotnet` |
| `pyproject.toml`, `requirements*.txt`, `setup.py` | `python` |
| `package.json` | `node` (ou `react`/`angular`/`vue` conforme dependências) |
| `go.mod` | `go` |
| `pom.xml`, `build.gradle*` | `java` |
| somente `*.tf` (nenhum outro marcador de stack) | `terraform` |

| Marcador nas dependências/arquivos | Tech |
|---|---|
| `Confluent.Kafka`, `confluent-kafka`, `kafka-python`, `aiokafka`, `kafkajs` | `kafka` |
| `*.tf`, `cdk.json`, `serverless.yml`, `template.yaml` (SAM), `AWSSDK.*`, `boto3` | `aws` |
| `*.tf` (em qualquer pasta, ex.: `infra/`) | `terraform` |
| `Microsoft.AspNetCore.*` / SDK `Microsoft.NET.Sdk.Web`, `fastapi`, `flask`, `django`, `express`, `*.openapi.*`/`openapi.*` | `api` |
| `Microsoft.EntityFrameworkCore*`, `Dapper`, `Npgsql`, `Microsoft.Data.SqlClient`, `sqlalchemy`, `psycopg*`, `asyncpg`, `alembic`, pasta `Migrations/` | `sql` |
| `MongoDB.Driver`, `pymongo`, `motor`, `AWSSDK.DynamoDBv2`, `dynamodb` com `boto3`/`aioboto3`, `StackExchange.Redis`, `redis` | `nosql` |
| `Dockerfile`, `docker-compose*.yml` | `docker` |

   - Mais de uma stack → use a predominante e registre as demais em `techs`.
   - Registre também o que o marcador informar: `version` (`TargetFramework`, `requires-python`, `engines.node`, `required_version`...), `runtime` (`serverless.yml`/SAM → `aws-lambda`, `Dockerfile` → `container`), `frameworks` e `tools`. Não identificado → `?`.
   - Sem marcador (repositório vazio) → `stack: ?` e `stack_source: ?`. **Não bloqueia**: a stack passa a ser exigida na seção "Stack técnico" da spec e é aplicada na etapa `stack` (seção 4 do `orquestrador.md`).
   - **Biblioteca compartilhada**: as do kit (passo 2) têm `kind: lib`; os repositórios do workspace, `kind: app`. Havendo lib, acrescente `python-lib` aos `techs` da lib e de cada repositório `python` (consumidores).
4. **`workspace.yaml`**: a partir de `KIT/templates/workspace.yaml`, com `prepared_at` (data) e `kit_ref` (`KIT_REF` e commit, ou `local`) no topo e uma entrada por repositório (`base_branch` = branch padrão do `origin`; sem remoto, a branch atual; `depends_on: []`). Se já existir, só acrescente repositórios novos.
5. **Notas `.agents/repos/<repo>.md`**: a partir de `KIT/templates/repo-notes.md`, no máximo 15 linhas. Repositório com `AGENTS.md` próprio ou documento de arquitetura (`docs/arquitetura.md`, `ARCHITECTURE.md`) → a nota aponta para eles e acrescenta o que faltar. Senão, extraia build/teste/lint de `package.json`, `Makefile`, `pyproject.toml`, `*.sln`/`*.csproj` e CI (`.github/workflows`, `azure-pipelines.yml`, `.gitlab-ci.yml`). Não encontrado → `?`.
6. **Skills**: siga o procedimento **Skills** da seção 0 do `orquestrador.md` (o mesmo da etapa `stack`): ele instala as skills e grava o `.agents/indice-skills.md`.
7. **Roteiro, roles, modelos e scripts**: copie `KIT/orquestrador.md` para `.agents/orquestrador.md`, `KIT/roles/*.md` para `.agents/roles/`, `KIT/templates/{spec-input,env}.md` para `.agents/templates/` e `KIT/bin/*.py` para `.agents/bin/`.
8. **Spec Kit** (carregue a skill `spec-kit`): instale o CLI `specify` se faltar (`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git` ou `pipx install git+https://github.com/github/spec-kit.git`). Use sempre scripts `py` (`--script py`), que rodam em qualquer sistema operacional. Integração = a chave do agente em uso em `specify integration list`; agente sem chave própria → `generic`.
   - `.specify/` não existe → consulte `specify init --help` e inicialize no diretório atual com essa integração, sem criar repositório git, forçando se o diretório não estiver vazio.
   - `.specify/` existe sem a integração do agente em uso → `specify integration install <chave> --script py` (se a integração não for *multi-install safe*, confirme com o humano antes de usar `--force`).
   - Se `.specify/memory/constitution.md` for o template padrão e `KIT/templates/constitution.md` existir, substitua-o pelo do kit.
9. **Pastas**: crie `specs/` e `integration/` se não existirem.
10. **Finalizar**: atualize `prepared_at` e `kit_ref` no `workspace.yaml`.
    - Devolva ao humano um resumo de até 15 linhas: repositórios e stacks, skills instaladas e ausentes, divergências, e repositórios com `stack: ?` (a spec deve preencher "Stack técnico"; modelo em `.agents/templates/spec-input.md`).
    - Termine o resumo avisando que a janela de acompanhamento abre **sempre**, por padrão, quando a feature é iniciada (`fluxo.py iniciar`), sem comando do humano. Só se ela não conseguir abrir o `fluxo.py` avisa e traz o comando de acompanhamento para rodar em outro terminal (`python .agents/bin/painel.py --watch`). Desligar a janela: variável `SDD_SEM_JANELA=1`; fechada pelo humano, não reabre.
