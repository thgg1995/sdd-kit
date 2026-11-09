# Unit of Work

Aplica-se quando um caso de uso grava mais de uma coisa que precisa ser atômica (ex.: a entidade e o evento na outbox, §14), ou quando cada repositório abre e confirma a própria transação e uma falha no meio deixa o banco pela metade.

## Quando não usar
- Uma escrita só: o repositório grava direto; o banco garante a atomicidade dela.
- Escritas em serviços ou bancos diferentes: não há transação comum; use outbox, saga ou orquestrador de fluxo.
- Banco sem transação entre itens (ex.: DynamoDB fora de `TransactWriteItems`): a "unidade" é um método da porta que grava tudo numa operação atômica do banco (`data-nosql`).

## Forma
- A transação é delimitada pelo caso de uso: ele usa os repositórios da unidade e confirma no fim; sem confirmar, nada é gravado.
- Os repositórios usados na transação vêm da própria unidade (mesma conexão ou sessão).
- Gravar o evento na outbox pela mesma unidade é o que garante o §14 (evento só com a escrita; detalhes na `kafka-messaging`).
- Nas ferramentas: no SQLAlchemy, a sessão (`commit` em `confirmar`, `rollback` ao sair sem confirmar); no EF Core, o `DbContext` (`SaveChangesAsync` em `ConfirmarAsync`). A porta expõe só o que o caso de uso usa.
- Uma unidade por execução do caso de uso (o escopo da requisição ou da mensagem), nunca singleton.
- Regras do time: `clean-architecture` (transação no caso de uso).

## Python
```python
# confirmar_pedido.py
from dataclasses import dataclass, replace
from types import TracebackType
from typing import Protocol, Self


class PedidoNaoEncontrado(Exception):
    """Erro de negócio: não há pedido com esse id."""


@dataclass(frozen=True)
class Pedido:
    id: str
    confirmado: bool


@dataclass(frozen=True)
class PedidoConfirmado:
    pedido_id: str


class Pedidos(Protocol):
    def obter(self, pedido_id: str) -> Pedido: ...

    def salvar(self, pedido: Pedido) -> None: ...


class Outbox(Protocol):
    def adicionar(self, evento: PedidoConfirmado) -> None: ...


class UnidadeDeTrabalho(Protocol):
    """Uma transação: grava tudo junto em confirmar(); sair sem confirmar descarta."""

    pedidos: Pedidos
    outbox: Outbox

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        tipo: type[BaseException] | None,
        erro: BaseException | None,
        rastro: TracebackType | None,
    ) -> None: ...

    def confirmar(self) -> None: ...


class ConfirmarPedido:
    def __init__(self, unidade: UnidadeDeTrabalho) -> None:
        self._unidade = unidade

    def executar(self, pedido_id: str) -> None:
        with self._unidade as unidade:
            pedido = unidade.pedidos.obter(pedido_id)
            unidade.pedidos.salvar(replace(pedido, confirmado=True))
            unidade.outbox.adicionar(PedidoConfirmado(pedido_id))
            unidade.confirmar()
```

## .NET
```csharp
public sealed class PedidoNaoEncontradoException(string pedidoId)
    : Exception($"Pedido não encontrado: {pedidoId}");

public sealed record Pedido(string Id, bool Confirmado);

public sealed record PedidoConfirmado(string PedidoId);

public interface IPedidos
{
    Task<Pedido> ObterAsync(string pedidoId, CancellationToken cancellationToken);

    void Salvar(Pedido pedido);
}

public interface IOutbox
{
    void Adicionar(PedidoConfirmado evento);
}

// Uma transação: o que os repositórios dela registram é gravado junto em
// ConfirmarAsync; sem confirmar, nada é gravado. No EF Core, é o DbContext.
public interface IUnidadeDeTrabalho
{
    IPedidos Pedidos { get; }

    IOutbox Outbox { get; }

    Task ConfirmarAsync(CancellationToken cancellationToken);
}

public sealed class ConfirmarPedido(IUnidadeDeTrabalho unidade)
{
    public async Task ExecutarAsync(string pedidoId, CancellationToken cancellationToken)
    {
        var pedido = await unidade.Pedidos.ObterAsync(pedidoId, cancellationToken);
        unidade.Pedidos.Salvar(pedido with { Confirmado = true });
        unidade.Outbox.Adicionar(new PedidoConfirmado(pedidoId));
        await unidade.ConfirmarAsync(cancellationToken);
    }
}
```

## Como testar
- Com uma unidade fake que anota a confirmação: no caminho feliz, a entidade e o evento são registrados e a transação é confirmada.
- Erro no meio: a transação não é confirmada.
- A atomicidade de verdade (rollback no banco) fica para o teste de integração (`qa-integration`).

```python
# test_confirmar_pedido.py
from types import TracebackType
from typing import Self

import pytest

from confirmar_pedido import (
    ConfirmarPedido,
    Pedido,
    PedidoConfirmado,
    PedidoNaoEncontrado,
)


class PedidosFake:
    def __init__(self, pedidos: list[Pedido]) -> None:
        self.por_id = {pedido.id: pedido for pedido in pedidos}

    def obter(self, pedido_id: str) -> Pedido:
        if pedido_id not in self.por_id:
            raise PedidoNaoEncontrado(pedido_id)
        return self.por_id[pedido_id]

    def salvar(self, pedido: Pedido) -> None:
        self.por_id[pedido.id] = pedido


class OutboxFake:
    def __init__(self) -> None:
        self.eventos: list[PedidoConfirmado] = []

    def adicionar(self, evento: PedidoConfirmado) -> None:
        self.eventos.append(evento)


class UnidadeFake:
    def __init__(self, pedidos: list[Pedido]) -> None:
        self.pedidos = PedidosFake(pedidos)
        self.outbox = OutboxFake()
        self.confirmada = False

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        tipo: type[BaseException] | None,
        erro: BaseException | None,
        rastro: TracebackType | None,
    ) -> None:
        """No fake não há o que desfazer: o teste confere `confirmada`."""

    def confirmar(self) -> None:
        self.confirmada = True


def test_confirmar_pedido_grava_pedido_e_evento_na_mesma_transacao() -> None:
    unidade = UnidadeFake([Pedido("p-1", confirmado=False)])
    ConfirmarPedido(unidade).executar("p-1")
    assert unidade.confirmada
    assert unidade.pedidos.obter("p-1").confirmado
    assert unidade.outbox.eventos == [PedidoConfirmado("p-1")]


def test_confirmar_pedido_inexistente_nao_confirma_a_transacao() -> None:
    unidade = UnidadeFake([])
    with pytest.raises(PedidoNaoEncontrado):
        ConfirmarPedido(unidade).executar("p-9")
    assert not unidade.confirmada
```

```csharp
public class ConfirmarPedidoTests
{
    private sealed class UnidadeFake(params Pedido[] pedidos) : IUnidadeDeTrabalho, IPedidos, IOutbox
    {
        private readonly Dictionary<string, Pedido> _porId = pedidos.ToDictionary(pedido => pedido.Id);

        public List<PedidoConfirmado> Eventos { get; } = [];

        public bool Confirmada { get; private set; }

        public IPedidos Pedidos => this;

        public IOutbox Outbox => this;

        public Task<Pedido> ObterAsync(string pedidoId, CancellationToken cancellationToken) =>
            _porId.TryGetValue(pedidoId, out var pedido)
                ? Task.FromResult(pedido)
                : Task.FromException<Pedido>(new PedidoNaoEncontradoException(pedidoId));

        public void Salvar(Pedido pedido) => _porId[pedido.Id] = pedido;

        public void Adicionar(PedidoConfirmado evento) => Eventos.Add(evento);

        public Task ConfirmarAsync(CancellationToken cancellationToken)
        {
            Confirmada = true;
            return Task.CompletedTask;
        }

        public Pedido Obter(string pedidoId) => _porId[pedidoId];
    }

    [Fact]
    public async Task ExecutarAsync_PedidoExistente_GravaPedidoEEventoNaMesmaTransacao()
    {
        var unidade = new UnidadeFake(new Pedido("p-1", Confirmado: false));

        await new ConfirmarPedido(unidade).ExecutarAsync("p-1", CancellationToken.None);

        Assert.True(unidade.Confirmada);
        Assert.True(unidade.Obter("p-1").Confirmado);
        Assert.Equal(new[] { new PedidoConfirmado("p-1") }, unidade.Eventos);
    }

    [Fact]
    public async Task ExecutarAsync_PedidoInexistente_NaoConfirmaATransacao()
    {
        var unidade = new UnidadeFake();

        await Assert.ThrowsAsync<PedidoNaoEncontradoException>(
            () => new ConfirmarPedido(unidade).ExecutarAsync("p-9", CancellationToken.None));

        Assert.False(unidade.Confirmada);
    }
}
```
