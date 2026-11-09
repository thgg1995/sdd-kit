# Abstract Factory

Aplica-se quando duas ou mais famílias de objetos variam juntas e precisam ser usadas em conjunto (ex.: por provedor de pagamento, o formato da cobrança e a leitura do webhook), ou quando o código escolhe cada peça separadamente por `if provedor == ...` e misturar peças de famílias diferentes é bug.

## Quando não usar
- Uma família só: crie as peças direto.
- O código só chama operações e as peças não saem do lugar onde são usadas: é Strategy com várias operações (`references/strategy.md`).
- Uma peça só por família: é Factory Method (`references/factory-method.md`).

## Forma
- Uma fábrica por família, com um método por peça; todas as fábricas seguem a mesma interface.
- O composition root escolhe a família pela configuração e monta as peças a partir dela; cada peça vai para quem a usa (ex.: o formato para o caso de uso de cobrança, o leitor para o adaptador do webhook).
- As peças de uma família só nascem da fábrica dela: ninguém cria uma peça avulsa.
- Fábricas e peças sem I/O ficam em application; peças que fazem I/O são adaptadores em infrastructure.

## Python
```python
# provedores.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

CENTAVOS_POR_REAL = 100


@dataclass(frozen=True)
class Cobranca:
    pedido_id: str
    valor: Decimal


@dataclass(frozen=True)
class Pagamento:
    pedido_id: str
    pago: bool


class ProvedorDesconhecido(Exception):
    """Erro de negócio: o provedor configurado não existe."""


class FormatoDeCobranca(Protocol):
    def corpo(self, cobranca: Cobranca) -> dict[str, str]: ...


class LeitorDeWebhook(Protocol):
    def ler(self, corpo: dict[str, str]) -> Pagamento: ...


class FamiliaDeProvedor(Protocol):
    def formato_de_cobranca(self) -> FormatoDeCobranca: ...

    def leitor_de_webhook(self) -> LeitorDeWebhook: ...


class _FormatoAlfa:
    def corpo(self, cobranca: Cobranca) -> dict[str, str]:
        centavos = int(cobranca.valor * CENTAVOS_POR_REAL)
        return {"reference": cobranca.pedido_id, "amount_cents": str(centavos)}


class _LeitorAlfa:
    def ler(self, corpo: dict[str, str]) -> Pagamento:
        return Pagamento(corpo["reference"], corpo["status"] == "paid")


class FamiliaAlfa:
    def formato_de_cobranca(self) -> FormatoDeCobranca:
        return _FormatoAlfa()

    def leitor_de_webhook(self) -> LeitorDeWebhook:
        return _LeitorAlfa()


class _FormatoBeta:
    def corpo(self, cobranca: Cobranca) -> dict[str, str]:
        return {"pedido": cobranca.pedido_id, "valor": f"{cobranca.valor:.2f}"}


class _LeitorBeta:
    def ler(self, corpo: dict[str, str]) -> Pagamento:
        return Pagamento(corpo["pedido"], corpo["situacao"] == "PAGO")


class FamiliaBeta:
    def formato_de_cobranca(self) -> FormatoDeCobranca:
        return _FormatoBeta()

    def leitor_de_webhook(self) -> LeitorDeWebhook:
        return _LeitorBeta()


FAMILIAS: dict[str, FamiliaDeProvedor] = {"alfa": FamiliaAlfa(), "beta": FamiliaBeta()}


def obter_familia(nome: str) -> FamiliaDeProvedor:
    if nome not in FAMILIAS:
        raise ProvedorDesconhecido(nome)
    return FAMILIAS[nome]
```
No composition root: `familia = obter_familia(config.provedor)`, e cada peça vai para quem a usa (`CobrarPedido(familia.formato_de_cobranca(), ...)`, `WebhookDePagamento(familia.leitor_de_webhook(), ...)`).

## .NET
```csharp
using System.Globalization;

public sealed record Cobranca(string PedidoId, decimal Valor);

public sealed record Pagamento(string PedidoId, bool Pago);

public sealed class ProvedorDesconhecidoException(string nome)
    : Exception($"Provedor desconhecido: {nome}");

public interface IFormatoDeCobranca
{
    IReadOnlyDictionary<string, string> Corpo(Cobranca cobranca);
}

public interface ILeitorDeWebhook
{
    Pagamento Ler(IReadOnlyDictionary<string, string> corpo);
}

public interface IFamiliaDeProvedor
{
    IFormatoDeCobranca FormatoDeCobranca();

    ILeitorDeWebhook LeitorDeWebhook();
}

public sealed class FamiliaAlfa : IFamiliaDeProvedor
{
    private const int CentavosPorReal = 100;

    public IFormatoDeCobranca FormatoDeCobranca() => new Formato();

    public ILeitorDeWebhook LeitorDeWebhook() => new Leitor();

    private sealed class Formato : IFormatoDeCobranca
    {
        public IReadOnlyDictionary<string, string> Corpo(Cobranca cobranca) =>
            new Dictionary<string, string>
            {
                ["reference"] = cobranca.PedidoId,
                ["amount_cents"] = ((long)(cobranca.Valor * CentavosPorReal))
                    .ToString(CultureInfo.InvariantCulture),
            };
    }

    private sealed class Leitor : ILeitorDeWebhook
    {
        public Pagamento Ler(IReadOnlyDictionary<string, string> corpo) =>
            new(corpo["reference"], corpo["status"] == "paid");
    }
}

public sealed class FamiliaBeta : IFamiliaDeProvedor
{
    public IFormatoDeCobranca FormatoDeCobranca() => new Formato();

    public ILeitorDeWebhook LeitorDeWebhook() => new Leitor();

    private sealed class Formato : IFormatoDeCobranca
    {
        public IReadOnlyDictionary<string, string> Corpo(Cobranca cobranca) =>
            new Dictionary<string, string>
            {
                ["pedido"] = cobranca.PedidoId,
                ["valor"] = cobranca.Valor.ToString("0.00", CultureInfo.InvariantCulture),
            };
    }

    private sealed class Leitor : ILeitorDeWebhook
    {
        public Pagamento Ler(IReadOnlyDictionary<string, string> corpo) =>
            new(corpo["pedido"], corpo["situacao"] == "PAGO");
    }
}

public sealed class PagamentosOpcoes
{
    public required string Provedor { get; init; }
}
```

```csharp
// composition root (Program.cs, em builder.Services); PagamentosOpcoes registrada conforme dotnet-backend
services.AddSingleton<IFamiliaDeProvedor>(provedor =>
    provedor.GetRequiredService<IOptions<PagamentosOpcoes>>().Value.Provedor switch
    {
        "alfa" => new FamiliaAlfa(),
        "beta" => new FamiliaBeta(),
        var nome => throw new ProvedorDesconhecidoException(nome),
    });
services.AddSingleton(provedor => provedor.GetRequiredService<IFamiliaDeProvedor>().FormatoDeCobranca());
services.AddSingleton(provedor => provedor.GetRequiredService<IFamiliaDeProvedor>().LeitorDeWebhook());
```

## Como testar
- Cada família: as peças dela funcionam juntas (o leitor entende o formato do próprio provedor).
- As regras de cada peça (ex.: valor em centavos) e a família desconhecida.

```python
# test_provedores.py
from decimal import Decimal

import pytest

from provedores import Cobranca, ProvedorDesconhecido, obter_familia


@pytest.mark.parametrize(
    ("provedor", "webhook_pago"),
    [
        ("alfa", {"reference": "p-1", "status": "paid"}),
        ("beta", {"pedido": "p-1", "situacao": "PAGO"}),
    ],
)
def test_leitor_entende_o_webhook_da_propria_familia(
    provedor: str, webhook_pago: dict[str, str]
) -> None:
    pagamento = obter_familia(provedor).leitor_de_webhook().ler(webhook_pago)
    assert pagamento.pago
    assert pagamento.pedido_id == "p-1"


def test_formato_alfa_envia_valor_em_centavos() -> None:
    formato = obter_familia("alfa").formato_de_cobranca()
    assert formato.corpo(Cobranca("p-1", Decimal("10.50")))["amount_cents"] == "1050"


def test_obter_familia_desconhecida_lanca_erro() -> None:
    with pytest.raises(ProvedorDesconhecido):
        obter_familia("gama")
```

```csharp
public class FamiliasDeProvedorTests
{
    [Fact]
    public void LeitorDeWebhook_Alfa_EntendeOFormatoDaPropriaFamilia() =>
        Assert.True(new FamiliaAlfa().LeitorDeWebhook()
            .Ler(new Dictionary<string, string> { ["reference"] = "p-1", ["status"] = "paid" })
            .Pago);

    [Fact]
    public void LeitorDeWebhook_Beta_EntendeOFormatoDaPropriaFamilia() =>
        Assert.True(new FamiliaBeta().LeitorDeWebhook()
            .Ler(new Dictionary<string, string> { ["pedido"] = "p-1", ["situacao"] = "PAGO" })
            .Pago);

    [Fact]
    public void FormatoDeCobranca_Alfa_EnviaValorEmCentavos() =>
        Assert.Equal(
            "1050",
            new FamiliaAlfa().FormatoDeCobranca().Corpo(new Cobranca("p-1", 10.50m))["amount_cents"]);
}
```
