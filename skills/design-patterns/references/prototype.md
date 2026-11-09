# Prototype

Aplica-se quando um objeto novo nasce de um existente com poucas mudanças (ex.: duplicar um pedido como rascunho, criar um plano a partir de um modelo), ou quando o código remonta do zero, campo a campo, um objeto que já existe como modelo.

## Quando não usar
- O objeto novo não tem relação com um existente: construtor (ou `references/builder.md`).
- Objeto mutável: torne-o imutável antes; cópias de objeto mutável divergem e escondem alterações.

## Forma
- A linguagem já traz o padrão: `dataclasses.replace` no Python e `with` nos records do C#. Não escreva método `clone()`.
- Objeto imutável com coleções imutáveis (`tuple` no Python): a cópia rasa fica segura.
- O `with` do C# copia referências: coleção dentro do record continua compartilhada. Crie uma coleção nova na cópia (`Itens = [.. Itens]`).
- Identidade e estado de ciclo de vida não se copiam: a operação que duplica troca o id e volta o status ao inicial, explicitamente.
- Duplicar é regra de negócio: fica na entidade ou no caso de uso, com nome (`duplicar_como_rascunho`).

## Python
```python
# rascunho.py
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import Enum


class StatusPedido(Enum):
    RASCUNHO = "rascunho"
    CONFIRMADO = "confirmado"


@dataclass(frozen=True)
class Item:
    sku: str
    quantidade: int
    preco: Decimal


@dataclass(frozen=True)
class Pedido:
    id: str
    cliente_id: str
    status: StatusPedido
    itens: tuple[Item, ...]


def duplicar_como_rascunho(pedido: Pedido, novo_id: str) -> Pedido:
    return replace(pedido, id=novo_id, status=StatusPedido.RASCUNHO)
```

## .NET
```csharp
public enum StatusPedido { Rascunho, Confirmado }

public sealed record Item(string Sku, int Quantidade, decimal Preco);

public sealed record Pedido(string Id, string ClienteId, StatusPedido Status, IReadOnlyList<Item> Itens)
{
    public Pedido DuplicarComoRascunho(string novoId) =>
        this with { Id = novoId, Status = StatusPedido.Rascunho, Itens = [.. Itens] };
}
```

## Como testar
- A cópia: id novo, status inicial e o restante igual ao original.
- O original não muda; no C#, a coleção da cópia é outra instância.

```python
# test_rascunho.py
from decimal import Decimal

from rascunho import Item, Pedido, StatusPedido, duplicar_como_rascunho


def test_duplicar_como_rascunho_troca_id_e_status_e_mantem_itens() -> None:
    itens = (Item("a", 2, Decimal(10)),)
    original = Pedido("p-1", "c-1", StatusPedido.CONFIRMADO, itens)
    copia = duplicar_como_rascunho(original, "p-2")
    assert (copia.id, copia.status) == ("p-2", StatusPedido.RASCUNHO)
    assert copia.itens == original.itens
    assert original.status is StatusPedido.CONFIRMADO
```

```csharp
public class PedidoTests
{
    [Fact]
    public void DuplicarComoRascunho_PedidoConfirmado_TrocaIdEStatusEMantemItens()
    {
        var original = new Pedido("p-1", "c-1", StatusPedido.Confirmado, [new Item("a", 2, 10m)]);

        var copia = original.DuplicarComoRascunho("p-2");

        Assert.Equal(("p-2", StatusPedido.Rascunho), (copia.Id, copia.Status));
        Assert.Equal(original.Itens, copia.Itens);
        Assert.NotSame(original.Itens, copia.Itens);
    }
}
```
