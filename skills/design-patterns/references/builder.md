# Builder

Aplica-se quando um objeto tem muitos campos opcionais, quando uma função passa do limite de parâmetros da `clean-code-solid`, ou quando testes repetem a montagem de um objeto grande.

## Quando não usar
- Poucos campos, todos obrigatórios: construtor.
- Builder fluente clássico (`.com_x().com_y().construir()`) em produção: em Python e C#, argumentos nomeados, valores padrão e objetos imutáveis já resolvem. Use-o só quando a montagem tem passos com validação entre eles que o construtor não consegue expressar.

## Forma
- **Produção — objeto de parâmetros**: os opcionais viram campos com valor padrão de um objeto imutável; a validação entre campos fica na criação (`__post_init__` no Python, construtor no .NET). A função passa a receber esse objeto.
- **Testes — Test Data Builder**: uma função devolve um objeto válido e completo; cada teste altera só o que importa para o cenário (`dataclasses.replace` no Python, `with` no C#). Fica num módulo compartilhado dos testes.

## Python
```python
# relatorio.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class StatusPedido(Enum):
    ABERTO = "aberto"
    PAGO = "pago"
    ENVIADO = "enviado"


class PeriodoInvalido(Exception):
    """Erro de negócio: o início do período é depois do fim."""


@dataclass(frozen=True)
class FiltroRelatorio:
    inicio: date
    fim: date
    cliente_id: str | None = None
    status: StatusPedido | None = None
    valor_minimo: Decimal | None = None

    def __post_init__(self) -> None:
        if self.inicio > self.fim:
            raise PeriodoInvalido(f"{self.inicio} > {self.fim}")


@dataclass(frozen=True)
class Cliente:
    id: str
    nome: str
    email: str
    pais: str
    vip: bool
    limite_credito: Decimal
```
Uso: `FiltroRelatorio(inicio=date(2026, 1, 1), fim=date(2026, 1, 31), status=StatusPedido.PAGO)`.

## .NET
```csharp
public enum StatusPedido { Aberto, Pago, Enviado }

public sealed class PeriodoInvalidoException(DateOnly inicio, DateOnly fim)
    : Exception($"Período inválido: {inicio} a {fim}");

public sealed record FiltroRelatorio
{
    public FiltroRelatorio(DateOnly inicio, DateOnly fim)
    {
        if (inicio > fim)
        {
            throw new PeriodoInvalidoException(inicio, fim);
        }

        Inicio = inicio;
        Fim = fim;
    }

    public DateOnly Inicio { get; }

    public DateOnly Fim { get; }

    public string? ClienteId { get; init; }

    public StatusPedido? Status { get; init; }

    public decimal? ValorMinimo { get; init; }
}

public sealed record Cliente(
    string Id, string Nome, string Email, string Pais, bool Vip, decimal LimiteCredito);
```
Uso: `new FiltroRelatorio(inicio, fim) { Status = StatusPedido.Pago }`. `Inicio` e `Fim` não têm `init`, então um `with` não consegue burlar a validação do período.

## Como testar
- Objeto de parâmetros: a combinação inválida lança o erro de negócio.
- Test Data Builder: os testes usam a função em vez de montar o objeto inteiro; ela muda quando a entidade ganha um campo, e os testes não.

```python
# test_relatorio.py
from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from relatorio import Cliente, FiltroRelatorio, PeriodoInvalido

CLIENTE_PADRAO = Cliente(
    id="c-1",
    nome="Cliente Exemplo",
    email="cliente@exemplo.com",
    pais="BR",
    vip=False,
    limite_credito=Decimal(1000),
)


def um_cliente(**alteracoes: Any) -> Cliente:
    """Test Data Builder: cliente válido; o teste altera só o que importa."""
    return replace(CLIENTE_PADRAO, **alteracoes)


def test_filtro_relatorio_periodo_invertido_lanca_erro() -> None:
    with pytest.raises(PeriodoInvalido):
        FiltroRelatorio(inicio=date(2026, 2, 1), fim=date(2026, 1, 1))


def test_um_cliente_altera_so_o_campo_pedido() -> None:
    cliente = um_cliente(vip=True)
    assert cliente.vip
    assert cliente.limite_credito == CLIENTE_PADRAO.limite_credito
```

```csharp
public static class Construtores
{
    public static Cliente UmCliente() => new(
        Id: "c-1",
        Nome: "Cliente Exemplo",
        Email: "cliente@exemplo.com",
        Pais: "BR",
        Vip: false,
        LimiteCredito: 1000m);
}

public class FiltroRelatorioTests
{
    [Fact]
    public void Construtor_PeriodoInvertido_LancaPeriodoInvalido() =>
        Assert.Throws<PeriodoInvalidoException>(
            () => new FiltroRelatorio(new DateOnly(2026, 2, 1), new DateOnly(2026, 1, 1)));

    [Fact]
    public void UmCliente_ComVip_AlteraSoOCampoPedido()
    {
        var cliente = Construtores.UmCliente() with { Vip = true };

        Assert.True(cliente.Vip);
        Assert.Equal(1000m, cliente.LimiteCredito);
    }
}
```
