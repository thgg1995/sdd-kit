# Interpreter

Aplica-se quando regras ou filtros vêm da configuração ou do usuário e são avaliados em tempo de execução (ex.: "país BR e (valor acima de 100 ou cliente VIP)" definido por campanha), em vez de ficarem fixos no código.

## Quando não usar
- Regra fixa, escrita pelo desenvolvedor: Specification (`references/specification.md`).
- Regra escrita em texto livre, com gramática própria: use uma biblioteca de parser ou uma linguagem de expressão pronta (ex.: JSONata, CEL); não escreva parser à mão.
- Expressão já avaliada por um motor da plataforma (ex.: JSONata no Step Functions): a regra fica no motor.

## Forma
- A regra chega como dado estruturado (JSON da configuração), não como texto: ler a regra é só percorrer esse dado.
- Um tipo imutável por operador, com `avaliar(alvo)`; os operadores compostos (`todas`, `alguma`) avaliam os filhos. É a árvore do Interpreter.
- A regra é lida e validada uma vez, na carga da configuração, e avaliada muitas vezes. Operador desconhecido ou campo ausente é erro de configuração na leitura, não na avaliação.
- Leitura e árvore ficam em application; carregar o JSON (arquivo, parâmetro) é adaptador.

## Python
```python
# regras.py
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Protocol


class RegraInvalida(Exception):
    """Erro de configuração: a regra não segue o formato aceito."""


class Regra(Protocol):
    def avaliar(self, alvo: Mapping[str, str]) -> bool: ...


@dataclass(frozen=True)
class Igual:
    campo: str
    valor: str

    def avaliar(self, alvo: Mapping[str, str]) -> bool:
        return alvo.get(self.campo) == self.valor


@dataclass(frozen=True)
class MaiorQue:
    campo: str
    limite: Decimal

    def avaliar(self, alvo: Mapping[str, str]) -> bool:
        return self.campo in alvo and Decimal(alvo[self.campo]) > self.limite


@dataclass(frozen=True)
class Todas:
    regras: tuple[Regra, ...]

    def avaliar(self, alvo: Mapping[str, str]) -> bool:
        return all(regra.avaliar(alvo) for regra in self.regras)


@dataclass(frozen=True)
class Alguma:
    regras: tuple[Regra, ...]

    def avaliar(self, alvo: Mapping[str, str]) -> bool:
        return any(regra.avaliar(alvo) for regra in self.regras)


def ler_regra(dado: Any) -> Regra:
    """Converte a regra da configuração (JSON já carregado) na árvore avaliável."""
    if not isinstance(dado, dict) or len(dado) != 1:
        raise RegraInvalida(repr(dado))
    ((operador, argumento),) = dado.items()
    try:
        if operador in ("todas", "alguma"):
            filhas = tuple(ler_regra(item) for item in argumento)
            return Todas(filhas) if operador == "todas" else Alguma(filhas)
        if operador == "igual":
            return Igual(argumento["campo"], argumento["valor"])
        if operador == "maior_que":
            return MaiorQue(argumento["campo"], Decimal(argumento["valor"]))
    except (KeyError, TypeError) as erro:
        raise RegraInvalida(repr(dado)) from erro
    raise RegraInvalida(f"operador desconhecido: {operador}")
```

## .NET
```csharp
using System.Globalization;
using System.Text.Json;

public sealed class RegraInvalidaException(string detalhe) : Exception($"Regra inválida: {detalhe}");

public interface IRegra
{
    bool Avaliar(IReadOnlyDictionary<string, string> alvo);
}

public sealed record Igual(string Campo, string Valor) : IRegra
{
    public bool Avaliar(IReadOnlyDictionary<string, string> alvo) =>
        alvo.TryGetValue(Campo, out var atual) && atual == Valor;
}

public sealed record MaiorQue(string Campo, decimal Limite) : IRegra
{
    public bool Avaliar(IReadOnlyDictionary<string, string> alvo) =>
        alvo.TryGetValue(Campo, out var atual)
        && decimal.Parse(atual, CultureInfo.InvariantCulture) > Limite;
}

public sealed record Todas(IReadOnlyList<IRegra> Regras) : IRegra
{
    public bool Avaliar(IReadOnlyDictionary<string, string> alvo) =>
        Regras.All(regra => regra.Avaliar(alvo));
}

public sealed record Alguma(IReadOnlyList<IRegra> Regras) : IRegra
{
    public bool Avaliar(IReadOnlyDictionary<string, string> alvo) =>
        Regras.Any(regra => regra.Avaliar(alvo));
}

public static class LeitorDeRegra
{
    // Converte a regra da configuração (JSON) na árvore avaliável.
    public static IRegra Ler(JsonElement dado)
    {
        if (dado.ValueKind != JsonValueKind.Object || dado.EnumerateObject().Count() != 1)
        {
            throw new RegraInvalidaException(dado.GetRawText());
        }

        var operador = dado.EnumerateObject().Single();
        var argumento = operador.Value;
        return operador.Name switch
        {
            "todas" => new Todas([.. argumento.EnumerateArray().Select(Ler)]),
            "alguma" => new Alguma([.. argumento.EnumerateArray().Select(Ler)]),
            "igual" => new Igual(Texto(argumento, "campo"), Texto(argumento, "valor")),
            "maior_que" => new MaiorQue(
                Texto(argumento, "campo"),
                decimal.Parse(Texto(argumento, "valor"), CultureInfo.InvariantCulture)),
            _ => throw new RegraInvalidaException($"operador desconhecido: {operador.Name}"),
        };
    }

    private static string Texto(JsonElement argumento, string propriedade) =>
        argumento.ValueKind == JsonValueKind.Object
        && argumento.TryGetProperty(propriedade, out var valor)
        && valor.ValueKind == JsonValueKind.String
            ? valor.GetString() ?? ""
            : throw new RegraInvalidaException($"'{propriedade}' ausente ou não é texto");
}
```

## Como testar
- A regra lida da configuração avaliada contra alvos que cobrem cada ramo (cada lado do "alguma", o "todas" que barra).
- A leitura: operador desconhecido e argumento malformado lançam o erro de configuração.

```python
# test_regras.py
import pytest

from regras import RegraInvalida, ler_regra

CONFIGURACAO = {
    "todas": [
        {"igual": {"campo": "pais", "valor": "BR"}},
        {
            "alguma": [
                {"maior_que": {"campo": "valor", "valor": "100"}},
                {"igual": {"campo": "vip", "valor": "sim"}},
            ]
        },
    ]
}


@pytest.mark.parametrize(
    ("alvo", "esperado"),
    [
        ({"pais": "BR", "valor": "150"}, True),
        ({"pais": "BR", "valor": "50", "vip": "sim"}, True),
        ({"pais": "BR", "valor": "50"}, False),
        ({"pais": "PT", "valor": "150"}, False),
    ],
)
def test_regra_da_configuracao_avalia_o_alvo(
    alvo: dict[str, str], esperado: bool
) -> None:
    assert ler_regra(CONFIGURACAO).avaliar(alvo) is esperado


@pytest.mark.parametrize(
    "dado",
    [{"parecido": {"campo": "pais", "valor": "BR"}}, {"igual": {"campo": "pais"}}],
)
def test_ler_regra_malformada_lanca_erro(dado: dict[str, object]) -> None:
    with pytest.raises(RegraInvalida):
        ler_regra(dado)
```

```csharp
using System.Text.Json;

public class LeitorDeRegraTests
{
    private const string Configuracao = """
        {"todas": [
          {"igual": {"campo": "pais", "valor": "BR"}},
          {"alguma": [
            {"maior_que": {"campo": "valor", "valor": "100"}},
            {"igual": {"campo": "vip", "valor": "sim"}}
          ]}
        ]}
        """;

    [Theory]
    [InlineData("BR", "150", null, true)]
    [InlineData("BR", "50", "sim", true)]
    [InlineData("BR", "50", null, false)]
    [InlineData("PT", "150", null, false)]
    public void Avaliar_RegraDaConfiguracao_AplicaAsCondicoes(string pais, string valor, string? vip, bool esperado)
    {
        var alvo = new Dictionary<string, string> { ["pais"] = pais, ["valor"] = valor };
        if (vip is not null)
        {
            alvo["vip"] = vip;
        }

        using var documento = JsonDocument.Parse(Configuracao);

        Assert.Equal(esperado, LeitorDeRegra.Ler(documento.RootElement).Avaliar(alvo));
    }

    [Theory]
    [InlineData("""{"parecido": {"campo": "pais", "valor": "BR"}}""")]
    [InlineData("""{"igual": {"campo": "pais"}}""")]
    public void Ler_RegraMalformada_LancaRegraInvalida(string json)
    {
        using var documento = JsonDocument.Parse(json);

        Assert.Throws<RegraInvalidaException>(() => LeitorDeRegra.Ler(documento.RootElement));
    }
}
```
