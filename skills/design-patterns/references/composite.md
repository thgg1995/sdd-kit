# Composite

Aplica-se quando há estrutura em árvore em que item e grupo são tratados do mesmo jeito (ex.: produto e kit de produtos; regra simples e regra composta), ou quando o código testa o tipo do item (`isinstance`, `is Kit`) para percorrer grupos.

## Quando não usar
- Lista de um nível só, sem grupo dentro de grupo: lista simples.
- Item e grupo não têm operação em comum: não é Composite; são dois tipos distintos.

## Forma
- Uma interface com as operações que valem para item e grupo.
- O item (folha) implementa direto; o grupo guarda os filhos (do tipo da interface) e combina o resultado deles. Grupo dentro de grupo funciona pela recursão.
- Grupo imutável, montado com os filhos já prontos: não há como um grupo conter a si mesmo.
- Persistir a árvore (ex.: tabela com a referência ao pai) é trabalho do adaptador; a árvore em memória fica em domain ou application.

## Python
```python
# catalogo.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


class ItemDeCatalogo(Protocol):
    def preco(self) -> Decimal: ...


@dataclass(frozen=True)
class Produto:
    sku: str
    preco_unitario: Decimal

    def preco(self) -> Decimal:
        return self.preco_unitario


@dataclass(frozen=True)
class Kit:
    nome: str
    itens: tuple[ItemDeCatalogo, ...]
    desconto: Decimal  # fração: Decimal("0.10") é 10%

    def preco(self) -> Decimal:
        bruto = sum((item.preco() for item in self.itens), Decimal(0))
        return bruto * (1 - self.desconto)
```

## .NET
```csharp
public interface IItemDeCatalogo
{
    decimal Preco();
}

public sealed record Produto(string Sku, decimal PrecoUnitario) : IItemDeCatalogo
{
    public decimal Preco() => PrecoUnitario;
}

// Desconto em fração: 0.10m é 10%.
public sealed record Kit(string Nome, IReadOnlyList<IItemDeCatalogo> Itens, decimal Desconto)
    : IItemDeCatalogo
{
    public decimal Preco() => Itens.Sum(item => item.Preco()) * (1 - Desconto);
}
```

## Como testar
- A folha sozinha; o grupo com folhas; grupo dentro de grupo; grupo vazio.

```python
# test_catalogo.py
from decimal import Decimal

from catalogo import Kit, Produto


def test_preco_kit_soma_itens_com_desconto() -> None:
    itens = (Produto("a", Decimal(60)), Produto("b", Decimal(40)))
    assert Kit("kit", itens, Decimal("0.10")).preco() == Decimal(90)


def test_preco_kit_dentro_de_kit_soma_recursivamente() -> None:
    interno = Kit("interno", (Produto("a", Decimal(50)),), Decimal(0))
    externo = Kit("externo", (interno, Produto("b", Decimal(50))), Decimal(0))
    assert externo.preco() == Decimal(100)


def test_preco_kit_vazio_e_zero() -> None:
    assert Kit("vazio", (), Decimal(0)).preco() == Decimal(0)
```

```csharp
public class KitTests
{
    [Fact]
    public void Preco_KitComDesconto_SomaItensComDesconto()
    {
        var kit = new Kit("kit", [new Produto("a", 60m), new Produto("b", 40m)], Desconto: 0.10m);

        Assert.Equal(90m, kit.Preco());
    }

    [Fact]
    public void Preco_KitDentroDeKit_SomaRecursivamente()
    {
        var interno = new Kit("interno", [new Produto("a", 50m)], Desconto: 0m);
        var externo = new Kit("externo", [interno, new Produto("b", 50m)], Desconto: 0m);

        Assert.Equal(100m, externo.Preco());
    }
}
```
