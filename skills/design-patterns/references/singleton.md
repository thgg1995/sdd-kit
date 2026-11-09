# Singleton

Aplica-se quando um recurso deve existir uma vez por processo (cliente HTTP, pool de conexões, cache em memória, catálogo carregado na inicialização), ou quando o código tem instância global estática (`instancia()`, `Instance`, variável de módulo alterada em tempo de execução).

## Quando não usar
- A forma clássica (construtor privado e acesso estático) é proibida no kit (`SKILL.md`): esconde a dependência, impede trocar a instância no teste e guarda estado entre testes.
- Objeto barato e sem estado: crie onde precisar; instância única não traz ganho.

Sintoma no código (não faça):
```python
class Catalogo:
    _instancia = None

    @classmethod
    def instancia(cls) -> "Catalogo":
        if cls._instancia is None:
            cls._instancia = cls()
        return cls._instancia
```

## Forma
- "Uma instância só" é tempo de vida, decidido no composition root: ele cria o objeto uma vez e o entrega a quem precisa (Python) ou o registra como singleton no container (.NET).
- Quem usa recebe o objeto no construtor; nunca o busca num ponto global.
- No .NET, singleton não depende de serviço scoped (dependência capturada); o container acusa isso com a validação de escopos, ligada por padrão no ambiente de desenvolvimento.
- Em Lambda, o que é criado no carregamento do módulo vive entre as invocações da mesma instância; siga a `aws-serverless` para o que criar ali.

## Python
```python
# precos.py
from dataclasses import dataclass
from decimal import Decimal


class ProdutoDesconhecido(Exception):
    """Erro de negócio: o SKU não está no catálogo."""


class CatalogoEmMemoria:
    """Carregado uma vez na inicialização e compartilhado pelos casos de uso."""

    def __init__(self, precos: dict[str, Decimal]) -> None:
        self._precos = dict(precos)

    def preco(self, sku: str) -> Decimal:
        if sku not in self._precos:
            raise ProdutoDesconhecido(sku)
        return self._precos[sku]


class CalcularTotal:
    def __init__(self, catalogo: CatalogoEmMemoria) -> None:
        self._catalogo = catalogo

    def executar(self, skus: list[str]) -> Decimal:
        return sum((self._catalogo.preco(sku) for sku in skus), Decimal(0))


class EscolherMaisBarato:
    def __init__(self, catalogo: CatalogoEmMemoria) -> None:
        self._catalogo = catalogo

    def executar(self, skus: list[str]) -> str:
        return min(skus, key=self._catalogo.preco)


@dataclass(frozen=True)
class Aplicacao:
    calcular_total: CalcularTotal
    escolher_mais_barato: EscolherMaisBarato


def montar(precos: dict[str, Decimal]) -> Aplicacao:
    """Composition root: a única instância do catálogo nasce aqui."""
    catalogo = CatalogoEmMemoria(precos)
    return Aplicacao(CalcularTotal(catalogo), EscolherMaisBarato(catalogo))
```

## .NET
```csharp
public sealed class ProdutoDesconhecidoException(string sku)
    : Exception($"Produto desconhecido: {sku}");

// Carregado uma vez na inicialização e compartilhado pelos casos de uso.
public sealed class CatalogoEmMemoria(IReadOnlyDictionary<string, decimal> precos)
{
    public decimal Preco(string sku) =>
        precos.TryGetValue(sku, out var preco) ? preco : throw new ProdutoDesconhecidoException(sku);
}

public sealed class CalcularTotal(CatalogoEmMemoria catalogo)
{
    public decimal Executar(IEnumerable<string> skus) => skus.Sum(catalogo.Preco);
}

public sealed class EscolherMaisBarato(CatalogoEmMemoria catalogo)
{
    public string Executar(IEnumerable<string> skus) => skus.OrderBy(catalogo.Preco).First();
}

public sealed class CatalogoOpcoes
{
    public required Dictionary<string, decimal> Precos { get; init; }
}
```

```csharp
// composition root (Program.cs, em builder.Services); CatalogoOpcoes registrada conforme dotnet-backend
services.AddSingleton(provedor => new CatalogoEmMemoria(
    provedor.GetRequiredService<IOptions<CatalogoOpcoes>>().Value.Precos));
services.AddScoped<CalcularTotal>();
services.AddScoped<EscolherMaisBarato>();
```

## Como testar
- Cada teste cria a sua instância: não há estado global para limpar, e um teste não enxerga o que outro alterou.
- Os casos de uso recebem a instância no construtor, como em produção.

```python
# test_precos.py
from decimal import Decimal

from precos import montar

PRECOS = {"a": Decimal(10), "b": Decimal(5)}


def test_calcular_total_usa_o_catalogo_montado() -> None:
    assert montar(PRECOS).calcular_total.executar(["a", "b", "a"]) == Decimal(25)


def test_escolher_mais_barato_devolve_o_sku_de_menor_preco() -> None:
    assert montar(PRECOS).escolher_mais_barato.executar(["a", "b"]) == "b"


def test_cada_montagem_tem_seu_catalogo_sem_estado_global() -> None:
    caro = montar({"a": Decimal(20)})
    assert caro.calcular_total.executar(["a"]) == Decimal(20)
    assert montar(PRECOS).calcular_total.executar(["a"]) == Decimal(10)
```

```csharp
public class CatalogoTests
{
    private static CatalogoEmMemoria Catalogo() =>
        new(new Dictionary<string, decimal> { ["a"] = 10m, ["b"] = 5m });

    [Fact]
    public void Executar_CalcularTotal_SomaOsPrecosDoCatalogo() =>
        Assert.Equal(25m, new CalcularTotal(Catalogo()).Executar(["a", "b", "a"]));

    [Fact]
    public void Executar_EscolherMaisBarato_DevolveOSkuDeMenorPreco() =>
        Assert.Equal("b", new EscolherMaisBarato(Catalogo()).Executar(["a", "b"]));
}
```
