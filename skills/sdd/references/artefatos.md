# Artefatos do SDD — conteúdo esperado e checklist de qualidade

Cada artefato abaixo vive em `specs/<f>/` (exceto quando indicado). Use o checklist antes de declarar a etapa concluída.

## spec de entrada (`specs/_input/` ou o arquivo do humano)
- Modelo: `.agents/templates/spec-input.md`. Contém objetivo, atores, regras (RN), integração, não funcionais (RNF), critérios de aceite (CA), pontos em aberto e **Stack técnico**.
- Checklist: cada RN tem dono claro; cada CA é verificável; pontos em aberto têm default.

## spec.md (o quê / por quê)
- Seções: Clarifications (quando houver), Cenários de usuário e testes (histórias priorizadas P1, P2...), Casos de borda, Requisitos funcionais (FR), Entidades principais, Critérios de sucesso (SC), Premissas.
- Checklist:
  - [ ] nenhuma linguagem, framework, serviço ou API (nomes de recursos exigidos pela entrada são exceção registrada);
  - [ ] cada história é testável sozinha e tem cenários Dado/Quando/Então;
  - [ ] cada FR usa "DEVE"/"NÃO DEVE" e cita a origem (RN/RNF/Q#);
  - [ ] cada SC é mensurável (número, prazo, percentual) e verificável sem conhecer a implementação;
  - [ ] casos de borda incluem erro, vazio, duplicidade, volume e concorrência quando se aplicam;
  - [ ] premissas listam os defaults aplicados.

## clarifications.md
- Uma tabela por rodada: `# | Tema | Status | Default sugerido/Resposta | Aplicado em`.
- Respostas também gravadas na spec em `## Clarifications` › `### Session <data>` (`- Q: ... → A: ...`).

## techlead/perguntas.md
- Perguntas técnicas do tech lead ao humano, uma seção `## Rodada <n>` por rodada; por pergunta: contexto, requisito afetado, opções com consequência, recomendada e `Resposta do humano:`.
- Checklist: opções compatíveis entre si e com as decisões já tomadas; nenhuma pergunta de regra de negócio (essas são do PM, em `clarifications.md`).

## stack.md
- Bloco YAML por repositório: `stack`, `version`, `runtime`, `frameworks`, `techs`, `tools`, `commands`, `conventions`. Vocabulário de `spec-input.md`.

## plan.md (o como)
- Resumo; Technical Context (linguagem/versão, dependências, armazenamento, testes, plataforma, restrições, escala); Constitution Check (tabela regra → situação); repositórios, contratos e ondas; mapeamento requisito → repositório; estrutura do código; Complexity Tracking.
- Checklist:
  - [ ] Technical Context idêntico a `stack.md`/`workspace.yaml`;
  - [ ] cada regra da constitution avaliada; cada ⚠️ com exceção justificada;
  - [ ] cada FR/SC mapeado para um repositório;
  - [ ] `depends_on` coerente com produtor/consumidor dos contratos.

## research.md
- Uma entrada por decisão: **Decisão**, **Motivo**, **Alternativas** descartadas. Nenhuma `NEEDS CLARIFICATION` pode restar.

## data-model.md
- Tabela entidade → dono (único que escreve); atributos com tipo e regra; ciclo de vida/estados; padrões de acesso; dados pessoais e sua proteção.

## contracts/
- Um arquivo por contrato (OpenAPI 3.1, AsyncAPI 3 + JSON Schema, ou formato próprio para recursos de infraestrutura), com `owner`, `consumers`, `version` no topo.
- Checklist: nomes exatos; tipos; erros; versionamento; o que é compatível e o que é quebra.

## quickstart.md
- Pré-requisitos, ordem de implantação, cenários ponta a ponta (preparação → ação → esperado), cada um ligado a um CA.

## repos/<repo>/plan.md
- Só o que o repositório precisa: stack, contratos produzidos/consumidos, recursos/módulos, testes, comandos, fora do escopo, a linha `Desenho técnico: sim|não — <motivo>` (escrita pelo PM) e a seção `Desenho técnico` (escrita pelo tech lead).

## tasks.md e repos/<repo>/tasks.md
- Formato: `- [ ] T### [P?] [US#?] [repo:<nome>] descrição com caminho exato`.
- Checklist:
  - [ ] toda tarefa cita arquivo e, quando aplicável, o FR/CA;
  - [ ] testes exigidos pela constitution estão presentes por história;
  - [ ] em repositório vazio, a estrutura inicial vem primeiro;
  - [ ] dependências e oportunidades de paralelismo declaradas;
  - [ ] nenhuma tarefa sem requisito e nenhum requisito sem tarefa.

## reports/
- `analyze.md` (achados por severidade, cobertura, métricas), `converge.md`, `techlead.md`, `<repo>/{dev,review}.md`, `integration/qa.md` — sempre no template do papel, sem seções extras.

## status.md
- Única fonte para retomar: etapa, situação, próxima ação, contratos congelados, pendências, tabela por repositório, QA e lacunas do converge.
