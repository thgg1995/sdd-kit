---
name: data-nosql
description: Padrões para bancos não relacionais (DynamoDB, MongoDB e similares): modelagem por padrão de acesso, chaves, índices e dados sensíveis. Use em tarefas que criam ou alteram coleções, tabelas NoSQL ou suas consultas.
---

# Bancos não relacionais

## Modelagem por padrão de acesso (constitution §18)
Antes de qualquer código, o `plan.md` lista os padrões de acesso:
```
| Padrão | Chave usada | Índice | Frequência |
| Buscar pedido por id | PK=PEDIDO#<id> | tabela | alta |
| Pedidos do cliente por data | GSI1PK=CLIENTE#<id>, GSI1SK=<data> | GSI1 | média |
```
O modelo é derivado dessa tabela, não do modelo relacional.

## DynamoDB
- Use `Query` com chave de partição. `Scan` é proibido em código de produção.
- Chaves com prefixo de tipo (`PEDIDO#`, `CLIENTE#`); evite partições quentes (ex.: data como PK).
- Escritas condicionais (`ConditionExpression`) para idempotência e concorrência otimista.

## MongoDB
- Toda consulta usa campo indexado; índices declarados em código de inicialização/migração versionado (constitution §15, §17).
- Prefira embutir dados lidos juntos; referencie quando o subdocumento cresce sem limite.
- Valide documentos com JSON Schema da coleção quando possível.

## Evolução de schema (constitution §15)
- Documentos carregam `schemaVersion`. O código lê a versão atual e a anterior.
- Migração em lote só com script versionado no repositório.

## Dados sensíveis (constitution §19)
- Criptografia em repouso habilitada (KMS no DynamoDB, encryption at rest no Mongo).
- Campos de alto risco com criptografia em nível de aplicação/campo. <!-- TIME: definir quais -->
- Nunca logar documentos inteiros; logue chaves.
