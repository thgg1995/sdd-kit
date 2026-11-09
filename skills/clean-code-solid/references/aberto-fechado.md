# Aberto/fechado (O)

Aplica-se quando acrescentar uma variação (tipo, regra, canal) exige editar o código das variações existentes, ou quando se cogita um ponto de extensão.

## Sintomas
Variação nova tem de ser código novo. A forma depende do sintoma; as que são padrão de projeto estão na `design-patterns`:

| No código | Forma |
|---|---|
| o mesmo critério (`if tipo == ...`) decide o comportamento em dois ou mais lugares | Strategy (`references/strategy.md`) |
| a variação é só de valor (taxa, prazo, limite) | tabela por chave (`references/strategy.md`, "Quando não usar") |
| três ou mais verificações independentes, cada uma com motivo próprio, numa função que ganha um `if` a cada regra nova (risco, elegibilidade, validação de cadastro) | lista de regras (abaixo) |
| cache, log, métrica ou retentativa copiados em cada implementação | Decorator (`references/decorator.md`) |
| o caso de uso cresce chamando cada parte que reage a uma mudança | Observer (`references/observer.md`) |

## Quando não aplicar
- Menos de duas variações reais, ou variação que ainda não existe: sem ponto de extensão (linha O da tabela SOLID e "Simplicidade", no `SKILL.md`).
- Até duas verificações, ou verificações que sempre mudam juntas: uma função com os `if`s.
- Conjunto fechado e estável de tipos, em que um tipo novo deve obrigar a rever cada decisão: `match` exaustivo, sem ponto de extensão (`design-patterns`, `references/visitor.md`).

## Forma: lista de regras
- Cada regra é independente: recebe o dado e diz se disparou, com o motivo; não chama outra regra nem depende da ordem. Se a ordem importa ou uma regra interrompe as seguintes, a forma é cadeia (`design-patterns`, `references/chain-of-responsibility.md`).
- O avaliador percorre todas e junta os motivos, sem conhecer nenhuma regra pelo nome.
- Regra nova é uma função (ou classe) nova e uma linha no registro. O avaliador e as regras existentes não mudam: no review, o diff de uma regra nova só tem código novo e essa linha.
- Regra que consulta I/O (ex.: lista de bloqueio) recebe a porta pelo construtor, e o registro passa para o composition root (`references/inversao-de-dependencia.md`).

## Python
```python
# risco.py
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal

VALOR_ALTO = Decimal(5000)
PAIS_DE_ORIGEM = "BR"
QUANTIDADE_MAXIMA = 20


@dataclass(frozen=True)
class Pedido:
    valor: Decimal
    pais_de_entrega: str
    cliente_novo: bool
    quantidade_de_itens: int


@dataclass(frozen=True)
class Regra:
    motivo: str
    dispara: Callable[[Pedido], bool]


def valor_alto_de_cliente_novo(pedido: Pedido) -> bool:
    return pedido.cliente_novo and pedido.valor >= VALOR_ALTO


def entrega_fora_do_pais(pedido: Pedido) -> bool:
    return pedido.pais_de_entrega != PAIS_DE_ORIGEM


def quantidade_acima_do_limite(pedido: Pedido) -> bool:
    return pedido.quantidade_de_itens > QUANTIDADE_MAXIMA


# Registro: regra nova é uma função nova e uma linha aqui.
REGRAS = (
    Regra("valor alto de cliente novo", valor_alto_de_cliente_novo),
    Regra("entrega fora do país", entrega_fora_do_pais),
    Regra("quantidade acima do limite", quantidade_acima_do_limite),
)


def avaliar_risco(pedido: Pedido, regras: Sequence[Regra] = REGRAS) -> list[str]:
    return [regra.motivo for regra in regras if regra.dispara(pedido)]
```

## .NET
```csharp
public sealed record Pedido(decimal Valor, string PaisDeEntrega, bool ClienteNovo, int QuantidadeDeItens);

public interface IRegraDeRisco
{
    string Motivo { get; }

    bool Dispara(Pedido pedido);
}

public sealed class ValorAltoDeClienteNovo : IRegraDeRisco
{
    private const decimal ValorAlto = 5000m;

    public string Motivo => "valor alto de cliente novo";

    public bool Dispara(Pedido pedido) => pedido.ClienteNovo && pedido.Valor >= ValorAlto;
}

public sealed class EntregaForaDoPais : IRegraDeRisco
{
    private const string PaisDeOrigem = "BR";

    public string Motivo => "entrega fora do país";

    public bool Dispara(Pedido pedido) => pedido.PaisDeEntrega != PaisDeOrigem;
}

public sealed class QuantidadeAcimaDoLimite : IRegraDeRisco
{
    private const int QuantidadeMaxima = 20;

    public string Motivo => "quantidade acima do limite";

    public bool Dispara(Pedido pedido) => pedido.QuantidadeDeItens > QuantidadeMaxima;
}

// Não conhece nenhuma regra: recebe todas as registradas.
public sealed class AvaliacaoDeRisco(IEnumerable<IRegraDeRisco> regras)
{
    public IReadOnlyList<string> Motivos(Pedido pedido) =>
        [.. regras.Where(regra => regra.Dispara(pedido)).Select(regra => regra.Motivo)];
}
```

```csharp
// composition root (Program.cs, em builder.Services): regra nova é uma classe nova e uma linha aqui
services.AddSingleton<IRegraDeRisco, ValorAltoDeClienteNovo>();
services.AddSingleton<IRegraDeRisco, EntregaForaDoPais>();
services.AddSingleton<IRegraDeRisco, QuantidadeAcimaDoLimite>();
services.AddSingleton<AvaliacaoDeRisco>();
```

## Como testar
- Cada regra sozinha, no limite: um caso que dispara e um que não dispara.
- O avaliador com as regras reais num cenário que dispara mais de uma, ou com regras de teste (sempre dispara).
- Regra nova traz os próprios testes; os testes existentes não mudam.

```python
# test_risco.py
from dataclasses import replace
from decimal import Decimal

from risco import (
    Pedido,
    Regra,
    avaliar_risco,
    entrega_fora_do_pais,
    valor_alto_de_cliente_novo,
)

SEM_RISCO = Pedido(
    valor=Decimal(100), pais_de_entrega="BR", cliente_novo=False, quantidade_de_itens=1
)


def test_valor_alto_de_cliente_novo_cliente_antigo_nao_dispara() -> None:
    assert not valor_alto_de_cliente_novo(replace(SEM_RISCO, valor=Decimal(9000)))


def test_valor_alto_de_cliente_novo_no_limite_dispara() -> None:
    assert valor_alto_de_cliente_novo(
        replace(SEM_RISCO, valor=Decimal(5000), cliente_novo=True)
    )


def test_entrega_fora_do_pais_entrega_no_pais_nao_dispara() -> None:
    assert not entrega_fora_do_pais(SEM_RISCO)


def test_avaliar_risco_duas_regras_disparadas_devolve_os_dois_motivos() -> None:
    pedido = replace(SEM_RISCO, pais_de_entrega="PT", quantidade_de_itens=21)
    assert avaliar_risco(pedido) == [
        "entrega fora do país",
        "quantidade acima do limite",
    ]


def test_avaliar_risco_regras_de_teste_usa_so_elas() -> None:
    sempre = Regra("sempre", lambda _pedido: True)
    assert avaliar_risco(SEM_RISCO, [sempre]) == ["sempre"]
```

```csharp
public class AvaliacaoDeRiscoTests
{
    private static readonly Pedido SemRisco =
        new(Valor: 100m, PaisDeEntrega: "BR", ClienteNovo: false, QuantidadeDeItens: 1);

    [Fact]
    public void Dispara_ValorAltoDeClienteAntigo_NaoDispara() =>
        Assert.False(new ValorAltoDeClienteNovo().Dispara(SemRisco with { Valor = 9_000m }));

    [Fact]
    public void Dispara_ValorNoLimiteDeClienteNovo_Dispara() =>
        Assert.True(new ValorAltoDeClienteNovo().Dispara(SemRisco with { Valor = 5_000m, ClienteNovo = true }));

    [Fact]
    public void Motivos_DuasRegrasDisparadas_DevolveOsDoisMotivos()
    {
        var avaliacao = new AvaliacaoDeRisco(
            [new ValorAltoDeClienteNovo(), new EntregaForaDoPais(), new QuantidadeAcimaDoLimite()]);

        var motivos = avaliacao.Motivos(SemRisco with { PaisDeEntrega = "PT", QuantidadeDeItens = 21 });

        Assert.Equal(new[] { "entrega fora do país", "quantidade acima do limite" }, motivos);
    }
}
```
