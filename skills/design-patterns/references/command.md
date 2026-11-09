# Command

Aplica-se quando uma operação precisa existir como objeto (para ser validada, registrada, enfileirada ou auditada), ou quando o caso de uso recebe vários parâmetros soltos que, juntos, formam um pedido do usuário (`reajustar(categoria, variacao, motivo, ...)`).

## Quando não usar
- Chamada imediata com um ou dois parâmetros: chamada direta.
- Executar depois, em outro processo: o comando vira mensagem, com contrato em `contracts/` (producer e consumer da `clean-architecture`), não um objeto guardado em memória.
- Desfazer efeitos externos já feitos: é compensação, no caso de uso (`references/mediator.md`) ou no orquestrador de fluxo.

## Forma
- O comando é imutável, nomeado pela intenção com verbo (`ReajustarPrecos`), e traz tudo o que o caso de uso precisa; na criação, valida o que não depende de I/O.
- Um caso de uso por comando, com um método `executar(comando)`.
- O comando é um tipo da aplicação: o adaptador de entrada o monta a partir do request ou da mensagem.
- Ação sem dados a validar ou registrar é só uma função ou lambda; o objeto comando entra quando há dados.

## Python
```python
# reajuste.py
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Protocol

VARIACAO_MINIMA = Decimal("-0.5")
VARIACAO_MAXIMA = Decimal(1)


class ReajusteInvalido(Exception):
    """Erro de negócio: a variação está fora dos limites."""


@dataclass(frozen=True)
class ReajustarPrecos:
    """Comando: a intenção do usuário, com tudo o que o caso de uso precisa."""

    categoria: str
    variacao: Decimal  # fração: Decimal("0.10") é +10%
    motivo: str

    def __post_init__(self) -> None:
        if not VARIACAO_MINIMA <= self.variacao <= VARIACAO_MAXIMA:
            raise ReajusteInvalido(str(self.variacao))


@dataclass(frozen=True)
class Produto:
    sku: str
    categoria: str
    preco: Decimal


class Produtos(Protocol):
    def da_categoria(self, categoria: str) -> list[Produto]: ...

    def salvar(self, produto: Produto) -> None: ...


class ReajustarPrecosDaCategoria:
    def __init__(self, produtos: Produtos) -> None:
        self._produtos = produtos

    def executar(self, comando: ReajustarPrecos) -> int:
        produtos = self._produtos.da_categoria(comando.categoria)
        for produto in produtos:
            novo_preco = produto.preco * (1 + comando.variacao)
            self._produtos.salvar(replace(produto, preco=novo_preco))
        return len(produtos)
```

## .NET
```csharp
public sealed class ReajusteInvalidoException(decimal variacao)
    : Exception($"Variação fora dos limites: {variacao}");

// Comando: a intenção do usuário, com tudo o que o caso de uso precisa.
// Variação em fração: 0.10m é +10%.
public sealed record ReajustarPrecos
{
    private const decimal VariacaoMinima = -0.5m;
    private const decimal VariacaoMaxima = 1m;

    public ReajustarPrecos(string categoria, decimal variacao, string motivo)
    {
        if (variacao is < VariacaoMinima or > VariacaoMaxima)
        {
            throw new ReajusteInvalidoException(variacao);
        }

        Categoria = categoria;
        Variacao = variacao;
        Motivo = motivo;
    }

    public string Categoria { get; }

    public decimal Variacao { get; }

    public string Motivo { get; }
}

public sealed record Produto(string Sku, string Categoria, decimal Preco);

public interface IProdutos
{
    Task<IReadOnlyList<Produto>> DaCategoriaAsync(string categoria, CancellationToken cancellationToken);

    Task SalvarAsync(Produto produto, CancellationToken cancellationToken);
}

public sealed class ReajustarPrecosDaCategoria(IProdutos produtos)
{
    public async Task<int> ExecutarAsync(ReajustarPrecos comando, CancellationToken cancellationToken)
    {
        var daCategoria = await produtos.DaCategoriaAsync(comando.Categoria, cancellationToken);
        foreach (var produto in daCategoria)
        {
            var novoPreco = produto.Preco * (1 + comando.Variacao);
            await produtos.SalvarAsync(produto with { Preco = novoPreco }, cancellationToken);
        }

        return daCategoria.Count;
    }
}
```

## Como testar
- O comando: combinação inválida lança o erro de negócio na criação.
- O caso de uso: com um fake da porta, o efeito do comando e o resultado devolvido.

```python
# test_reajuste.py
from decimal import Decimal

import pytest

from reajuste import (
    Produto,
    ReajustarPrecos,
    ReajustarPrecosDaCategoria,
    ReajusteInvalido,
)


class ProdutosFake:
    def __init__(self, produtos: list[Produto]) -> None:
        self.por_sku = {produto.sku: produto for produto in produtos}

    def da_categoria(self, categoria: str) -> list[Produto]:
        return [
            produto
            for produto in self.por_sku.values()
            if produto.categoria == categoria
        ]

    def salvar(self, produto: Produto) -> None:
        self.por_sku[produto.sku] = produto


def test_reajustar_precos_com_variacao_acima_do_limite_lanca_erro() -> None:
    with pytest.raises(ReajusteInvalido):
        ReajustarPrecos("livros", Decimal(2), "erro de digitação")


def test_executar_reajusta_so_a_categoria_do_comando() -> None:
    produtos = ProdutosFake(
        [Produto("a", "livros", Decimal(10)), Produto("b", "jogos", Decimal(10))]
    )
    comando = ReajustarPrecos("livros", Decimal("0.10"), "inflação")
    assert ReajustarPrecosDaCategoria(produtos).executar(comando) == 1
    assert produtos.por_sku["a"].preco == Decimal(11)
    assert produtos.por_sku["b"].preco == Decimal(10)
```

```csharp
public class ReajustarPrecosTests
{
    private sealed class ProdutosFake(params Produto[] iniciais) : IProdutos
    {
        public Dictionary<string, Produto> PorSku { get; } = iniciais.ToDictionary(produto => produto.Sku);

        public Task<IReadOnlyList<Produto>> DaCategoriaAsync(string categoria, CancellationToken cancellationToken) =>
            Task.FromResult<IReadOnlyList<Produto>>([.. PorSku.Values.Where(produto => produto.Categoria == categoria)]);

        public Task SalvarAsync(Produto produto, CancellationToken cancellationToken)
        {
            PorSku[produto.Sku] = produto;
            return Task.CompletedTask;
        }
    }

    [Fact]
    public void Construtor_VariacaoAcimaDoLimite_LancaReajusteInvalido() =>
        Assert.Throws<ReajusteInvalidoException>(() => new ReajustarPrecos("livros", 2m, "erro de digitação"));

    [Fact]
    public async Task ExecutarAsync_DuasCategorias_ReajustaSoADoComando()
    {
        var produtos = new ProdutosFake(new Produto("a", "livros", 10m), new Produto("b", "jogos", 10m));

        var reajustados = await new ReajustarPrecosDaCategoria(produtos)
            .ExecutarAsync(new ReajustarPrecos("livros", 0.10m, "inflação"), CancellationToken.None);

        Assert.Equal(1, reajustados);
        Assert.Equal(11m, produtos.PorSku["a"].Preco);
        Assert.Equal(10m, produtos.PorSku["b"].Preco);
    }
}
```
