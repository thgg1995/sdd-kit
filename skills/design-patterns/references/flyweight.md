# Flyweight

Aplica-se quando uma medição de memória mostra muitas instâncias com o mesmo valor imutável (ex.: milhões de linhas de um arquivo, cada uma com o seu objeto `Categoria` igual aos das outras) e o volume de dados do plano chega a esse ponto.

## Quando não usar
- Sem medição: o ganho é especulativo e o código fica mais complexo. Meça antes (`tracemalloc` no Python; `dotnet-counters` ou um dump do heap no .NET).
- Objeto mutável: compartilhar instância mutável é bug. Flyweight só vale para valor imutável.

## Forma
- Uma fábrica com dicionário devolve a mesma instância para o mesmo valor; quem usa pede à fábrica em vez de construir.
- A fábrica é uma instância criada no composition root e entregue a quem processa, nunca estado global (`SKILL.md`, Proibido).
- O que muda de um objeto para outro (a parte extrínseca: quantidade, preço da linha) fica fora do objeto compartilhado.
- Antes do Flyweight, veja se basta reduzir o custo por objeto: `@dataclass(slots=True)` no Python; `record struct` no .NET.

## Python
```python
# categorias.py
from dataclasses import dataclass
from decimal import Decimal


class CategoriaDesconhecida(Exception):
    """Erro de negócio: a categoria não está na tabela de alíquotas."""


@dataclass(frozen=True)
class Categoria:
    nome: str
    aliquota: Decimal


class Categorias:
    """Fábrica de flyweights: uma instância de Categoria por nome."""

    def __init__(self, aliquotas: dict[str, Decimal]) -> None:
        self._aliquotas = dict(aliquotas)
        self._compartilhadas: dict[str, Categoria] = {}

    def obter(self, nome: str) -> Categoria:
        if nome not in self._aliquotas:
            raise CategoriaDesconhecida(nome)
        if nome not in self._compartilhadas:
            self._compartilhadas[nome] = Categoria(nome, self._aliquotas[nome])
        return self._compartilhadas[nome]
```

## .NET
```csharp
using System.Collections.Concurrent;

public sealed record Categoria(string Nome, decimal Aliquota);

public sealed class CategoriaDesconhecidaException(string nome)
    : Exception($"Categoria desconhecida: {nome}");

// Fábrica de flyweights: uma instância de Categoria por nome; registrada como singleton.
public sealed class Categorias(IReadOnlyDictionary<string, decimal> aliquotas)
{
    private readonly ConcurrentDictionary<string, Categoria> _compartilhadas = new();

    public Categoria Obter(string nome) =>
        aliquotas.TryGetValue(nome, out var aliquota)
            ? _compartilhadas.GetOrAdd(nome, chave => new Categoria(chave, aliquota))
            : throw new CategoriaDesconhecidaException(nome);
}
```

## Como testar
- O mesmo valor pedido duas vezes devolve a mesma instância (`is` no Python, `Assert.Same` no .NET).
- Valor desconhecido: o erro de negócio.
- O ganho de memória se confirma com a mesma medição que motivou o padrão, não em teste unitário.

```python
# test_categorias.py
from decimal import Decimal

import pytest

from categorias import CategoriaDesconhecida, Categorias


def test_obter_mesmo_nome_devolve_a_mesma_instancia() -> None:
    categorias = Categorias({"alimentos": Decimal("0.07")})
    assert categorias.obter("alimentos") is categorias.obter("alimentos")


def test_obter_nome_desconhecido_lanca_erro() -> None:
    with pytest.raises(CategoriaDesconhecida):
        Categorias({}).obter("joias")
```

```csharp
public class CategoriasTests
{
    [Fact]
    public void Obter_MesmoNome_DevolveAMesmaInstancia()
    {
        var categorias = new Categorias(new Dictionary<string, decimal> { ["alimentos"] = 0.07m });

        Assert.Same(categorias.Obter("alimentos"), categorias.Obter("alimentos"));
    }

    [Fact]
    public void Obter_NomeDesconhecido_LancaCategoriaDesconhecida() =>
        Assert.Throws<CategoriaDesconhecidaException>(
            () => new Categorias(new Dictionary<string, decimal>()).Obter("joias"));
}
```
