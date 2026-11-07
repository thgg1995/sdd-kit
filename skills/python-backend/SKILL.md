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
- Limites da `clean-code` no `pyproject.toml`:
```toml
[tool.ruff.lint]
extend-select = ["C901", "PLR0913"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-args = 5
```
- Supressão com motivo, na linha do `def`: `# noqa: C901  # <motivo>` (ou `PLR0913`).

## Tipagem (constitution §31)
- Type hints em todo código novo; `mypy --strict` (ou pyright) sem erros nos módulos alterados.
- Modelos de entrada/saída com Pydantic.

## Async (constitution §30)
- Em código async, só bibliotecas async (httpx, asyncpg, aiokafka...). Proibido `requests`, `time.sleep` e drivers síncronos dentro de corrotinas.
- Trabalho bloqueante inevitável vai para `asyncio.to_thread`.

## Configuração
- `pydantic-settings`, validado na inicialização.
- Segredos conforme `aws-infra`.

## Estrutura (constitution §32)
Camadas e níveis na `clean-architecture`; aqui, os nomes em Python. <!-- TIME: ajustar os nomes, se o time usar outros -->
- Código em `src/<pacote>/`.
- Nível 1: `handler.py` (adaptador de entrada e composition root; ou o ponto de entrada que o runtime exige, ex.: `__main__.py`), `service.py` (caso de uso, regras puras e portas) e um módulo por tecnologia de saída (ex.: `aws.py`, `db.py`).
- Nível 2: `entrypoints/<papel>/`, `application/<caso_de_uso>/`, `application/ports.py`, `infrastructure/` e, se houver regra compartilhada, `domain/`. Composition root em `main.py`; em Lambda, no módulo do handler.
- Nível 3: o layout do nível 2, com o modelo de domínio em `domain/`.
- Portas com `typing.Protocol`.
- Regra de dependência conferida no review, pelos `import` de cada arquivo alterado. <!-- TIME: verificação automática (ex.: import-linter) é decisão do time; se adotada, declarar aqui -->
