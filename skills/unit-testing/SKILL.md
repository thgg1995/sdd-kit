---
name: unit-testing
description: Como escrever testes unitários no padrão do time (.NET e Python). Use sempre que o dev implementa uma tarefa.
---

# Testes unitários (constitution §26)

## O que testar
- Cada tarefa: o comportamento esperado + cada caso de erro e de borda listado no `plan.md`.
- Teste comportamento observável (retorno, estado, evento publicado), não detalhes de implementação.
- Regra de negócio sem I/O: teste unitário. Banco/Kafka reais: teste de integração (`qa-integration`).

## Estrutura
- Arrange / Act / Assert, um comportamento por teste.
- Nome: `Metodo_Cenario_ResultadoEsperado` (.NET) ou `test_<metodo>_<cenario>_<resultado>` (Python).
- Sem dependência de ordem, de relógio ou de rede: injete relógio e dependências.

## .NET
- xUnit + FluentAssertions; mocks com NSubstitute. <!-- TIME: ou Moq/NUnit -->
- Projeto de teste espelha o projeto de produção (`<Projeto>.Tests`).
- Rodar um teste: `dotnet test --filter "FullyQualifiedName~<Nome>"`.

## Python
- pytest; mocks com `pytest-mock`; assíncrono com `pytest-asyncio`.
- Pasta `tests/` espelhando o pacote.
- Rodar um teste: `pytest -k <nome>`.

## Mocks
- Mocke só fronteiras (repositórios, clientes HTTP, producer Kafka). Nunca mocke a classe sob teste.
- Prefira fakes simples em memória a mocks com muitas expectativas.
