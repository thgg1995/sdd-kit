# State

Aplica-se quando uma entidade tem três ou mais estados com regras de transição (de onde pode ir para onde), ou quando transições são validadas por `if status == ...` em vários casos de uso.

## Quando não usar
- Dois estados e uma transição: um booleano ou um enum simples basta.
- Estado só informativo, sem regra de transição: campo comum.

## Forma
- Tabela de transições: enum dos estados e um dicionário "estado → estados permitidos". A entidade expõe um método por ação (`autorizar()`, `estornar()`), que consulta a tabela e lança erro de negócio na transição inválida.
- Objeto por estado (o State clássico): só quando, além das transições, o comportamento muda por estado (ex.: o valor do estorno depende do estado). A tabela continua decidindo as transições.
- O status não tem setter público. Carregar do banco usa um método de fábrica (`restaurar(id, status)`), chamado só pelo adaptador de persistência.
- A entidade fica em domain. Regras do time: `clean-architecture` (`references/dominio-rico.md`).

## Python
```python
# pagamento.py
from enum import Enum


class StatusPagamento(Enum):
    PENDENTE = "pendente"
    AUTORIZADO = "autorizado"
    CAPTURADO = "capturado"
    ESTORNADO = "estornado"
    CANCELADO = "cancelado"


TRANSICOES: dict[StatusPagamento, frozenset[StatusPagamento]] = {
    StatusPagamento.PENDENTE: frozenset(
        {StatusPagamento.AUTORIZADO, StatusPagamento.CANCELADO}
    ),
    StatusPagamento.AUTORIZADO: frozenset(
        {StatusPagamento.CAPTURADO, StatusPagamento.CANCELADO}
    ),
    StatusPagamento.CAPTURADO: frozenset({StatusPagamento.ESTORNADO}),
    StatusPagamento.ESTORNADO: frozenset(),
    StatusPagamento.CANCELADO: frozenset(),
}


class TransicaoInvalida(Exception):
    """Erro de negócio: a ação não é permitida no estado atual."""

    def __init__(self, atual: StatusPagamento, destino: StatusPagamento) -> None:
        super().__init__(f"{atual.value} -> {destino.value}")
        self.atual = atual
        self.destino = destino


class Pagamento:
    def __init__(self, pagamento_id: str) -> None:
        self.id = pagamento_id
        self._status = StatusPagamento.PENDENTE

    @classmethod
    def restaurar(cls, pagamento_id: str, status: StatusPagamento) -> "Pagamento":
        pagamento = cls(pagamento_id)
        pagamento._status = status
        return pagamento

    @property
    def status(self) -> StatusPagamento:
        return self._status

    def autorizar(self) -> None:
        self._transitar(StatusPagamento.AUTORIZADO)

    def capturar(self) -> None:
        self._transitar(StatusPagamento.CAPTURADO)

    def estornar(self) -> None:
        self._transitar(StatusPagamento.ESTORNADO)

    def cancelar(self) -> None:
        self._transitar(StatusPagamento.CANCELADO)

    def _transitar(self, destino: StatusPagamento) -> None:
        if destino not in TRANSICOES[self._status]:
            raise TransicaoInvalida(self._status, destino)
        self._status = destino
```

## .NET
```csharp
public enum StatusPagamento { Pendente, Autorizado, Capturado, Estornado, Cancelado }

public sealed class TransicaoInvalidaException(StatusPagamento atual, StatusPagamento destino)
    : Exception($"{atual} -> {destino}")
{
    public StatusPagamento Atual { get; } = atual;

    public StatusPagamento Destino { get; } = destino;
}

public sealed class Pagamento
{
    private static readonly Dictionary<StatusPagamento, StatusPagamento[]> Transicoes = new()
    {
        [StatusPagamento.Pendente] = [StatusPagamento.Autorizado, StatusPagamento.Cancelado],
        [StatusPagamento.Autorizado] = [StatusPagamento.Capturado, StatusPagamento.Cancelado],
        [StatusPagamento.Capturado] = [StatusPagamento.Estornado],
        [StatusPagamento.Estornado] = [],
        [StatusPagamento.Cancelado] = [],
    };

    public Pagamento(string id) => Id = id;

    public string Id { get; }

    public StatusPagamento Status { get; private set; } = StatusPagamento.Pendente;

    public static Pagamento Restaurar(string id, StatusPagamento status) =>
        new(id) { Status = status };

    public void Autorizar() => Transitar(StatusPagamento.Autorizado);

    public void Capturar() => Transitar(StatusPagamento.Capturado);

    public void Estornar() => Transitar(StatusPagamento.Estornado);

    public void Cancelar() => Transitar(StatusPagamento.Cancelado);

    private void Transitar(StatusPagamento destino)
    {
        if (!Transicoes[Status].Contains(destino))
        {
            throw new TransicaoInvalidaException(Status, destino);
        }

        Status = destino;
    }
}
```

## Como testar
- Uma transição permitida por teste e as proibidas relevantes, parametrizadas pelos estados de origem.
- O caso de uso: carrega a entidade por um fake da porta, chama a ação e confere o status salvo; transição inválida chega como erro de negócio ao adaptador de entrada.

```python
# test_pagamento.py
import pytest

from pagamento import Pagamento, StatusPagamento, TransicaoInvalida


def test_capturar_pagamento_autorizado_fica_capturado() -> None:
    pagamento = Pagamento.restaurar("p-1", StatusPagamento.AUTORIZADO)
    pagamento.capturar()
    assert pagamento.status is StatusPagamento.CAPTURADO


@pytest.mark.parametrize(
    "status",
    [StatusPagamento.PENDENTE, StatusPagamento.AUTORIZADO, StatusPagamento.CANCELADO],
)
def test_estornar_sem_captura_lanca_transicao_invalida(status: StatusPagamento) -> None:
    pagamento = Pagamento.restaurar("p-1", status)
    with pytest.raises(TransicaoInvalida):
        pagamento.estornar()
```

```csharp
public class PagamentoTests
{
    [Fact]
    public void Capturar_PagamentoAutorizado_FicaCapturado()
    {
        var pagamento = Pagamento.Restaurar("p-1", StatusPagamento.Autorizado);

        pagamento.Capturar();

        Assert.Equal(StatusPagamento.Capturado, pagamento.Status);
    }

    [Theory]
    [InlineData(StatusPagamento.Pendente)]
    [InlineData(StatusPagamento.Autorizado)]
    [InlineData(StatusPagamento.Cancelado)]
    public void Estornar_SemCaptura_LancaTransicaoInvalida(StatusPagamento status) =>
        Assert.Throws<TransicaoInvalidaException>(
            () => Pagamento.Restaurar("p-1", status).Estornar());
}
```
