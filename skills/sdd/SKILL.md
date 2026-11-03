---
name: sdd
description: Spec-Driven Development (SDD) — princípios, cadeia de artefatos, gates, rastreabilidade e armadilhas. Use em qualquer etapa de especificação, clarificação, plano, tarefas, análise ou convergência, e sempre que houver dúvida sobre o processo.
---

# Spec-Driven Development (SDD)

A **especificação é a fonte da verdade**. Código, testes e infraestrutura são derivados dela, e toda divergência se resolve corrigindo primeiro o artefato de origem, nunca só o código.

## Princípios (valem para qualquer tarefa)
1. **O quê antes do como.** A spec descreve comportamento, regras e resultados mensuráveis, sem tecnologia. Tecnologia entra no plano (aqui, também em `stack.md`).
2. **Nada é inventado.** Lacuna de regra de negócio vira `[NEEDS CLARIFICATION]` e pergunta ao humano, com default sugerido. Nenhum agente decide regra de negócio, linguagem, versão ou runtime.
3. **Cada artefato deriva do anterior** e só avança depois do seu gate. Mudar um artefato anterior invalida os seguintes, que precisam ser revistos.
4. **Rastreabilidade ponta a ponta**: todo requisito tem tarefa; toda tarefa tem requisito; todo critério de aceite tem teste.
5. **Contrato antes de código.** O que é compartilhado entre componentes é definido, versionado e congelado antes da implementação.
6. **A constitution prevalece** sobre preferências, skills e convenções; desvio só como exceção registrada no plano, com motivo e alternativa descartada.
7. **Testável ou não existe.** Requisito sem critério verificável não é requisito; critério sem teste não está atendido.
8. **Convergir ao final.** A entrega só termina quando o código corresponde à spec, ao plano e às tarefas; o que faltar vira tarefa nova.

## Cadeia de artefatos e gates
```
spec de entrada
  → spec.md ............ o quê/por quê (histórias, FR, SC, casos de borda)   gate: clarificação
  → stack.md ........... stack por repositório (fora da spec, que é agnóstica)
  → plan.md + research + data-model + contracts/ + quickstart ... o como     gate: Constitution Check
  → repos/<repo>/plan.md (+ Desenho técnico) ...... o como por repositório
  → tasks.md + repos/<repo>/tasks.md .............. passos executáveis      gate: analyze (0 críticos)
  → contratos congelados
  → código + testes (dev) → review → QA de integração → converge             gate: converge
```

## Rastreabilidade (IDs)
| ID | Nasce em | Vira | Verificado por |
|---|---|---|---|
| `RN`, `RNF`, `CA` | spec de entrada | `FR-###`, `SC-###`, cenários de aceite | analyze (cobertura) |
| `FR-###` | spec.md | tarefas `T###` que o citam | analyze, converge |
| `SC-###`, `CA##` | spec.md | testes nomeados com o ID (ex.: `test_E3_CA03_...`) | review, QA |
| `T###` | tasks.md | commits `[<f>] T### ...` | review (cobertura das tarefas) |
| `Q#` | clarifications.md | `## Clarifications` › `### Session` na spec | gate de clarificação |

## Regras dos artefatos (resumo)
- **spec.md**: histórias priorizadas e testáveis de forma independente; FRs com "DEVE"; SCs mensuráveis e sem tecnologia; casos de borda; premissas explícitas; no máximo 3 `[NEEDS CLARIFICATION]` por rodada no specify.
- **plan.md**: Technical Context só a partir de `stack.md`/`workspace.yaml`; Constitution Check com cada regra; decisões em `research.md` (decisão, motivo, alternativas); exceções em Complexity Tracking.
- **contracts/**: um arquivo por contrato, com `owner`, `consumers` e `version`; quebra exige nova versão convivendo com a anterior.
- **tasks.md**: `- [ ] T### [P?] [US#?] [repo:<nome>] descrição com caminho`; fases Setup → Fundação → uma por história (prioridade) → Acabamento; dependências e paralelismo explícitos.

## Gates — o que bloqueia
- **Clarificação**: qualquer `[NEEDS CLARIFICATION]` aberto, ou stack de repositório envolvido indefinida.
- **Constitution Check**: violação de regra DEVE/NUNCA sem exceção justificada.
- **Analyze**: achado CRÍTICO persistente depois de uma correção.
- **Contratos congelados**: mudança só com aprovação do humano.
- **Converge**: tarefa de convergência pendente.

## Antipadrões mais comuns
Tecnologia na spec · regra de negócio presumida · critério de aceite vago ("rápido", "seguro") · plano que troca a stack · contrato escrito depois do código · tarefa sem caminho de arquivo ou sem requisito · código "corrigido" sem atualizar a spec. Detalhes e correções em `references/antipadroes.md`.

## Referências
- `references/artefatos.md` — ler quando for escrever ou revisar um artefato específico (conteúdo esperado e checklist de qualidade de cada um).
- `references/antipadroes.md` — ler quando o analyze, o review ou o converge apontarem problema de processo, ou ao revisar uma spec/plano de baixa qualidade.
