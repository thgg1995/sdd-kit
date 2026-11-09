# Decorator

Aplica-se quando cache, métrica, log ou retentativa de uma operação precisam envolver uma porta sem mudar o adaptador, ou quando esse código aparece copiado em vários adaptadores.

## Quando não usar
- Retentativa e timeout de chamada HTTP: use o mecanismo da `api-design`. De cliente de SDK: a configuração do próprio cliente (ex.: `botocore.config.Config`, na `aws-serverless`).
- Só um adaptador precisa do comportamento, e ele faz parte do que o adaptador é: escreva no próprio adaptador.
- Decorator que só repassa a chamada: remova.

## Forma
- Uma classe que implementa a mesma porta, recebe a implementação real no construtor e acrescenta o comportamento antes ou depois de chamá-la.
- O composition root monta o encadeamento (`ComCache(ComMetrica(Real(...)))`); o caso de uso recebe a porta e não sabe que há decorators.
- O decorator fica em infrastructure, junto dos adaptadores. Relógio e outras fontes de não determinismo entram por parâmetro.
- Decorator com estado (cache) vive o mesmo tempo que o estado; a implementação interna precisa aceitar esse tempo de vida (no .NET, abaixo: a `CotacaoHttp` recebe a `IHttpClientFactory` e cria o cliente a cada chamada, em vez de um typed client, que é transitório).
- Em Python, o decorador de função (`@...`) serve para funções; para envolver uma porta, use uma classe.

## Python
```python
# cotacao.py
from collections.abc import Callable
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol


class CotacaoCambio(Protocol):
    def cotacao(self, moeda: str) -> Decimal: ...


class CotacaoComCache:
    """Mesma porta da cotação real; guarda cada resultado pelo tempo de validade."""

    def __init__(
        self,
        interna: CotacaoCambio,
        validade: timedelta,
        agora: Callable[[], datetime],
    ) -> None:
        self._interna = interna
        self._validade = validade
        self._agora = agora
        self._guardadas: dict[str, tuple[Decimal, datetime]] = {}

    def cotacao(self, moeda: str) -> Decimal:
        guardada = self._guardadas.get(moeda)
        if guardada is not None and self._agora() - guardada[1] < self._validade:
            return guardada[0]
        valor = self._interna.cotacao(moeda)
        self._guardadas[moeda] = (valor, self._agora())
        return valor
```
No composition root: `CotacaoComCache(CotacaoHttp(cliente), config.validade_cotacao, agora=lambda: datetime.now(timezone.utc))`.

## .NET
```csharp
using System.Collections.Concurrent;

public interface ICotacaoCambio
{
    Task<decimal> CotacaoAsync(string moeda, CancellationToken cancellationToken);
}

public sealed class CotacaoComCache(ICotacaoCambio interna, TimeSpan validade, TimeProvider relogio)
    : ICotacaoCambio
{
    private readonly ConcurrentDictionary<string, (decimal Valor, DateTimeOffset GuardadaEm)> _guardadas = new();

    public async Task<decimal> CotacaoAsync(string moeda, CancellationToken cancellationToken)
    {
        if (_guardadas.TryGetValue(moeda, out var guardada)
            && relogio.GetUtcNow() - guardada.GuardadaEm < validade)
        {
            return guardada.Valor;
        }

        var valor = await interna.CotacaoAsync(moeda, cancellationToken);
        _guardadas[moeda] = (valor, relogio.GetUtcNow());
        return valor;
    }
}
```

O adaptador real e as opções usadas na composição:
```csharp
using System.Net.Http.Json;

public sealed class CotacaoHttp(IHttpClientFactory fabrica) : ICotacaoCambio
{
    public const string NomeDoCliente = "cotacao";

    public async Task<decimal> CotacaoAsync(string moeda, CancellationToken cancellationToken)
    {
        var cliente = fabrica.CreateClient(NomeDoCliente);
        return await cliente.GetFromJsonAsync<decimal>($"cotacoes/{moeda}", cancellationToken);
    }
}

public sealed class CotacaoOpcoes
{
    public required Uri Url { get; init; }

    public required TimeSpan Validade { get; init; }
}
```

```csharp
// composition root (Program.cs, em builder.Services)
// CotacaoOpcoes registrada e validada na inicialização (dotnet-backend); resiliência e timeout do cliente (api-design)
services.AddHttpClient(CotacaoHttp.NomeDoCliente, (provedor, cliente) =>
    cliente.BaseAddress = provedor.GetRequiredService<IOptions<CotacaoOpcoes>>().Value.Url);
services.AddSingleton<CotacaoHttp>();
services.AddSingleton<ICotacaoCambio>(provedor => new CotacaoComCache(
    provedor.GetRequiredService<CotacaoHttp>(),
    provedor.GetRequiredService<IOptions<CotacaoOpcoes>>().Value.Validade,
    TimeProvider.System));
```

## Como testar
- O decorator com um fake da porta (que conta as chamadas) e um relógio controlado: dentro da validade não chama a porta de novo; vencida, chama.
- A implementação real é testada sem o decorator; o caso de uso, com um fake da porta.

```python
# test_cotacao.py
from datetime import datetime, timedelta
from decimal import Decimal

from cotacao import CotacaoComCache


class CotacaoFake:
    def __init__(self) -> None:
        self.chamadas = 0

    def cotacao(self, moeda: str) -> Decimal:
        self.chamadas += 1
        return Decimal("5.10")


class Relogio:
    def __init__(self) -> None:
        self.instante = datetime(2026, 1, 1, 12, 0)

    def agora(self) -> datetime:
        return self.instante


def test_cotacao_dentro_da_validade_nao_chama_a_porta_de_novo() -> None:
    fake, relogio = CotacaoFake(), Relogio()
    cotacao = CotacaoComCache(fake, timedelta(minutes=5), relogio.agora)
    cotacao.cotacao("USD")
    relogio.instante += timedelta(minutes=4)
    cotacao.cotacao("USD")
    assert fake.chamadas == 1


def test_cotacao_vencida_chama_a_porta_de_novo() -> None:
    fake, relogio = CotacaoFake(), Relogio()
    cotacao = CotacaoComCache(fake, timedelta(minutes=5), relogio.agora)
    cotacao.cotacao("USD")
    relogio.instante += timedelta(minutes=5)
    cotacao.cotacao("USD")
    assert fake.chamadas == 2
```

```csharp
public class CotacaoComCacheTests
{
    private sealed class CotacaoFake : ICotacaoCambio
    {
        public int Chamadas { get; private set; }

        public Task<decimal> CotacaoAsync(string moeda, CancellationToken cancellationToken)
        {
            Chamadas++;
            return Task.FromResult(5.10m);
        }
    }

    private sealed class RelogioControlado : TimeProvider
    {
        public DateTimeOffset Agora { get; set; } = new(2026, 1, 1, 12, 0, 0, TimeSpan.Zero);

        public override DateTimeOffset GetUtcNow() => Agora;
    }

    [Fact]
    public async Task CotacaoAsync_DentroDaValidade_NaoChamaAPortaDeNovo()
    {
        var fake = new CotacaoFake();
        var relogio = new RelogioControlado();
        var cotacao = new CotacaoComCache(fake, TimeSpan.FromMinutes(5), relogio);

        await cotacao.CotacaoAsync("USD", CancellationToken.None);
        relogio.Agora += TimeSpan.FromMinutes(4);
        await cotacao.CotacaoAsync("USD", CancellationToken.None);

        Assert.Equal(1, fake.Chamadas);
    }

    [Fact]
    public async Task CotacaoAsync_Vencida_ChamaAPortaDeNovo()
    {
        var fake = new CotacaoFake();
        var relogio = new RelogioControlado();
        var cotacao = new CotacaoComCache(fake, TimeSpan.FromMinutes(5), relogio);

        await cotacao.CotacaoAsync("USD", CancellationToken.None);
        relogio.Agora += TimeSpan.FromMinutes(5);
        await cotacao.CotacaoAsync("USD", CancellationToken.None);

        Assert.Equal(2, fake.Chamadas);
    }
}
```
