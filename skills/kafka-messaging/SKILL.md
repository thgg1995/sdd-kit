---
name: kafka-messaging
description: Padrões do time para producers e consumers Kafka (idempotência, DLQ, schema, ordenação, outbox). Use em tarefas que envolvem tópicos, eventos ou consumers.
---

# Kafka

## Idempotência (constitution §10)
- Todo evento carrega `eventId` (UUID) no header.
- Tabela/coleção `processed_events (event_id PK, processed_at)`, gravada **na mesma transação** do efeito de negócio.
- `eventId` já existe → não reprocessa, só avança o offset.

## Falhas e DLQ (constitution §11)
- 3 retentativas em memória com backoff exponencial. <!-- TIME: ajustar -->
- Esgotou → publica em `<topico>.dlq` com headers `error-reason`, `original-topic`, `original-partition`, `original-offset`; depois avança o offset.
- Erro de desserialização/schema vai direto para a DLQ (não adianta retentar).

## Offset
Avance o offset só depois de processar ou enviar para a DLQ.
- .NET (Confluent.Kafka): `EnableAutoCommit = true`, `EnableAutoOffsetStore = false`; após processar, `consumer.StoreOffset(result);`
- Python (confluent-kafka): `"enable.auto.commit": False`; após processar, `consumer.commit(message=msg, asynchronous=False)`.

## Schema (constitution §12)
- O schema do evento está em `contracts/`. Produtor valida antes de publicar; consumidor valida ao ler.
- Evolução compatível conforme `architecture`. <!-- TIME: se usarem Schema Registry, configurar compatibilidade BACKWARD -->

## Ordenação (constitution §13)
- A chave da mensagem é o id do agregado (ex.: `pedidoId`). Eventos do mesmo agregado ficam na mesma partição.
- Producer com `enable.idempotence=true` e `acks=all`.

## Outbox (constitution §14)
1. Na mesma transação da escrita de negócio, grave o evento na tabela `outbox (id, topic, key, payload, headers, created_at, published_at)`.
2. Um publicador lê pendentes em ordem, publica e marca `published_at`.
3. Alternativa aceita: CDC (ex.: Debezium) sobre a tabela outbox.

## Observabilidade
Propague o `traceparent` nos headers da mensagem (constitution §24) e exponha lag e volume de DLQ (constitution §25).
