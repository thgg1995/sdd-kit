---
name: python-backend
description: Padrões de código Python do time (tipagem, async, dependências, lint, estrutura). Use em qualquer repositório com stack python.
---

# Python

## Versão e dependências
- Python 3.12+. <!-- TIME: fixar versão -->
- Dependências com lockfile versionado (uv ou Poetry). <!-- TIME: escolher -->

## Lint e build (constitution §29)
- `ruff check` e `ruff format` sem erros novos.

## Tipagem (constitution §31)
- Type hints em todo código novo; `mypy --strict` (ou pyright) sem erros nos módulos alterados.
- Modelos de entrada/saída com Pydantic.

## Async (constitution §30)
- Em código async, só bibliotecas async (httpx, asyncpg, aiokafka...). Proibido `requests`, `time.sleep` e drivers síncronos dentro de corrotinas.
- Trabalho bloqueante inevitável vai para `asyncio.to_thread`.

## Configuração
- `pydantic-settings`, validado na inicialização.
- Segredos conforme `aws-infra`.

## Estrutura
<!-- TIME: descrever a estrutura padrão do time -->
- Regras de negócio fora de rotas e handlers de mensagem.
