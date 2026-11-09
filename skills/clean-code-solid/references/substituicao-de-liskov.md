# Substituição de Liskov (L)

Aplica-se quando uma interface ou classe base tem duas ou mais implementações e uma delas se comporta diferente do combinado: lança "não suportado", exige mais na entrada, garante menos na saída ou sinaliza outro erro.

## Sintomas
- Implementação que lança `NotImplementedError`/`NotSupportedException`, ou deixa vazio um método que deveria agir: a interface está grande demais (`references/segregacao-de-interfaces.md`).
- Quem chama testa o tipo concreto para tratar uma implementação à parte (`isinstance(desconto, DescontoFixo)`, `desconto is DescontoFixo`).
- Implementação que recusa entrada que o contrato aceita (valida mais, tem limite menor): exige mais.
- Implementação que devolve fora do que o contrato garante (negativo, `None`/`null`, lista fora da ordem prometida): garante menos.
- Implementações que sinalizam o mesmo caso com erros diferentes (`KeyError` numa, erro de negócio na outra).
- Subclasse concreta que sobrescreve método da base e muda o resultado: troque por composição ("Classes e módulos", no `SKILL.md`).
- Fake de teste que não falha onde a implementação real falha (suíte de contrato de porta: `design-patterns`, `references/repository.md`).

## Forma
- O contrato fica escrito na interface: o que aceita, o que garante na saída e que erros lança. Sem contrato escrito, não há como conferir a substituição.
- Toda implementação aceita tudo o que o contrato aceita e garante tudo o que ele garante. O caso de borda (abatimento maior que o valor) se resolve dentro da implementação, no limite do contrato.
- A invariante de que a implementação precisa para cumprir o contrato (percentual entre 0 e 100) é conferida na criação, não em cada chamada nem por quem chama.
- Implementação que não consegue cumprir uma operação não implementa aquela interface: divida a interface (`references/segregacao-de-interfaces.md`).

## Python
```python
# descontos.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

CEM_POR_CENTO = Decimal(100)


class Desconto(Protocol):
    """Contrato: aceita qualquer valor maior ou igual a zero e devolve o valor com
    desconto, entre zero e o próprio valor, sem lançar exceção."""

    def aplicar(self, valor: Decimal) -> Decimal: ...


@dataclass(frozen=True)
class DescontoPercentual:
    percentual: Decimal

    def __post_init__(self) -> None:
        # Fora de 0 a 100, aplicar sairia do contrato: a criação barra.
        if not Decimal(0) <= self.percentual <= CEM_POR_CENTO:
            raise ValueError(f"percentual fora de 0 a 100: {self.percentual}")

    def aplicar(self, valor: Decimal) -> Decimal:
        return valor - valor * self.percentual / CEM_POR_CENTO


@dataclass(frozen=True)
class DescontoFixo:
    abatimento: Decimal

    def __post_init__(self) -> None:
        if self.abatimento < 0:
            raise ValueError(f"abatimento negativo: {self.abatimento}")

    def aplicar(self, valor: Decimal) -> Decimal:
        # Abatimento maior que o valor zera o valor: devolver negativo ou lançar erro
        # quebraria o contrato, e quem soma descontos teria de tratar este caso à parte.
        return max(valor - self.abatimento, Decimal(0))
```

## .NET
```csharp
// Contrato: aceita qualquer valor maior ou igual a zero e devolve o valor com desconto,
// entre zero e o próprio valor, sem lançar exceção.
public interface IDesconto
{
    decimal Aplicar(decimal valor);
}

public sealed class DescontoPercentual : IDesconto
{
    private const decimal CemPorCento = 100m;
    private readonly decimal _percentual;

    public DescontoPercentual(decimal percentual)
    {
        // Fora de 0 a 100, Aplicar sairia do contrato: a criação barra.
        ArgumentOutOfRangeException.ThrowIfNegative(percentual);
        ArgumentOutOfRangeException.ThrowIfGreaterThan(percentual, CemPorCento);
        _percentual = percentual;
    }

    public decimal Aplicar(decimal valor) => valor - valor * _percentual / CemPorCento;
}

public sealed class DescontoFixo : IDesconto
{
    private readonly decimal _abatimento;

    public DescontoFixo(decimal abatimento)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(abatimento);
        _abatimento = abatimento;
    }

    // Abatimento maior que o valor zera o valor: devolver negativo ou lançar exceção
    // quebraria o contrato, e quem soma descontos teria de tratar este caso à parte.
    public decimal Aplicar(decimal valor) => Math.Max(valor - _abatimento, 0m);
}
```

## Como testar
- Suíte de contrato: os mesmos testes, parametrizados pelas implementações e por valores de borda, conferem as garantias comuns. Implementação nova entra na lista e tem de passar sem mudar os testes.
- Cada implementação tem também os testes da própria regra.

```python
# test_descontos.py
from decimal import Decimal

import pytest

from descontos import Desconto, DescontoFixo, DescontoPercentual

# Suíte de contrato: toda implementação entra nesta lista e passa nos mesmos testes.
IMPLEMENTACOES: list[Desconto] = [
    DescontoPercentual(Decimal(0)),
    DescontoPercentual(Decimal(100)),
    DescontoFixo(Decimal(15)),
]
VALORES_DE_BORDA = [Decimal(0), Decimal("0.01"), Decimal(15), Decimal(1000)]


@pytest.mark.parametrize("desconto", IMPLEMENTACOES, ids=repr)
@pytest.mark.parametrize("valor", VALORES_DE_BORDA, ids=str)
def test_aplicar_qualquer_valor_devolve_entre_zero_e_o_valor(
    desconto: Desconto, valor: Decimal
) -> None:
    assert Decimal(0) <= desconto.aplicar(valor) <= valor


def test_aplicar_abatimento_maior_que_o_valor_devolve_zero() -> None:
    assert DescontoFixo(Decimal(15)).aplicar(Decimal(10)) == Decimal(0)


def test_desconto_percentual_acima_de_cem_lanca_erro() -> None:
    with pytest.raises(ValueError, match="percentual"):
        DescontoPercentual(Decimal(150))
```

```csharp
// Suíte de contrato: toda implementação entra em Implementacoes e passa nos mesmos testes.
public class DescontoContratoTests
{
    private static readonly IDesconto[] Implementacoes =
        [new DescontoPercentual(0m), new DescontoPercentual(100m), new DescontoFixo(15m)];

    private static readonly decimal[] ValoresDeBorda = [0m, 0.01m, 15m, 1_000m];

    public static TheoryData<IDesconto, decimal> Casos()
    {
        var casos = new TheoryData<IDesconto, decimal>();
        foreach (var desconto in Implementacoes)
        {
            foreach (var valor in ValoresDeBorda)
            {
                casos.Add(desconto, valor);
            }
        }

        return casos;
    }

    [Theory]
    [MemberData(nameof(Casos))]
    public void Aplicar_QualquerValor_DevolveEntreZeroEOValor(IDesconto desconto, decimal valor) =>
        Assert.InRange(desconto.Aplicar(valor), 0m, valor);
}

public class DescontoTests
{
    [Fact]
    public void Aplicar_AbatimentoMaiorQueOValor_DevolveZero() =>
        Assert.Equal(0m, new DescontoFixo(15m).Aplicar(10m));

    [Fact]
    public void DescontoPercentual_AcimaDeCem_LancaArgumentOutOfRange() =>
        Assert.Throws<ArgumentOutOfRangeException>(() => new DescontoPercentual(150m));
}
```
