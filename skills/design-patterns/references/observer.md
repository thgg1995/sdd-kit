# Observer

Aplica-se quando, depois de uma mudança, outras partes precisam reagir (ex.: pagamento confirmado → emitir nota, pontuar fidelidade) e o caso de uso cresce chamando cada uma delas, ou a lista de reações muda de uma instalação para outra.

## Quando não usar
- Reação em outro serviço, ou que pode falhar sem desfazer a operação: evento de integração, publicado pelo producer (`clean-architecture`, `kafka-messaging`), fora do processo.
- Barramento em memória com registro global de assinantes: proibido sem decisão registrada (`clean-architecture`).
- Uma reação só: chamada direta no caso de uso.

## Forma
- Reação no mesmo processo e na mesma transação: o caso de uso recebe a lista de observadores pela interface e notifica cada um depois da mudança. Sem registro global e sem barramento.
- O composition root monta a lista; a ordem da lista é a ordem de execução. No .NET, cada observador é registrado no container com a mesma interface (`AddScoped<IAoConfirmarPagamento, EmitirNotaFiscal>()`), e o caso de uso recebe `IEnumerable<IAoConfirmarPagamento>`.
- Observador que falha derruba a operação inteira (mesma transação). Por isso só entra aqui a reação que precisa ser atômica com a mudança; o resto vira evento de integração.
- A interface do observador fica em application; cada observador é um caso de uso pequeno ou um adaptador.

## Python
```python
# pagamento_confirmado.py
from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class PagamentoConfirmado:
    pedido_id: str
    valor: Decimal


class AoConfirmarPagamento(Protocol):
    """Observador: uma reação no mesmo processo e na mesma transação."""

    def reagir(self, evento: PagamentoConfirmado) -> None: ...


class Pagamentos(Protocol):
    def marcar_como_pago(self, pedido_id: str) -> None: ...


class ConfirmarPagamento:
    def __init__(
        self, pagamentos: Pagamentos, observadores: Sequence[AoConfirmarPagamento]
    ) -> None:
        self._pagamentos = pagamentos
        self._observadores = tuple(observadores)

    def executar(self, pedido_id: str, valor: Decimal) -> None:
        self._pagamentos.marcar_como_pago(pedido_id)
        evento = PagamentoConfirmado(pedido_id, valor)
        for observador in self._observadores:
            observador.reagir(evento)
```

## .NET
```csharp
public sealed record PagamentoConfirmado(string PedidoId, decimal Valor);

// Observador: uma reação no mesmo processo e na mesma transação.
public interface IAoConfirmarPagamento
{
    Task ReagirAsync(PagamentoConfirmado evento, CancellationToken cancellationToken);
}

public interface IPagamentos
{
    Task MarcarComoPagoAsync(string pedidoId, CancellationToken cancellationToken);
}

public sealed class ConfirmarPagamento(IPagamentos pagamentos, IEnumerable<IAoConfirmarPagamento> observadores)
{
    public async Task ExecutarAsync(string pedidoId, decimal valor, CancellationToken cancellationToken)
    {
        await pagamentos.MarcarComoPagoAsync(pedidoId, cancellationToken);
        var evento = new PagamentoConfirmado(pedidoId, valor);
        foreach (var observador in observadores)
        {
            await observador.ReagirAsync(evento, cancellationToken);
        }
    }
}
```

## Como testar
- Com observadores fake: todos recebem o evento, na ordem da lista.
- Falha na mudança: nenhum observador é notificado.
- Cada observador real é testado sozinho, com o evento como entrada.

```python
# test_pagamento_confirmado.py
from decimal import Decimal

import pytest

from pagamento_confirmado import ConfirmarPagamento, PagamentoConfirmado


class Recusa(Exception):
    pass


class PagamentosFake:
    def __init__(self, falha: Exception | None = None) -> None:
        self._falha = falha

    def marcar_como_pago(self, pedido_id: str) -> None:
        if self._falha is not None:
            raise self._falha


class ObservadorFake:
    def __init__(self, nome: str, notificados: list[str]) -> None:
        self._nome = nome
        self._notificados = notificados

    def reagir(self, evento: PagamentoConfirmado) -> None:
        self._notificados.append(f"{self._nome}:{evento.pedido_id}")


def test_executar_notifica_os_observadores_na_ordem() -> None:
    notificados: list[str] = []
    observadores = [
        ObservadorFake("nota", notificados),
        ObservadorFake("pontos", notificados),
    ]
    ConfirmarPagamento(PagamentosFake(), observadores).executar("p-1", Decimal(10))
    assert notificados == ["nota:p-1", "pontos:p-1"]


def test_executar_com_falha_na_mudanca_nao_notifica() -> None:
    notificados: list[str] = []
    caso_de_uso = ConfirmarPagamento(
        PagamentosFake(falha=Recusa()), [ObservadorFake("nota", notificados)]
    )
    with pytest.raises(Recusa):
        caso_de_uso.executar("p-1", Decimal(10))
    assert notificados == []
```

```csharp
public class ConfirmarPagamentoTests
{
    private sealed class PagamentosFake(Exception? falha = null) : IPagamentos
    {
        public Task MarcarComoPagoAsync(string pedidoId, CancellationToken cancellationToken) =>
            falha is null ? Task.CompletedTask : Task.FromException(falha);
    }

    private sealed class ObservadorFake(string nome, List<string> notificados) : IAoConfirmarPagamento
    {
        public Task ReagirAsync(PagamentoConfirmado evento, CancellationToken cancellationToken)
        {
            notificados.Add($"{nome}:{evento.PedidoId}");
            return Task.CompletedTask;
        }
    }

    [Fact]
    public async Task ExecutarAsync_DoisObservadores_NotificaNaOrdem()
    {
        var notificados = new List<string>();
        var observadores = new[] { new ObservadorFake("nota", notificados), new ObservadorFake("pontos", notificados) };

        await new ConfirmarPagamento(new PagamentosFake(), observadores)
            .ExecutarAsync("p-1", 10m, CancellationToken.None);

        Assert.Equal(new[] { "nota:p-1", "pontos:p-1" }, notificados);
    }

    [Fact]
    public async Task ExecutarAsync_FalhaNaMudanca_NaoNotifica()
    {
        var notificados = new List<string>();
        var casoDeUso = new ConfirmarPagamento(
            new PagamentosFake(new InvalidOperationException("recusado")),
            [new ObservadorFake("nota", notificados)]);

        await Assert.ThrowsAsync<InvalidOperationException>(
            () => casoDeUso.ExecutarAsync("p-1", 10m, CancellationToken.None));

        Assert.Empty(notificados);
    }
}
```
