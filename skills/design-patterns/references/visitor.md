# Visitor

Aplica-se quando várias operações (calcular imposto, montar a linha da nota, validar) percorrem uma hierarquia fechada de tipos e o código tem `isinstance`/`is` espalhado, ou cada operação nova obriga a acrescentar um método em todos os tipos.

## Quando não usar
- Uma operação só, que pertence ao tipo: método no próprio tipo (polimorfismo comum).
- Hierarquia aberta (outros módulos criam tipos novos): método na interface, para cada tipo trazer o seu.

## Forma
- A linguagem já traz o padrão: pattern matching (`match` no Python, expressão `switch` no C#) no lugar do `accept`/`visit` do livro.
- Tipos fechados e imutáveis: dataclasses numa união no Python; records com uma base abstrata sem comportamento no C#.
- Uma função por operação, com um caso por tipo: a operação inteira fica num lugar só.
- Tipo novo exige um caso em todas as operações. O último caso é `assert_never(item)` no Python e `UnreachableException` no C#: o type checker (Python) acusa o tipo sem caso, e os dois falham alto se um tipo escapar em tempo de execução.

## Python
```python
# nota.py
from dataclasses import dataclass
from decimal import Decimal
from typing import assert_never

ALIQUOTA_PRODUTO = Decimal("0.18")
ALIQUOTA_SERVICO = Decimal("0.05")


@dataclass(frozen=True)
class Produto:
    descricao: str
    preco: Decimal


@dataclass(frozen=True)
class Servico:
    descricao: str
    horas: Decimal
    valor_hora: Decimal


@dataclass(frozen=True)
class Frete:
    valor: Decimal


ItemDaNota = Produto | Servico | Frete


def imposto(item: ItemDaNota) -> Decimal:
    match item:
        case Produto(preco=preco):
            return preco * ALIQUOTA_PRODUTO
        case Servico(horas=horas, valor_hora=valor_hora):
            return horas * valor_hora * ALIQUOTA_SERVICO
        case Frete():
            return Decimal(0)
        case _:
            assert_never(item)


def linha_da_nota(item: ItemDaNota) -> str:
    match item:
        case Produto(descricao=descricao, preco=preco):
            return f"{descricao}: {preco:.2f}"
        case Servico(descricao=descricao, horas=horas):
            return f"{descricao}: {horas} h"
        case Frete(valor=valor):
            return f"Frete: {valor:.2f}"
        case _:
            assert_never(item)
```

## .NET
```csharp
using System.Diagnostics;
using System.Globalization;

public abstract record ItemDaNota;

public sealed record Produto(string Descricao, decimal Preco) : ItemDaNota;

public sealed record Servico(string Descricao, decimal Horas, decimal ValorHora) : ItemDaNota;

public sealed record Frete(decimal Valor) : ItemDaNota;

public static class Nota
{
    private const decimal AliquotaProduto = 0.18m;
    private const decimal AliquotaServico = 0.05m;

    public static decimal Imposto(ItemDaNota item) => item switch
    {
        Produto produto => produto.Preco * AliquotaProduto,
        Servico servico => servico.Horas * servico.ValorHora * AliquotaServico,
        Frete => 0m,
        _ => throw new UnreachableException($"Item sem regra de imposto: {item.GetType().Name}"),
    };

    public static string LinhaDaNota(ItemDaNota item) => item switch
    {
        Produto produto => $"{produto.Descricao}: {Valor(produto.Preco)}",
        Servico servico => $"{servico.Descricao}: {servico.Horas.ToString(CultureInfo.InvariantCulture)} h",
        Frete frete => $"Frete: {Valor(frete.Valor)}",
        _ => throw new UnreachableException($"Item sem linha na nota: {item.GetType().Name}"),
    };

    private static string Valor(decimal valor) => valor.ToString("0.00", CultureInfo.InvariantCulture);
}
```

## Como testar
- Cada operação com um item de cada tipo.

```python
# test_nota.py
from decimal import Decimal

from nota import Frete, Produto, Servico, imposto, linha_da_nota

ITENS = [
    Produto("caneta", Decimal(10)),
    Servico("instalação", Decimal(2), Decimal(50)),
    Frete(Decimal(15)),
]


def test_imposto_aplica_a_regra_de_cada_tipo() -> None:
    assert [imposto(item) for item in ITENS] == [Decimal("1.8"), Decimal(5), Decimal(0)]


def test_linha_da_nota_descreve_cada_tipo() -> None:
    assert [linha_da_nota(item) for item in ITENS] == [
        "caneta: 10.00",
        "instalação: 2 h",
        "Frete: 15.00",
    ]
```

```csharp
public class NotaTests
{
    private static readonly ItemDaNota[] Itens =
        [new Produto("caneta", 10m), new Servico("instalação", 2m, 50m), new Frete(15m)];

    [Fact]
    public void Imposto_CadaTipo_AplicaASuaRegra() =>
        Assert.Equal(new[] { 1.8m, 5m, 0m }, Itens.Select(Nota.Imposto));

    [Fact]
    public void LinhaDaNota_CadaTipo_DescreveOItem() =>
        Assert.Equal(new[] { "caneta: 10.00", "instalação: 2 h", "Frete: 15.00" }, Itens.Select(Nota.LinhaDaNota));
}
```
