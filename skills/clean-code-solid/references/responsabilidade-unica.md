# Responsabilidade única (S)

Aplica-se quando uma classe ou módulo junta assuntos que mudam por motivos diferentes: regra de negócio, formato de arquivo ou de contrato, acesso a I/O.

## Sintomas
- As mudanças vêm de atores diferentes (ex.: a política de comissão é do comercial; o layout do arquivo, do financeiro), e os dois mexem na mesma classe.
- O módulo importa ferramentas de assuntos diferentes: biblioteca de formato (`csv`, serializador) junto da regra de cálculo, ou driver de banco junto da formatação.
- Métodos que usam grupos separados de campos (coesão, em "Classes e módulos" do `SKILL.md`).
- O teste da regra precisa ler o arquivo gerado, montar o formato ou simular I/O para conferir um cálculo.
- O histórico do arquivo (`git log`) mostra mudanças por motivos que nada têm a ver um com o outro.

## Quando não aplicar
- Partes que sempre mudam juntas, pelo mesmo motivo, ficam juntas, mesmo que sejam dois passos (ex.: o cálculo e o arredondamento do mesmo cálculo).
- A unidade é o motivo de mudança, não o tamanho: não quebre uma função coesa em classes de um método só, nem crie classe que só repassa a chamada (proibido na `clean-architecture`).

## Forma
- Um módulo (ou classe) por motivo, com o nome do assunto: `comissoes` (regra), `exportacao_de_comissoes` (layout do arquivo).
- Regra em código puro, sem formato nem I/O; o formato fica em outro módulo, que recebe o resultado da regra; o I/O fica no adaptador (`clean-architecture`).
- O caso de uso orquestra: chama a regra, passa o resultado ao formato e entrega o texto à porta de envio, sem fazer o trabalho de nenhum deles.

## Python
```python
# comissoes.py
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

# Motivo para mudar: a política de comissão do comercial.
META_MENSAL = Decimal(50000)
TAXA_ATE_A_META = Decimal("0.05")
TAXA_ACIMA_DA_META = Decimal("0.08")


@dataclass(frozen=True)
class Venda:
    vendedor_id: str
    valor: Decimal


@dataclass(frozen=True)
class Comissao:
    vendedor_id: str
    total_vendido: Decimal
    valor: Decimal


def calcular_comissoes(vendas: Iterable[Venda]) -> list[Comissao]:
    totais: dict[str, Decimal] = {}
    for venda in vendas:
        totais[venda.vendedor_id] = (
            totais.get(venda.vendedor_id, Decimal(0)) + venda.valor
        )
    return [
        Comissao(vendedor_id, total, _comissao(total))
        for vendedor_id, total in sorted(totais.items())
    ]


def _comissao(total_vendido: Decimal) -> Decimal:
    ate_a_meta = min(total_vendido, META_MENSAL) * TAXA_ATE_A_META
    acima_da_meta = max(total_vendido - META_MENSAL, Decimal(0)) * TAXA_ACIMA_DA_META
    return ate_a_meta + acima_da_meta
```

```python
# exportacao_de_comissoes.py
import csv
import io
from collections.abc import Iterable
from decimal import Decimal

from comissoes import Comissao

# Motivo para mudar: o layout do arquivo que o financeiro importa.
COLUNAS = ("vendedor", "total_vendido", "comissao")


def comissoes_em_csv(comissoes: Iterable[Comissao]) -> str:
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";", lineterminator="\n")
    escritor.writerow(COLUNAS)
    escritor.writerows(
        (
            comissao.vendedor_id,
            _com_virgula(comissao.total_vendido),
            _com_virgula(comissao.valor),
        )
        for comissao in comissoes
    )
    return saida.getvalue()


def _com_virgula(valor: Decimal) -> str:
    return f"{valor:.2f}".replace(".", ",")
```

## .NET
```csharp
public sealed record Venda(string VendedorId, decimal Valor);

public sealed record Comissao(string VendedorId, decimal TotalVendido, decimal Valor);

// Motivo para mudar: a política de comissão do comercial.
public static class CalculoDeComissoes
{
    private const decimal MetaMensal = 50_000m;
    private const decimal TaxaAteAMeta = 0.05m;
    private const decimal TaxaAcimaDaMeta = 0.08m;

    public static IReadOnlyList<Comissao> Calcular(IEnumerable<Venda> vendas) =>
        [.. vendas
            .GroupBy(venda => venda.VendedorId)
            .OrderBy(grupo => grupo.Key, StringComparer.Ordinal)
            .Select(grupo => DoVendedor(grupo.Key, grupo.Sum(venda => venda.Valor)))];

    private static Comissao DoVendedor(string vendedorId, decimal totalVendido)
    {
        var ateAMeta = Math.Min(totalVendido, MetaMensal) * TaxaAteAMeta;
        var acimaDaMeta = Math.Max(totalVendido - MetaMensal, 0m) * TaxaAcimaDaMeta;
        return new Comissao(vendedorId, totalVendido, ateAMeta + acimaDaMeta);
    }
}
```

```csharp
using System.Globalization;
using System.Text;

// Motivo para mudar: o layout do arquivo que o financeiro importa.
public static class ExportacaoDeComissoes
{
    private const string Cabecalho = "vendedor;total_vendido;comissao";

    private static readonly NumberFormatInfo VirgulaDecimal = new() { NumberDecimalSeparator = "," };

    public static string ParaCsv(IEnumerable<Comissao> comissoes)
    {
        var csv = new StringBuilder(Cabecalho).Append('\n');
        foreach (var comissao in comissoes)
        {
            csv.Append(comissao.VendedorId).Append(';')
                .Append(comissao.TotalVendido.ToString("F2", VirgulaDecimal)).Append(';')
                .Append(comissao.Valor.ToString("F2", VirgulaDecimal)).Append('\n');
        }

        return csv.ToString();
    }
}
```

## Como testar
- A regra com valores de venda, sem formato nem I/O: o teste compara comissões, não texto.
- O formato com comissões fixas, comparando o texto inteiro.
- Mudança de um motivo só altera os testes do módulo daquele motivo.

```python
# test_comissoes.py
from decimal import Decimal

from comissoes import Comissao, Venda, calcular_comissoes
from exportacao_de_comissoes import comissoes_em_csv


def test_calcular_comissoes_acima_da_meta_paga_taxa_maior_so_no_excedente() -> None:
    vendas = [Venda("v-1", Decimal(40000)), Venda("v-1", Decimal(20000))]
    assert calcular_comissoes(vendas) == [
        Comissao("v-1", Decimal(60000), Decimal(3300))
    ]


def test_comissoes_em_csv_valores_com_centavos_usa_virgula_decimal() -> None:
    comissoes = [Comissao("v-1", Decimal("60000.5"), Decimal("3300.04"))]
    assert (
        comissoes_em_csv(comissoes)
        == "vendedor;total_vendido;comissao\nv-1;60000,50;3300,04\n"
    )
```

```csharp
public class ComissoesTests
{
    [Fact]
    public void Calcular_AcimaDaMeta_PagaTaxaMaiorSoNoExcedente()
    {
        var vendas = new[] { new Venda("v-1", 40_000m), new Venda("v-1", 20_000m) };

        var comissoes = CalculoDeComissoes.Calcular(vendas);

        Assert.Equal(new[] { new Comissao("v-1", 60_000m, 3_300m) }, comissoes);
    }

    [Fact]
    public void ParaCsv_ValoresComCentavos_UsaVirgulaDecimal() =>
        Assert.Equal(
            "vendedor;total_vendido;comissao\nv-1;60000,50;3300,04\n",
            ExportacaoDeComissoes.ParaCsv([new Comissao("v-1", 60_000.5m, 3_300.04m)]));
}
```
