# Repository

Aplica-se quando um caso de uso precisa ler ou gravar uma entidade (ou um agregado, no nível 3), ou ao escrever o fake do repositório para os testes unitários.

## Quando não usar
- Leitura para tela ou relatório que não carrega a entidade: porta de consulta própria, devolvendo o formato da leitura (`clean-architecture`: leitura sem regra vai direto à porta).
- Dado de outro serviço: API ou evento do dono (§2), não repositório.

## Forma
- Uma porta por entidade (por raiz de agregado, no nível 3), com as operações que os casos de uso usam, nomeadas pela intenção (`do_cliente`, não `buscar_por_filtro`).
- Recebe e devolve tipos da aplicação: nada de ORM, `IQueryable`, cursor ou SQL na porta.
- "Não encontrado" é erro de negócio (ou uma operação que pergunta se existe), nunca `None`/`null` como resposta.
- O fake em memória fica num módulo compartilhado dos testes. A mesma suíte de contrato roda contra o fake (teste unitário) e contra a implementação real (integração, `qa-integration`): é o que garante que o fake não mente.
- A implementação real segue a skill de dados (`data-relational`, `data-nosql`) e mora em infrastructure.
- Regras do time: `clean-architecture` (porta mínima, sem `Repository<T>`).

## Python
```python
# pedidos.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


class PedidoNaoEncontrado(Exception):
    """Erro de negócio: não há pedido com esse id."""


@dataclass(frozen=True)
class Pedido:
    id: str
    cliente_id: str
    total: Decimal


class PedidoRepository(Protocol):
    """Porta: só as operações que os casos de uso usam."""

    def obter(self, pedido_id: str) -> Pedido: ...

    def salvar(self, pedido: Pedido) -> None: ...

    def do_cliente(self, cliente_id: str) -> list[Pedido]: ...
```

## .NET
```csharp
public sealed class PedidoNaoEncontradoException(string pedidoId)
    : Exception($"Pedido não encontrado: {pedidoId}");

public sealed record Pedido(string Id, string ClienteId, decimal Total);

// Porta: só as operações que os casos de uso usam.
public interface IPedidoRepository
{
    Task<Pedido> ObterAsync(string pedidoId, CancellationToken cancellationToken);

    Task SalvarAsync(Pedido pedido, CancellationToken cancellationToken);

    Task<IReadOnlyList<Pedido>> DoClienteAsync(string clienteId, CancellationToken cancellationToken);
}
```

## Como testar
- O fake e a suíte de contrato, parametrizada pelas implementações: aqui só o fake; no teste de integração, a implementação real entra na mesma lista.
- Os casos de uso usam o fake, nunca a implementação real.

```python
# test_pedidos.py
from decimal import Decimal

import pytest

from pedidos import Pedido, PedidoNaoEncontrado, PedidoRepository


class PedidoRepositoryEmMemoria:
    """Fake para testes unitários; passa no mesmo contrato da implementação real."""

    def __init__(self) -> None:
        self._por_id: dict[str, Pedido] = {}

    def obter(self, pedido_id: str) -> Pedido:
        if pedido_id not in self._por_id:
            raise PedidoNaoEncontrado(pedido_id)
        return self._por_id[pedido_id]

    def salvar(self, pedido: Pedido) -> None:
        self._por_id[pedido.id] = pedido

    def do_cliente(self, cliente_id: str) -> list[Pedido]:
        return [
            pedido
            for pedido in self._por_id.values()
            if pedido.cliente_id == cliente_id
        ]


# Contrato: a mesma lista de testes roda contra o fake (aqui) e contra a
# implementação real (no teste de integração, acrescentando-a em params).
@pytest.fixture(params=[PedidoRepositoryEmMemoria], ids=["em_memoria"])
def repositorio(request: pytest.FixtureRequest) -> PedidoRepository:
    return request.param()


def test_salvar_e_obter_devolve_o_mesmo_pedido(repositorio: PedidoRepository) -> None:
    pedido = Pedido("p-1", "c-1", Decimal(10))
    repositorio.salvar(pedido)
    assert repositorio.obter("p-1") == pedido


def test_salvar_de_novo_substitui_o_pedido(repositorio: PedidoRepository) -> None:
    repositorio.salvar(Pedido("p-1", "c-1", Decimal(10)))
    repositorio.salvar(Pedido("p-1", "c-1", Decimal(20)))
    assert repositorio.obter("p-1").total == Decimal(20)


def test_obter_inexistente_lanca_erro(repositorio: PedidoRepository) -> None:
    with pytest.raises(PedidoNaoEncontrado):
        repositorio.obter("p-9")


def test_do_cliente_devolve_so_os_pedidos_dele(repositorio: PedidoRepository) -> None:
    repositorio.salvar(Pedido("p-1", "c-1", Decimal(10)))
    repositorio.salvar(Pedido("p-2", "c-2", Decimal(10)))
    assert [pedido.id for pedido in repositorio.do_cliente("c-1")] == ["p-1"]
```

```csharp
// Fake para testes unitários; passa no mesmo contrato da implementação real.
public sealed class PedidoRepositoryEmMemoria : IPedidoRepository
{
    private readonly Dictionary<string, Pedido> _porId = new();

    public Task<Pedido> ObterAsync(string pedidoId, CancellationToken cancellationToken) =>
        _porId.TryGetValue(pedidoId, out var pedido)
            ? Task.FromResult(pedido)
            : Task.FromException<Pedido>(new PedidoNaoEncontradoException(pedidoId));

    public Task SalvarAsync(Pedido pedido, CancellationToken cancellationToken)
    {
        _porId[pedido.Id] = pedido;
        return Task.CompletedTask;
    }

    public Task<IReadOnlyList<Pedido>> DoClienteAsync(string clienteId, CancellationToken cancellationToken) =>
        Task.FromResult<IReadOnlyList<Pedido>>([.. _porId.Values.Where(pedido => pedido.ClienteId == clienteId)]);
}

// Contrato: os mesmos testes rodam contra o fake (aqui) e contra a implementação
// real (no teste de integração, acrescentando-a em Implementacoes).
public class PedidoRepositoryContratoTests
{
    public static TheoryData<Func<IPedidoRepository>> Implementacoes =>
        new() { () => new PedidoRepositoryEmMemoria() };

    [Theory]
    [MemberData(nameof(Implementacoes))]
    public async Task SalvarEObter_MesmoId_DevolveOMesmoPedido(Func<IPedidoRepository> criar)
    {
        var repositorio = criar();
        var pedido = new Pedido("p-1", "c-1", 10m);

        await repositorio.SalvarAsync(pedido, CancellationToken.None);

        Assert.Equal(pedido, await repositorio.ObterAsync("p-1", CancellationToken.None));
    }

    [Theory]
    [MemberData(nameof(Implementacoes))]
    public async Task Obter_Inexistente_LancaPedidoNaoEncontrado(Func<IPedidoRepository> criar) =>
        await Assert.ThrowsAsync<PedidoNaoEncontradoException>(
            () => criar().ObterAsync("p-9", CancellationToken.None));

    [Theory]
    [MemberData(nameof(Implementacoes))]
    public async Task DoCliente_DoisClientes_DevolveSoOsPedidosDele(Func<IPedidoRepository> criar)
    {
        var repositorio = criar();
        await repositorio.SalvarAsync(new Pedido("p-1", "c-1", 10m), CancellationToken.None);
        await repositorio.SalvarAsync(new Pedido("p-2", "c-2", 10m), CancellationToken.None);

        var doCliente = await repositorio.DoClienteAsync("c-1", CancellationToken.None);

        Assert.Equal(new[] { "p-1" }, doCliente.Select(pedido => pedido.Id));
    }
}
```
