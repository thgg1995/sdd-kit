---
name: dotnet-backend
description: Padrões de código .NET do time (async, tipagem, configuração, estrutura). Use em qualquer repositório com stack dotnet.
---

# .NET

## Versão e build (constitution §29)
- .NET LTS mais recente adotada pelo time. <!-- TIME: fixar versão -->
- `Directory.Build.props` com `<Nullable>enable</Nullable>`, `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>` e analisadores habilitados.
- Limite de complexidade da `clean-code` pela regra CA1502 (o padrão dela é mais folgado):
  - `.editorconfig`, na seção `[*.cs]`: `dotnet_diagnostic.CA1502.severity = warning`;
  - `CodeMetricsConfig.txt` ao lado do `Directory.Build.props`, com a linha `CA1502: 10`;
  - no `Directory.Build.props`: `<ItemGroup><AdditionalFiles Include="$(MSBuildThisFileDirectory)CodeMetricsConfig.txt" /></ItemGroup>`.
- Supressão com motivo: `[SuppressMessage("Maintainability", "CA1502", Justification = "<motivo>")]`.
- Limite de parâmetros da `clean-code`: os analisadores padrão não o medem; o reviewer confere no diff.

## Async (constitution §30)
- Async de ponta a ponta. Proibido `.Result`, `.Wait()`, `.GetAwaiter().GetResult()` e `async void` (exceto handlers de evento de UI).
- Todo método async público recebe e repassa `CancellationToken`.

## Tipagem (constitution §31)
- Nullable reference types habilitado; nada de `!` para silenciar aviso sem justificativa.
- DTOs como `record` imutáveis.

## Configuração
- `IOptions<T>` com validação na inicialização (`ValidateDataAnnotations().ValidateOnStart()`).
- Segredos conforme `aws-infra`.

## Estrutura (constitution §32)
Camadas e níveis na `clean-architecture`; aqui, os nomes em .NET. <!-- TIME: ajustar os nomes, se o time usar outros -->
- Nível 1: um projeto `<Servico>` com `Function.cs` ou `Program.cs` (adaptador de entrada e composition root), `<CasoDeUso>.cs` (caso de uso, regras e portas) e um arquivo por tecnologia de saída.
- Nível 2: um projeto `<Servico>` com as pastas `Entrypoints/<Papel>/`, `Application/<CasoDeUso>/`, `Application/Ports/`, `Infrastructure/` e, se houver regra compartilhada, `Domain/`. Composition root em `Program.cs` (em Lambda, `Function.cs`).
- Nível 3: um projeto por camada — `<Servico>.Domain`, `<Servico>.Application`, `<Servico>.Infrastructure` e o de entrada (`<Servico>.Api`, `.Worker` ou `.Function`, conforme o papel). Referências: entrada → Application e Infrastructure (esta só para o composition root); Infrastructure → Application; Application → Domain; Domain → nenhum. A compilação barra o resto.
- Portas como `interface` em Application; implementações em Infrastructure, registradas no container pelo composition root.
- Injeção de dependência pelo container padrão; sem service locator.
- Regra de dependência nos níveis 1 e 2 conferida no review, pelos `using` de cada arquivo alterado. <!-- TIME: verificação automática (ex.: NetArchTest) é decisão do time; se adotada, declarar aqui -->
