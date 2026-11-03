# Antipadrões do SDD e como corrigir

| Antipadrão | Sintoma | Correção |
|---|---|---|
| Tecnologia na spec | `spec.md` cita linguagem, framework, banco, API | mover para `stack.md`/`plan.md`; na spec, descrever o comportamento |
| Regra de negócio presumida | FR sem origem (RN, RNF ou Q#) ou com "provavelmente" | `[NEEDS CLARIFICATION]` + pergunta com default; nunca decidir pelo humano |
| Critério vago | "rápido", "seguro", "escalável", "intuitivo" | número, prazo, percentual ou condição verificável |
| Critério sem teste | CA sem teste nomeado com o ID | criar o teste ou registrar `NÃO COBERTO` com motivo |
| Plano que troca a stack | Technical Context diferente de `stack.md` | voltar ao gate de clarificação; o plano não escolhe stack |
| Contrato depois do código | `contracts/` criado ou alterado durante a implementação | contratos antes das tarefas; após congelar, só com aprovação do humano |
| Contrato implícito | dois repositórios combinam algo fora de `contracts/` | todo ponto de contato entre repositórios vira contrato versionado |
| Tarefa órfã | tarefa sem FR/CA, ou FR sem tarefa | analyze aponta; ajustar `tasks.md` antes de implementar |
| Tarefa sem caminho | "implementar o serviço" | caminho exato do arquivo e o que muda nele |
| Código corrigido em silêncio | comportamento muda sem a spec mudar | corrigir primeiro o artefato de origem; depois tarefas e código |
| Exceção não registrada | desvio da constitution só no código | registrar no Complexity Tracking do plano, com motivo e alternativa |
| Escopo que cresce na implementação | refatoração, "melhoria", arquivo fora das tarefas | desfazer; registrar em `Fora do escopo` do relatório |
| Convergência pulada | entrega declarada pronta sem comparar com spec/plano/tarefas | rodar o converge; o que faltar vira tarefa |
| Spec gigante e única | uma spec para várias features independentes | uma feature por spec; histórias independentes e priorizadas |
| Clarificação infinita | rodadas de perguntas de baixo impacto | uma rodada só: decisões abertas por impacto, o resto como confirmação de default; pergunta dependente vai como condicional, não em nova rodada |
