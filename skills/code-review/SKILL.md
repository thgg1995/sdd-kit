---
name: code-review
description: Como revisar um diff contra a constitution e as skills do time e reportar achados. Use sempre no papel reviewer.
---

# Code review

## Método
1. Leia o diff inteiro uma vez e liste as áreas tocadas (API, Kafka, dados, infra...).
2. Para cada área, confira as regras da constitution indicadas abaixo. Use a skill da área (já carregada pelo prompt) para saber como deveria estar feito.
3. Abra arquivos fora do diff só para confirmar uma suspeita concreta.

## Mapa área → regras
| Área no diff | Regras | Skill de referência |
|---|---|---|
| Endpoints, clientes HTTP | §5–9, §23 | `api-design` |
| Producers/consumers | §10–14 | `kafka-messaging` |
| Migrations, queries SQL | §15–17, §19 | `data-relational` |
| Coleções/tabelas NoSQL | §15, §17–19 | `data-nosql` |
| Terraform: estrutura, versões, estado, proteção de dados, segredos no estado, testes | §20–21, §26, §33 | `terraform` |
| Recursos AWS: IAM, segredos, criptografia, rede, SQS | §11, §19, §21–22, §25 | `aws-infra` |
| Lambda, Step Functions, agendamento | §9, §22, §24–25 | `aws-serverless` |
| Logs, tracing, health | §24–25 | `observability` |
| Testes | §26–28 | `unit-testing` |
| Qualquer código | §29–31 | skill da stack |
| Camadas, imports e adaptadores (back-end) | §32 | `clean-architecture` |
| Nomes, funções, classes, objetos, erros, comentários, SOLID; limites do linter | §29 | `clean-code-solid` |
| Padrões de projeto: sintoma sem padrão, padrão sem sintoma (back-end) | — | `design-patterns` |
| Fronteiras entre serviços | §1–4 | contratos em `contracts/` |

## Achados
- Cite a regra violada: `[arquivo:linha] §10 consumer sem deduplicação → gravar eventId em processed_events na mesma transação`.
- Violação de regra **DEVE/NUNCA** → `bloqueante`. Desvio de **DEVERIA** sem justificativa no plano → `bloqueante`; com justificativa → nada.
- Desvio de uma skill que não viola regra → `sugestão`.
- Não comente estilo que o linter/formatter resolve.
