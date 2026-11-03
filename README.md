# sdd-kit

Kit versionado do processo Spec-Driven. Mantenha-o num repositório próprio (ex.: `minha-org/sdd-kit`).

```
AGENTS.md             # configuração e roteamento; é o único arquivo que vai para a raiz de cada workspace
orquestrador.md       # roteiro do orquestrador (pipeline); a preparação o copia para .agents/
preparacao.md         # preparação do workspace, lida do kit quando o workspace é preparado
roles/                # pm, techlead, dev, reviewer, qa e donos.md (mapa de donos, lido por pm e techlead)
bin/                  # fluxo.py (registro do fluxo), janela.py (acompanhamento em janela, abre sempre sozinha) e painel.py (o mesmo no terminal, só se a janela não abrir)
python_lib/           # biblioteca Python compartilhada (repositório git próprio; consumida do kit, não copiada)
skills/
  catalog.yaml        # quando cada skill é instalada e o gatilho no índice
  <skill>/SKILL.md    # suas skills (padrão Agent Skills)
  <skill>/references/ # detalhes da skill, lidos sob demanda
templates/
  workspace.yaml
  repo-notes.md
  spec-input.md       # modelo da spec de entrada (inclui a seção "Stack técnico")
  env.md              # modelo do ambiente preparado para os subagentes (etapa `ambiente`)
  constitution.md     # opcional: constitution padrão do time
```

## Biblioteca compartilhada
A `python_lib/` vive no kit, com o próprio `.git`. A preparação a registra no `workspace.yaml` (`kind: lib`, `source: kit`, `path: ../sdd-kit/python_lib`) e os repositórios Python a consomem de lá. O tech lead decide, pelo `CATALOGO.md` dela, se cada necessidade técnica dos consumidores reusa, altera ou cria um método na lib (skill `python-lib`); as alterações são commitadas na própria lib, no kit.

## Como usar
1. Coloque suas skills em `skills/<nome>/SKILL.md` e registre cada uma no `catalog.yaml`.
2. Crie uma pasta de workspace e clone dentro dela os repositórios necessários.
3. Copie o `AGENTS.md` deste kit para a raiz do workspace e ajuste `KIT_SOURCE` e `IDIOMA`. Se a sua ferramenta de IA não ler `AGENTS.md` sozinha, crie o arquivo de instruções dela com uma linha apontando para ele (ex.: `CLAUDE.md` com `@AGENTS.md`; `GEMINI.md`, ou `contextFileName: AGENTS.md` nas configurações do Gemini CLI).
4. Escreva a spec seguindo `templates/spec-input.md`. A seção **Stack técnico** é obrigatória para repositórios vazios ou com stack não detectada (stack, versão, runtime, techs). Para os demais, ela é opcional e confirma o que foi detectado.
5. Abra qualquer agente de IA na raiz do workspace (o processo não depende de fornecedor: sem subagentes, os papéis rodam em sequência; o Spec Kit é instalado para o agente em uso) e peça: "implemente a spec em <arquivo>". Na primeira vez, o `AGENTS.md` obtém o kit e a preparação do workspace (`preparacao.md`) roda sozinha.

## Como escrever uma skill
O padrão completo (estrutura, regras verificáveis, catálogo e checklist) está na skill `skills/skill-authoring/`, que o tech lead segue ao propor skills. Resumo:
Toda skill usa divulgação progressiva: o essencial sempre é lido; o detalhe, só quando a tarefa pede.
```
skills/<skill>/
  SKILL.md              # sempre lido pelo subagente
  references/
    <assunto>.md        # lido só quando o gatilho do índice corresponder à tarefa
```
- **`SKILL.md`, no máximo 150 linhas** (a preparação do workspace avisa quando passar):
  - frontmatter `name` + `description`;
  - as regras que valem para qualquer tarefa da skill (o que é obrigatório e o que é proibido, com a seção da constitution que cada uma detalha);
  - um índice de referências, uma linha por arquivo, com o gatilho de leitura:
    `- references/iam.md — ler quando a tarefa cria ou altera role/policy`.
- **`references/`**: exemplos, padrões completos, tabelas e casos especiais. Pode crescer à vontade; cada arquivo trata de um assunto e deve ser entendível sozinho.
- Regra estrutural (layout do projeto, convenções que afetam a primeira tarefa) fica no `SKILL.md`, nunca só em `references/`, para não haver retrabalho.
- Registre a skill no `catalog.yaml` (`stacks`/`techs`/`always`, `trigger`, `loaded_by`, `rules`).
