---
name: data-relational
description: Padrões para bancos relacionais (migrations, consultas parametrizadas, índices, dados sensíveis). Use em tarefas que criam ou alteram tabelas, queries ou repositórios de dados SQL.
---

# Bancos relacionais

## Migrations (constitution §15)
- .NET: EF Core (`dotnet ef migrations add <Nome>`). Python: Alembic (`alembic revision --autogenerate -m "<nome>"`). <!-- TIME: ou Flyway/DbUp -->
- Toda migration é revisada à mão; nunca confie só no autogerado.
- Mudanças que quebram usam **expand → migrate → contract**, em deploys separados:
  1. expand: adiciona coluna/tabela nova (nullable ou com default);
  2. migrate: código grava nas duas e faz backfill;
  3. contract: remove o antigo só quando nenhuma versão em execução o usa.
- Proibido na mesma migration: renomear/remover coluna em uso, `NOT NULL` sem default em tabela com dados.

## Consultas (constitution §16)
- Sempre ORM ou parâmetros (`@p` no Dapper, `:p`/`text()` com bind no SQLAlchemy).
- `FromSqlRaw`/f-string com entrada externa: proibido. Use `FromSqlInterpolated` ou parâmetros.

## Índices (constitution §17)
- Toda consulta nova em caminho crítico declara o índice na mesma migration.
- Liste no `plan.md` as consultas críticas e o índice que as suporta.
- Evite `N+1`: carregue relacionamentos explicitamente (`Include`, `selectinload`).

## Transações
- Escopo curto; nenhuma chamada HTTP ou publicação Kafka dentro da transação (use outbox, ver `kafka-messaging`).

## Dados sensíveis (constitution §19)
- Colunas sensíveis marcadas no `plan.md`.
- Criptografia em repouso pelo banco/KMS; colunas de alto risco (documentos, dados financeiros) com criptografia em nível de aplicação. <!-- TIME: definir quais -->
- Nunca logar entidades inteiras; logue ids.
