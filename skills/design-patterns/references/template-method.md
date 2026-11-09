# Template Method

Aplica-se quando duas ou mais operações seguem o mesmo roteiro e diferem em um ou dois passos (ex.: importar CSV e importar JSON: ler, validar, converter, gravar), com o roteiro copiado entre elas, ou quando há uma classe base abstrata cujo método chama passos abstratos que as subclasses preenchem.

## Quando não usar
- A forma clássica, por herança (classe base abstrata com os passos), contraria a regra de composição em vez de herança (`clean-code-solid`).
- Os roteiros só se parecem e mudam por motivos diferentes: mantenha-os separados (duplicação na `clean-code-solid`).

## Forma
- O roteiro é uma função (ou classe) comum; o passo que varia chega como parâmetro: uma função ou uma porta.
- Cada variação é só o passo dela (`ler_csv`, `ler_json`); o composition root, ou quem chama, escolhe qual passar.
- Variação de vários passos que andam juntos: passe um objeto com esses passos (é Strategy, `references/strategy.md`).
- O roteiro fica em application; passos com I/O são portas.

## Python
```python
# importacao.py
import csv
import io
import json
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Linha:
    sku: str
    quantidade: int


@dataclass(frozen=True)
class Resultado:
    importadas: int
    rejeitadas: int


class RegistroInvalido(Exception):
    """O registro não tem SKU ou quantidade válida."""


Leitor = Callable[[str], list[dict[str, str]]]


def ler_csv(texto: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(texto)))


def ler_json(texto: str) -> list[dict[str, str]]:
    return json.loads(texto)


def converter(registro: dict[str, str]) -> Linha:
    try:
        linha = Linha(registro["sku"], int(registro["quantidade"]))
    except (KeyError, ValueError) as erro:
        raise RegistroInvalido(repr(registro)) from erro
    if not linha.sku or linha.quantidade <= 0:
        raise RegistroInvalido(repr(registro))
    return linha


def importar(texto: str, ler: Leitor, gravar: Callable[[Linha], None]) -> Resultado:
    """O roteiro comum; o passo que varia (ler) chega como parâmetro."""
    importadas = rejeitadas = 0
    for registro in ler(texto):
        try:
            linha = converter(registro)
        except RegistroInvalido:
            rejeitadas += 1
            continue
        gravar(linha)
        importadas += 1
    return Resultado(importadas, rejeitadas)
```

## .NET
```csharp
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Text.Json;
using Microsoft.VisualBasic.FileIO;

public sealed record Linha(string Sku, int Quantidade);

public sealed record Resultado(int Importadas, int Rejeitadas);

public static class Importacao
{
    public static IReadOnlyList<IReadOnlyDictionary<string, string>> LerCsv(string texto)
    {
        using var leitor = new TextFieldParser(new StringReader(texto)) { TextFieldType = FieldType.Delimited };
        leitor.SetDelimiters(",");
        var cabecalho = leitor.ReadFields() ?? [];
        var registros = new List<IReadOnlyDictionary<string, string>>();
        while (leitor.ReadFields() is { } campos)
        {
            registros.Add(cabecalho.Zip(campos).ToDictionary(par => par.First, par => par.Second));
        }

        return registros;
    }

    public static IReadOnlyList<IReadOnlyDictionary<string, string>> LerJson(string texto) =>
        JsonSerializer.Deserialize<List<Dictionary<string, string>>>(texto) ?? [];

    // O roteiro comum; o passo que varia (ler) chega como parâmetro.
    public static Resultado Importar(
        string texto,
        Func<string, IReadOnlyList<IReadOnlyDictionary<string, string>>> ler,
        Action<Linha> gravar)
    {
        var importadas = 0;
        var rejeitadas = 0;
        foreach (var registro in ler(texto))
        {
            if (TentarConverter(registro, out var linha))
            {
                gravar(linha);
                importadas++;
            }
            else
            {
                rejeitadas++;
            }
        }

        return new Resultado(importadas, rejeitadas);
    }

    private static bool TentarConverter(
        IReadOnlyDictionary<string, string> registro, [NotNullWhen(true)] out Linha? linha)
    {
        linha = registro.TryGetValue("sku", out var sku) && sku.Length > 0
            && registro.TryGetValue("quantidade", out var texto)
            && int.TryParse(texto, CultureInfo.InvariantCulture, out var quantidade) && quantidade > 0
                ? new Linha(sku, quantidade)
                : null;
        return linha is not null;
    }
}
```

## Como testar
- O roteiro com cada variação do passo, sobre a mesma entrada lógica: o resultado tem de ser o mesmo.
- Cada passo variável sozinho (o leitor de CSV, o de JSON).

```python
# test_importacao.py
import pytest

from importacao import Leitor, Linha, importar, ler_csv, ler_json

CSV = "sku,quantidade\na,2\n,5\nb,x\n"
JSON = (
    '[{"sku": "a", "quantidade": "2"}, {"sku": "", "quantidade": "5"},'
    ' {"sku": "b", "quantidade": "x"}]'
)


@pytest.mark.parametrize(("texto", "ler"), [(CSV, ler_csv), (JSON, ler_json)])
def test_importar_segue_o_mesmo_roteiro_para_cada_formato(
    texto: str, ler: Leitor
) -> None:
    gravadas: list[Linha] = []
    resultado = importar(texto, ler, gravadas.append)
    assert (resultado.importadas, resultado.rejeitadas) == (1, 2)
    assert gravadas == [Linha("a", 2)]
```

```csharp
public class ImportacaoTests
{
    private const string Csv = "sku,quantidade\na,2\n,5\nb,x\n";
    private const string Json =
        """[{"sku": "a", "quantidade": "2"}, {"sku": "", "quantidade": "5"}, {"sku": "b", "quantidade": "x"}]""";

    [Fact]
    public void Importar_Csv_SegueORoteiroComum() => Verificar(Csv, Importacao.LerCsv);

    [Fact]
    public void Importar_Json_SegueORoteiroComum() => Verificar(Json, Importacao.LerJson);

    private static void Verificar(
        string texto, Func<string, IReadOnlyList<IReadOnlyDictionary<string, string>>> ler)
    {
        var gravadas = new List<Linha>();

        var resultado = Importacao.Importar(texto, ler, gravadas.Add);

        Assert.Equal(new Resultado(Importadas: 1, Rejeitadas: 2), resultado);
        Assert.Equal(new[] { new Linha("a", 2) }, gravadas);
    }
}
```
