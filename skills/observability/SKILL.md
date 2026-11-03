---
name: observability
description: Padrões de logs, tracing, health check e métricas. Use em tarefas que criam ou alteram endpoints, consumers ou serviços.
---

# Observabilidade

## Logs estruturados (constitution §24)
- JSON, com campos fixos: `timestamp`, `level`, `service`, `traceId`, `spanId`, `message`.
- .NET: Serilog (ou `ILogger` com formatter JSON). Python: `structlog` ou logging com formatter JSON. <!-- TIME: ajustar -->
- Use templates estruturados (`"Pedido {PedidoId} criado"`), nunca concatenação.
- Nunca logar payloads inteiros nem dados sensíveis (constitution §19).

## Correlação (constitution §24)
- Padrão W3C Trace Context (`traceparent`), via OpenTelemetry.
- HTTP: propagado automaticamente pela instrumentação. Kafka: injete/extraia o `traceparent` nos headers da mensagem.
- .NET: `builder.Services.AddOpenTelemetry().WithTracing(...).WithMetrics(...)` com instrumentação ASP.NET Core, HttpClient e do driver de banco.
- Python: `opentelemetry-instrumentation-*` para o framework web, httpx e driver de banco.

## Health check (constitution §25)
- `/health/live`: processo de pé. `/health/ready`: dependências críticas acessíveis (banco, broker).
- .NET: `AddHealthChecks()` + `MapHealthChecks`. Python: endpoints equivalentes no framework.

## Métricas (constitution §25)
- APIs: taxa de erro e latência (p50/p95/p99) por rota.
- Consumers: lag por partição, mensagens processadas, falhas e volume enviado à DLQ.
- Exportadas via OpenTelemetry. <!-- TIME: destino (CloudWatch, Prometheus, Datadog...) -->
