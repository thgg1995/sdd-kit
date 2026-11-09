# Strategy

Aplica-se quando o plano lista duas ou mais variações de um comportamento, cada uma com regra própria, ou quando o mesmo critério (`if tipo == ...`) decide o comportamento em dois ou mais lugares do código.

## Quando não usar
- Uma variação só, ou duas decididas num único lugar: mantenha o `if`.
- A variação é só de valor (taxa, prazo, limite): use uma tabela de valores por chave, não uma classe por variação.
- A variação é fixa por instalação (vem da configuração): o composition root escolhe a implementação, sem registro nem escolha a cada chamada.

## Forma
- Uma interface com as operações que variam juntas; uma implementação por variação, cada uma com a sua regra.
- Um registro por chave escolhe a implementação pelo dado da chamada; chave desconhecida é erro de negócio.
- Uma operação só e sem estado: a estratégia pode ser uma função, e o registro, um dicionário de funções.
- Interface, implementações e registro ficam em application: são regra, sem I/O.

## Python
```python
# frete.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class Pedido:
    valor: Decimal
    peso_kg: Decimal


class ModalidadeDesconhecida(Exception):
    """Erro de negócio: a modalidade pedida não existe."""


class Modalidade(Protocol):
    def frete(self, pedido: Pedido) -> Decimal: ...

    def prazo_em_dias(self) -> int: ...


class Normal:
    TARIFA_POR_KG = Decimal("1.20")
    VALOR_FRETE_GRATIS = Decimal(200)
    PRAZO_EM_DIAS = 5

    def frete(self, pedido: Pedido) -> Decimal:
        if pedido.valor >= self.VALOR_FRETE_GRATIS:
            return Decimal(0)
        return pedido.peso_kg * self.TARIFA_POR_KG

    def prazo_em_dias(self) -> int:
        return self.PRAZO_EM_DIAS


class Expressa:
    TARIFA_POR_KG = Decimal("2.50")
    FRETE_MINIMO = Decimal(15)
    PRAZO_EM_DIAS = 1

    def frete(self, pedido: Pedido) -> Decimal:
        return max(self.FRETE_MINIMO, pedido.peso_kg * self.TARIFA_POR_KG)

    def prazo_em_dias(self) -> int:
        return self.PRAZO_EM_DIAS


class Retirada:
    def frete(self, pedido: Pedido) -> Decimal:
        return Decimal(0)

    def prazo_em_dias(self) -> int:
        return 0


MODALIDADES: dict[str, Modalidade] = {
    "normal": Normal(),
    "expressa": Expressa(),
    "retirada": Retirada(),
}


def obter_modalidade(nome: str) -> Modalidade:
    if nome not in MODALIDADES:
        raise ModalidadeDesconhecida(nome)
    return MODALIDADES[nome]
```

## .NET
```csharp
public sealed record Pedido(decimal Valor, decimal PesoKg);

public sealed class ModalidadeDesconhecidaException(string nome)
    : Exception($"Modalidade desconhecida: {nome}");

public interface IModalidade
{
    string Nome { get; }

    decimal Frete(Pedido pedido);

    int PrazoEmDias();
}

public sealed class Normal : IModalidade
{
    private const decimal TarifaPorKg = 1.20m;
    private const decimal ValorFreteGratis = 200m;
    private const int Prazo = 5;

    public string Nome => "normal";

    public decimal Frete(Pedido pedido) =>
        pedido.Valor >= ValorFreteGratis ? 0m : pedido.PesoKg * TarifaPorKg;

    public int PrazoEmDias() => Prazo;
}

public sealed class Expressa : IModalidade
{
    private const decimal TarifaPorKg = 2.50m;
    private const decimal FreteMinimo = 15m;
    private const int Prazo = 1;

    public string Nome => "expressa";

    public decimal Frete(Pedido pedido) => Math.Max(FreteMinimo, pedido.PesoKg * TarifaPorKg);

    public int PrazoEmDias() => Prazo;
}

public sealed class Retirada : IModalidade
{
    public string Nome => "retirada";

    public decimal Frete(Pedido pedido) => 0m;

    public int PrazoEmDias() => 0;
}

public sealed class Modalidades(IEnumerable<IModalidade> todas)
{
    private readonly Dictionary<string, IModalidade> _porNome =
        todas.ToDictionary(modalidade => modalidade.Nome);

    public IModalidade Obter(string nome) =>
        _porNome.TryGetValue(nome, out var modalidade)
            ? modalidade
            : throw new ModalidadeDesconhecidaException(nome);
}
```

```csharp
// composition root (Program.cs, em builder.Services)
services.AddSingleton<IModalidade, Normal>();
services.AddSingleton<IModalidade, Expressa>();
services.AddSingleton<IModalidade, Retirada>();
services.AddSingleton<Modalidades>();
```

## Como testar
- Cada estratégia direto, sem o registro: um teste por regra dela.
- O registro: chave desconhecida lança o erro de negócio.
- O caso de uso que usa a estratégia: um fake da interface, sem estratégia real.

```python
# test_frete.py
from decimal import Decimal

import pytest

from frete import Expressa, ModalidadeDesconhecida, Normal, Pedido, obter_modalidade


def test_frete_expressa_abaixo_do_minimo_cobra_o_minimo() -> None:
    pedido = Pedido(valor=Decimal(50), peso_kg=Decimal(2))
    assert Expressa().frete(pedido) == Decimal(15)


def test_frete_normal_acima_do_valor_de_frete_gratis_nao_cobra() -> None:
    pedido = Pedido(valor=Decimal(250), peso_kg=Decimal(10))
    assert Normal().frete(pedido) == Decimal(0)


def test_obter_modalidade_nome_desconhecido_lanca_erro() -> None:
    with pytest.raises(ModalidadeDesconhecida):
        obter_modalidade("drone")
```

```csharp
public class ModalidadesTests
{
    [Fact]
    public void Frete_ExpressaAbaixoDoMinimo_CobraOMinimo() =>
        Assert.Equal(15m, new Expressa().Frete(new Pedido(Valor: 50m, PesoKg: 2m)));

    [Fact]
    public void Frete_NormalAcimaDoValorDeFreteGratis_NaoCobra() =>
        Assert.Equal(0m, new Normal().Frete(new Pedido(Valor: 250m, PesoKg: 10m)));

    [Fact]
    public void Obter_NomeDesconhecido_LancaModalidadeDesconhecida() =>
        Assert.Throws<ModalidadeDesconhecidaException>(
            () => new Modalidades([new Normal(), new Expressa()]).Obter("drone"));
}
```
