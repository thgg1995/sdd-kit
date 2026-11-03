---
name: dotnet-backend
description: Padrões de código .NET do time (async, tipagem, configuração, estrutura). Use em qualquer repositório com stack dotnet.
---

# .NET

## Versão e build (constitution §29)
- .NET LTS mais recente adotada pelo time. <!-- TIME: fixar versão -->
- `Directory.Build.props` com `<Nullable>enable</Nullable>`, `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>` e analisadores habilitados.

## Async (constitution §30)
- Async de ponta a ponta. Proibido `.Result`, `.Wait()`, `.GetAwaiter().GetResult()` e `async void` (exceto handlers de evento de UI).
- Todo método async público recebe e repassa `CancellationToken`.

## Tipagem (constitution §31)
- Nullable reference types habilitado; nada de `!` para silenciar aviso sem justificativa.
- DTOs como `record` imutáveis.

## Configuração
- `IOptions<T>` com validação na inicialização (`ValidateDataAnnotations().ValidateOnStart()`).
- Segredos conforme `aws-infra`.

## Estrutura
<!-- TIME: descrever a estrutura padrão (ex.: Api / Application / Domain / Infrastructure) -->
- Injeção de dependência pelo container padrão; sem service locator.
- Regras de negócio fora de controllers e consumers.
