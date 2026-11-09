# Iterator

Aplica-se quando o código carrega uma coleção inteira na memória só para percorrê-la (ex.: todas as páginas de uma API, todas as linhas de um arquivo grande), ou quando o laço de paginação aparece repetido em vários lugares.

## Quando não usar
- Coleção pequena e já em memória: lista comum.
- Quem consome precisa do total ou de acesso por posição: a porta devolve a página com o total, não um iterável.

## Forma
- A linguagem já traz o padrão: gerador com `yield` no Python e `IAsyncEnumerable<T>` com `yield return` no .NET. A paginação fica escondida nele.
- Quem consome só faz `for` (ou `await foreach`) e pode parar no meio sem buscar as páginas restantes.
- A próxima página só é buscada quando a anterior acaba: a memória fica constante para qualquer volume.
- Com I/O no .NET, `IAsyncEnumerable` recebe o token com `[EnumeratorCancellation]`, para o cancelamento chegar à busca das páginas.
- Fica no adaptador de saída, que conhece a paginação da fonte; o caso de uso recebe o iterável.

## Python
```python
# paginacao.py
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Pagina:
    itens: tuple[str, ...]
    proximo_cursor: str | None


class FontePaginada(Protocol):
    def pagina(self, cursor: str | None) -> Pagina: ...


def todos_os_itens(fonte: FontePaginada) -> Iterator[str]:
    """Percorre as páginas sob demanda: a próxima só é buscada quando necessária."""
    cursor: str | None = None
    while True:
        pagina = fonte.pagina(cursor)
        yield from pagina.itens
        if pagina.proximo_cursor is None:
            return
        cursor = pagina.proximo_cursor
```

## .NET
```csharp
using System.Runtime.CompilerServices;

public sealed record Pagina(IReadOnlyList<string> Itens, string? ProximoCursor);

public interface IFontePaginada
{
    Task<Pagina> PaginaAsync(string? cursor, CancellationToken cancellationToken);
}

public static class Paginacao
{
    // Percorre as páginas sob demanda: a próxima só é buscada quando necessária.
    public static async IAsyncEnumerable<string> TodosOsItensAsync(
        IFontePaginada fonte, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        string? cursor = null;
        do
        {
            var pagina = await fonte.PaginaAsync(cursor, cancellationToken);
            foreach (var item in pagina.Itens)
            {
                yield return item;
            }

            cursor = pagina.ProximoCursor;
        }
        while (cursor is not null);
    }
}
```

## Como testar
- Com uma fonte fake de duas páginas: todos os itens, em ordem.
- Preguiça: depois do primeiro item, só a primeira página foi buscada.

```python
# test_paginacao.py
from paginacao import Pagina, todos_os_itens


class FonteFake:
    def __init__(self) -> None:
        self.paginas: dict[str | None, Pagina] = {
            None: Pagina(("a", "b"), "c2"),
            "c2": Pagina(("c",), None),
        }
        self.chamadas = 0

    def pagina(self, cursor: str | None) -> Pagina:
        self.chamadas += 1
        return self.paginas[cursor]


def test_todos_os_itens_percorre_as_paginas_em_ordem() -> None:
    assert list(todos_os_itens(FonteFake())) == ["a", "b", "c"]


def test_todos_os_itens_so_busca_a_proxima_pagina_quando_precisa() -> None:
    fonte = FonteFake()
    next(todos_os_itens(fonte))
    assert fonte.chamadas == 1
```

```csharp
public class PaginacaoTests
{
    private sealed class FonteFake : IFontePaginada
    {
        public int Chamadas { get; private set; }

        public Task<Pagina> PaginaAsync(string? cursor, CancellationToken cancellationToken)
        {
            Chamadas++;
            return Task.FromResult(cursor is null ? new Pagina(["a", "b"], "c2") : new Pagina(["c"], null));
        }
    }

    [Fact]
    public async Task TodosOsItensAsync_DuasPaginas_PercorreEmOrdem()
    {
        var itens = new List<string>();

        await foreach (var item in Paginacao.TodosOsItensAsync(new FonteFake(), CancellationToken.None))
        {
            itens.Add(item);
        }

        Assert.Equal(new[] { "a", "b", "c" }, itens);
    }

    [Fact]
    public async Task TodosOsItensAsync_PrimeiroItem_BuscaSoAPrimeiraPagina()
    {
        var fonte = new FonteFake();

        await using var itens = Paginacao.TodosOsItensAsync(fonte, CancellationToken.None).GetAsyncEnumerator();
        await itens.MoveNextAsync();

        Assert.Equal(1, fonte.Chamadas);
    }
}
```
