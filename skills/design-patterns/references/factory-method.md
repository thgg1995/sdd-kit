# Factory Method

Aplica-se quando o tipo do objeto a criar depende do dado recebido (ex.: CPF ou CNPJ pelo número de dígitos), ou quando a construção é escolhida por `if` em vários lugares do código.

## Quando não usar
- Um tipo só: chame o construtor.
- A escolha depende só da configuração da instalação: o composition root decide uma vez, sem fábrica.
- Os objetos não têm estado próprio e só variam no comportamento: é Strategy (`references/strategy.md`), não fábrica.

## Forma
- Uma função (Python) ou um método estático no tipo base (.NET) recebe o dado, escolhe o tipo e o cria; dado que não corresponde a nenhum tipo é erro de negócio.
- É o único lugar com o `if` da escolha; o resto do código usa o tipo base.
- Objetos criados que precisam de dependências (cliente, relógio): a fábrica vira uma classe que recebe essas dependências no construtor e é montada no composition root.
- A forma clássica (subclasse que sobrescreve o método de criação) só compensa em framework extensível por herança; em código de aplicação, use a função.
- Várias peças que variam juntas por família (ex.: formato de cobrança e leitor de webhook de cada provedor): `references/abstract-factory.md`.

## Python
```python
# documento.py
from dataclasses import dataclass

TAMANHO_CPF = 11
TAMANHO_CNPJ = 14


class DocumentoInvalido(Exception):
    """Erro de negócio: o texto não é um CPF nem um CNPJ."""


@dataclass(frozen=True)
class Cpf:
    numero: str

    def formatado(self) -> str:
        numero = self.numero
        return f"{numero[:3]}.{numero[3:6]}.{numero[6:9]}-{numero[9:]}"


@dataclass(frozen=True)
class Cnpj:
    numero: str

    def formatado(self) -> str:
        numero = self.numero
        return f"{numero[:2]}.{numero[2:5]}.{numero[5:8]}/{numero[8:12]}-{numero[12:]}"


Documento = Cpf | Cnpj


def criar_documento(texto: str) -> Documento:
    numero = "".join(caractere for caractere in texto if caractere.isdigit())
    if len(numero) == TAMANHO_CPF:
        return Cpf(numero)
    if len(numero) == TAMANHO_CNPJ:
        return Cnpj(numero)
    raise DocumentoInvalido(texto)
```

## .NET
```csharp
public sealed class DocumentoInvalidoException(string texto)
    : Exception($"Documento inválido: {texto}");

public abstract record Documento(string Numero)
{
    private const int TamanhoCpf = 11;
    private const int TamanhoCnpj = 14;

    public abstract string Formatado();

    public static Documento Criar(string texto)
    {
        var numero = new string(texto.Where(char.IsDigit).ToArray());
        return numero.Length switch
        {
            TamanhoCpf => new Cpf(numero),
            TamanhoCnpj => new Cnpj(numero),
            _ => throw new DocumentoInvalidoException(texto),
        };
    }
}

public sealed record Cpf(string Numero) : Documento(Numero)
{
    public override string Formatado() =>
        $"{Numero[..3]}.{Numero[3..6]}.{Numero[6..9]}-{Numero[9..]}";
}

public sealed record Cnpj(string Numero) : Documento(Numero)
{
    public override string Formatado() =>
        $"{Numero[..2]}.{Numero[2..5]}.{Numero[5..8]}/{Numero[8..12]}-{Numero[12..]}";
}
```

## Como testar
- Um teste por tipo que a fábrica cria, conferindo o tipo e o comportamento dele.
- Dado que não corresponde a nenhum tipo: o erro de negócio.

```python
# test_documento.py
import pytest

from documento import Cnpj, Cpf, DocumentoInvalido, criar_documento


def test_criar_documento_com_onze_digitos_cria_cpf() -> None:
    documento = criar_documento("123.456.789-01")
    assert isinstance(documento, Cpf)
    assert documento.formatado() == "123.456.789-01"


def test_criar_documento_com_quatorze_digitos_cria_cnpj() -> None:
    assert isinstance(criar_documento("12345678000199"), Cnpj)


def test_criar_documento_com_tamanho_invalido_lanca_erro() -> None:
    with pytest.raises(DocumentoInvalido):
        criar_documento("123")
```

```csharp
public class DocumentoTests
{
    [Fact]
    public void Criar_OnzeDigitos_CriaCpf()
    {
        var documento = Documento.Criar("123.456.789-01");

        Assert.IsType<Cpf>(documento);
        Assert.Equal("123.456.789-01", documento.Formatado());
    }

    [Fact]
    public void Criar_QuatorzeDigitos_CriaCnpj() =>
        Assert.IsType<Cnpj>(Documento.Criar("12345678000199"));

    [Fact]
    public void Criar_TamanhoInvalido_LancaDocumentoInvalido() =>
        Assert.Throws<DocumentoInvalidoException>(() => Documento.Criar("123"));
}
```
