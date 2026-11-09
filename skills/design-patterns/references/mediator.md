# Mediator

Aplica-se quando componentes se chamam em teia (o serviço de estoque chama o de pagamento, que chama o de expedição) e mudar a ordem ou acrescentar um passo mexe em vários lugares, ou quando surge a vontade de pôr um barramento em memória entre o adaptador e o caso de uso.

## Quando não usar
- Barramento ou mediator em memória entre adaptador e caso de uso (estilo MediatR): proibido sem decisão registrada em `research.md` (`clean-architecture`). O adaptador chama o caso de uso direto.
- Coordenação entre serviços diferentes: orquestrador de fluxo ou eventos, fora do processo (`clean-architecture`, tarefa orquestrada e producer).

## Forma
- No back-end, o caso de uso é o mediador: ele conhece as portas e decide a ordem; as portas não se conhecem nem se chamam.
- Cada passo é uma porta com a operação de que o caso de uso precisa. Acrescentar ou reordenar passos muda só o caso de uso.
- Falha no meio: quando o plano pede, o caso de uso desfaz o que já fez, em ordem inversa (compensação local), e relança o erro. Entre serviços, a compensação fica no orquestrador de fluxo.

## Python
```python
# fechamento.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


class PagamentoRecusado(Exception):
    """Erro de negócio: a cobrança foi recusada."""


@dataclass(frozen=True)
class Pedido:
    id: str
    total: Decimal


class Estoque(Protocol):
    def reservar(self, pedido_id: str) -> None: ...

    def liberar(self, pedido_id: str) -> None: ...


class Cobranca(Protocol):
    def cobrar(self, pedido_id: str, valor: Decimal) -> None: ...


class Expedicao(Protocol):
    def agendar(self, pedido_id: str) -> None: ...


class FecharPedido:
    """Mediador: as portas não se conhecem; a ordem e a compensação ficam aqui."""

    def __init__(
        self, estoque: Estoque, cobranca: Cobranca, expedicao: Expedicao
    ) -> None:
        self._estoque = estoque
        self._cobranca = cobranca
        self._expedicao = expedicao

    def executar(self, pedido: Pedido) -> None:
        self._estoque.reservar(pedido.id)
        try:
            self._cobranca.cobrar(pedido.id, pedido.total)
        except PagamentoRecusado:
            self._estoque.liberar(pedido.id)
            raise
        self._expedicao.agendar(pedido.id)
```

## .NET
```csharp
public sealed class PagamentoRecusadoException() : Exception("Pagamento recusado");

public sealed record Pedido(string Id, decimal Total);

public interface IEstoque
{
    Task ReservarAsync(string pedidoId, CancellationToken cancellationToken);

    Task LiberarAsync(string pedidoId, CancellationToken cancellationToken);
}

public interface ICobranca
{
    Task CobrarAsync(string pedidoId, decimal valor, CancellationToken cancellationToken);
}

public interface IExpedicao
{
    Task AgendarAsync(string pedidoId, CancellationToken cancellationToken);
}

// Mediador: as portas não se conhecem; a ordem e a compensação ficam aqui.
public sealed class FecharPedido(IEstoque estoque, ICobranca cobranca, IExpedicao expedicao)
{
    public async Task ExecutarAsync(Pedido pedido, CancellationToken cancellationToken)
    {
        await estoque.ReservarAsync(pedido.Id, cancellationToken);
        try
        {
            await cobranca.CobrarAsync(pedido.Id, pedido.Total, cancellationToken);
        }
        catch (PagamentoRecusadoException)
        {
            await estoque.LiberarAsync(pedido.Id, cancellationToken);
            throw;
        }

        await expedicao.AgendarAsync(pedido.Id, cancellationToken);
    }
}
```

## Como testar
- Um fake que implementa todas as portas e anota as chamadas: a ordem no caminho feliz e a compensação na falha.

```python
# test_fechamento.py
from decimal import Decimal

import pytest

from fechamento import FecharPedido, PagamentoRecusado, Pedido

PEDIDO = Pedido("p-1", Decimal(100))


class Portas:
    """Fake das três portas: anota as chamadas em ordem."""

    def __init__(self, falha_na_cobranca: Exception | None = None) -> None:
        self.chamadas: list[str] = []
        self._falha_na_cobranca = falha_na_cobranca

    def reservar(self, pedido_id: str) -> None:
        self.chamadas.append("reservar")

    def liberar(self, pedido_id: str) -> None:
        self.chamadas.append("liberar")

    def cobrar(self, pedido_id: str, valor: Decimal) -> None:
        self.chamadas.append("cobrar")
        if self._falha_na_cobranca is not None:
            raise self._falha_na_cobranca

    def agendar(self, pedido_id: str) -> None:
        self.chamadas.append("agendar")


def test_fechar_pedido_reserva_cobra_e_agenda_em_ordem() -> None:
    portas = Portas()
    FecharPedido(portas, portas, portas).executar(PEDIDO)
    assert portas.chamadas == ["reservar", "cobrar", "agendar"]


def test_fechar_pedido_com_pagamento_recusado_libera_o_estoque() -> None:
    portas = Portas(falha_na_cobranca=PagamentoRecusado())
    with pytest.raises(PagamentoRecusado):
        FecharPedido(portas, portas, portas).executar(PEDIDO)
    assert portas.chamadas == ["reservar", "cobrar", "liberar"]
```

```csharp
public class FecharPedidoTests
{
    private static readonly Pedido PedidoPadrao = new("p-1", 100m);

    private sealed class Portas(Exception? falhaNaCobranca = null) : IEstoque, ICobranca, IExpedicao
    {
        public List<string> Chamadas { get; } = [];

        public Task ReservarAsync(string pedidoId, CancellationToken cancellationToken) => Anotar("reservar");

        public Task LiberarAsync(string pedidoId, CancellationToken cancellationToken) => Anotar("liberar");

        public Task CobrarAsync(string pedidoId, decimal valor, CancellationToken cancellationToken)
        {
            Chamadas.Add("cobrar");
            return falhaNaCobranca is null ? Task.CompletedTask : Task.FromException(falhaNaCobranca);
        }

        public Task AgendarAsync(string pedidoId, CancellationToken cancellationToken) => Anotar("agendar");

        private Task Anotar(string chamada)
        {
            Chamadas.Add(chamada);
            return Task.CompletedTask;
        }
    }

    [Fact]
    public async Task ExecutarAsync_CaminhoFeliz_ReservaCobraEAgendaEmOrdem()
    {
        var portas = new Portas();

        await new FecharPedido(portas, portas, portas).ExecutarAsync(PedidoPadrao, CancellationToken.None);

        Assert.Equal(new[] { "reservar", "cobrar", "agendar" }, portas.Chamadas);
    }

    [Fact]
    public async Task ExecutarAsync_PagamentoRecusado_LiberaOEstoque()
    {
        var portas = new Portas(new PagamentoRecusadoException());

        await Assert.ThrowsAsync<PagamentoRecusadoException>(
            () => new FecharPedido(portas, portas, portas).ExecutarAsync(PedidoPadrao, CancellationToken.None));

        Assert.Equal(new[] { "reservar", "cobrar", "liberar" }, portas.Chamadas);
    }
}
```
