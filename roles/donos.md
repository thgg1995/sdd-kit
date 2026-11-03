# Mapa de donos dos artefatos

Lido pelo PM e pelo tech lead; o orquestrador o consulta para rotear ao dono uma falha do `conferir-donos` ou um achado `DONO` (seção 4.3 do `orquestrador.md`).

Cada artefato ou seção tem um único dono: o PM não escreve no que é do tech lead, e vice-versa. `python .agents/bin/fluxo.py conferir-donos <f>` verifica o que dá para checar por arquivo (marcadores sem resolver, linha `Desenho técnico` decidida, seções e relatório do tech lead, a seção `Verificações` do `research.md` (só em feature com `Processo` ≥ 2), contratos com `owner`, `consumers` e `version`, `depends_on`); o analyze confere o resto.

| Artefato / seção | Dono |
|---|---|
| `spec.md`, `clarifications.md`, `stack.md` (cópia da entrada e respostas do humano), `tasks.md` e `repos/*/tasks.md`, `quickstart.md` (cenários por requisito) | PM |
| `plan.md`: resumo, Technical Context (cópia de `stack.md`/`workspace.yaml`), Constitution Check de produto, mapeamento requisito → repositório, premissas | PM |
| `plan.md`: contratos, posse dos dados, versionamento, integração, `depends_on` e ondas, Complexity Tracking técnico | tech lead |
| `repos/<repo>/plan.md`: "O que este repositório entrega", "Fora do escopo" | PM |
| `repos/<repo>/plan.md`: linha `Desenho técnico: sim\|não`, seção `Desenho técnico`, `Contratos`, "Correções após o QA" | tech lead |
| `research.md`: decisões de produto (D-xx) | PM |
| `research.md`: decisões técnicas (T-xx) e `Limites verificados` | tech lead |
| `data-model.md`: entidades, atributos e regras de negócio | PM |
| `data-model.md`: dono de cada entidade, tipos físicos, chaves, índices (seções "(tech lead)") | tech lead |
| `contracts/*` | tech lead |
| `workspace.yaml`: `depends_on` | tech lead |
| `workspace.yaml`: stack, versão, runtime, techs e tools | orquestrador (a partir de `stack.md`) |

Pendência do tech lead num artefato do PM: marcador `[TECH LEAD: <o que decidir>]`, que o tech lead substitui pela decisão. Marcador sem substituir bloqueia o congelamento dos contratos.
