# Chain of Responsibility (pipeline)

Aplica-se quando o processamento é uma sequência de etapas (validar, calcular, aplicar desconto…) em que as etapas variam por tipo, canal ou configuração, ou quando uma função longa liga e desliga etapas por flags.

## Quando não usar
- Sequência fixa de duas ou três etapas, sempre as mesmas: chamadas diretas no caso de uso.
- Middleware HTTP (autenticação, correlação, erro global): use o pipeline do framework (middleware do ASP.NET Core, middleware e dependências do FastAPI).

## Forma
- Todas as etapas com a mesma assinatura: recebem o contexto e devolvem o contexto (imutável, com os campos que as etapas produzem).
- Uma função executa as etapas em ordem; uma etapa interrompe a cadeia lançando erro de negócio.
- A lista de etapas por tipo ou canal é um registro (dicionário); escolher a lista é o único `if`.
- Etapa com I/O recebe a porta de que precisa e vira assíncrona (`Func<Contexto, CancellationToken, Task<Contexto>>` no .NET); as etapas puras ficam síncronas.
- Variação "o primeiro que souber trata" (ex.: regras de preço por prioridade): cada elo devolve um resultado ou nada, e a cadeia para no primeiro resultado.
- Etapas e registro ficam em application.

## Python
```python
# checkout.py
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal

QUANTIDADE_PARA_DESCONTO = 10
PERCENTUAL_DE_DESCONTO = Decimal("0.05")


@dataclass(frozen=True)
class Item:
    sku: str
    preco: Decimal
    quantidade: int


@dataclass(frozen=True)
class Contexto:
    itens: tuple[Item, ...]
    subtotal: Decimal = Decimal(0)
    desconto: Decimal = Decimal(0)


class CarrinhoVazio(Exception):
    """Erro de negócio: não há itens para fechar o pedido."""


Etapa = Callable[[Contexto], Contexto]


def executar(contexto: Contexto, etapas: Sequence[Etapa]) -> Contexto:
    for etapa in etapas:
        contexto = etapa(contexto)
    return contexto


def validar_itens(contexto: Contexto) -> Contexto:
    if not contexto.itens:
        raise CarrinhoVazio()
    return contexto


def somar_itens(contexto: Contexto) -> Contexto:
    subtotal = sum(
        (item.preco * item.quantidade for item in contexto.itens), Decimal(0)
    )
    return replace(contexto, subtotal=subtotal)


def aplicar_desconto_por_quantidade(contexto: Contexto) -> Contexto:
    quantidade = sum(item.quantidade for item in contexto.itens)
    if quantidade < QUANTIDADE_PARA_DESCONTO:
        return contexto
    return replace(contexto, desconto=contexto.subtotal * PERCENTUAL_DE_DESCONTO)


ETAPAS_POR_CANAL: dict[str, tuple[Etapa, ...]] = {
    "loja": (validar_itens, somar_itens, aplicar_desconto_por_quantidade),
    "marketplace": (validar_itens, somar_itens),
}
```

## .NET
```csharp
public sealed record Item(string Sku, decimal Preco, int Quantidade);

public sealed record Contexto(IReadOnlyList<Item> Itens)
{
    public decimal Subtotal { get; init; }

    public decimal Desconto { get; init; }
}

public sealed class CarrinhoVazioException() : Exception("Carrinho vazio");

public delegate Contexto Etapa(Contexto contexto);

public static class Checkout
{
    private const int QuantidadeParaDesconto = 10;
    private const decimal PercentualDeDesconto = 0.05m;

    public static readonly IReadOnlyDictionary<string, Etapa[]> EtapasPorCanal =
        new Dictionary<string, Etapa[]>
        {
            ["loja"] = [ValidarItens, SomarItens, AplicarDescontoPorQuantidade],
            ["marketplace"] = [ValidarItens, SomarItens],
        };

    public static Contexto Executar(Contexto contexto, IEnumerable<Etapa> etapas) =>
        etapas.Aggregate(contexto, (atual, etapa) => etapa(atual));

    public static Contexto ValidarItens(Contexto contexto) =>
        contexto.Itens.Count > 0 ? contexto : throw new CarrinhoVazioException();

    public static Contexto SomarItens(Contexto contexto) =>
        contexto with { Subtotal = contexto.Itens.Sum(item => item.Preco * item.Quantidade) };

    public static Contexto AplicarDescontoPorQuantidade(Contexto contexto) =>
        contexto.Itens.Sum(item => item.Quantidade) < QuantidadeParaDesconto
            ? contexto
            : contexto with { Desconto = contexto.Subtotal * PercentualDeDesconto };
}
```

## Como testar
- Cada etapa sozinha: são funções puras, sem montar a cadeia.
- A cadeia de cada canal: o resultado final de um cenário completo e a interrupção pela etapa que lança erro.

```python
# test_checkout.py
from decimal import Decimal

import pytest

from checkout import (
    ETAPAS_POR_CANAL,
    CarrinhoVazio,
    Contexto,
    Item,
    aplicar_desconto_por_quantidade,
    executar,
)


def test_executar_carrinho_vazio_interrompe_na_validacao() -> None:
    with pytest.raises(CarrinhoVazio):
        executar(Contexto(itens=()), ETAPAS_POR_CANAL["loja"])


def test_executar_loja_com_dez_itens_aplica_desconto() -> None:
    contexto = Contexto(itens=(Item("a", Decimal(10), 10),))
    resultado = executar(contexto, ETAPAS_POR_CANAL["loja"])
    assert resultado.subtotal == Decimal(100)
    assert resultado.desconto == Decimal(5)


def test_aplicar_desconto_abaixo_da_quantidade_nao_altera() -> None:
    contexto = Contexto(itens=(Item("a", Decimal(10), 9),), subtotal=Decimal(90))
    assert aplicar_desconto_por_quantidade(contexto) == contexto
```

```csharp
public class CheckoutTests
{
    [Fact]
    public void Executar_CarrinhoVazio_InterrompeNaValidacao() =>
        Assert.Throws<CarrinhoVazioException>(
            () => Checkout.Executar(new Contexto([]), Checkout.EtapasPorCanal["loja"]));

    [Fact]
    public void Executar_LojaComDezItens_AplicaDesconto()
    {
        var resultado = Checkout.Executar(
            new Contexto([new Item("a", Preco: 10m, Quantidade: 10)]),
            Checkout.EtapasPorCanal["loja"]);

        Assert.Equal(100m, resultado.Subtotal);
        Assert.Equal(5m, resultado.Desconto);
    }
}
```
