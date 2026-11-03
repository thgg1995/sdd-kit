---
name: api-design
description: Padrões de APIs HTTP do time (erros, idempotência, paginação, timeouts, validação). Use em tarefas que criam ou alteram endpoints ou chamam APIs externas.
---

# APIs HTTP

## Contrato (constitution §5)
- O OpenAPI em `contracts/` é a fonte. Rotas, tipos e códigos de status seguem ele à risca.
- Gere clientes/modelos a partir do contrato quando o repositório já fizer isso; não duplique à mão.

## Erros (constitution §6)
Formato Problem Details (RFC 9457), `Content-Type: application/problem+json`.
- .NET: `builder.Services.AddProblemDetails();` + `app.UseExceptionHandler(); app.UseStatusCodePages();`
- Python (FastAPI): exception handler global que retorna `JSONResponse(..., media_type="application/problem+json")`.
- Nunca inclua stack trace, SQL ou mensagem de exceção interna. Logue o detalhe; devolva um `traceId`.

## Idempotência (constitution §7)
- `POST` com efeito colateral aceita o header `Idempotency-Key`.
- Guarde chave + hash do corpo + resposta por no mínimo 24h. <!-- TIME: ajustar retenção -->
- Mesma chave e mesmo corpo → devolva a resposta guardada. Mesma chave e corpo diferente → `422`.

## Paginação (constitution §8)
- Cursor (`?cursor=&limit=`), `limit` padrão 50, máximo 200. <!-- TIME: ajustar -->
- Resposta inclui `nextCursor` (nulo no fim).

## Chamadas externas (constitution §9)
- .NET: `services.AddHttpClient<TClient>().AddStandardResilienceHandler();` (Microsoft.Extensions.Http.Resilience), com timeout configurado.
- Python: `httpx.AsyncClient(timeout=httpx.Timeout(5.0))` + `tenacity` com backoff exponencial e jitter.
- Retente só: timeout, 429, 502, 503, 504. Nunca 4xx de negócio.

## Validação (constitution §23)
- .NET: FluentValidation ou DataAnnotations no DTO de entrada. Python: modelos Pydantic.
- Falha de validação → `400` com Problem Details listando os campos.
