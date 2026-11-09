# Specification

Aplica-se quando a mesma condição de negócio (ex.: "cliente elegível a crédito") aparece reescrita em vários lugares, ou quando condições se combinam com "e", "ou" e "não" e as combinações mudam.

## Quando não usar
- Condição usada num lugar só: uma função com nome basta.
- Filtrar no banco: os critérios vão para a porta de leitura, e a consulta fica no adaptador. A especificação avalia objetos em memória.

## Forma
- Uma especificação é um predicado com nome e descrição; combina-se com "e", "ou" e "não" e devolve outra especificação.
- As regras do domínio viram constantes com nome (`ELEGIVEL_A_CREDITO`), usadas no caso de uso e em qualquer outro lugar que precise da mesma condição.
- A descrição gerada pela combinação explica a regra na mensagem de erro de negócio.
- Fica em domain (regra compartilhada entre casos de uso).

## Python
```python
# credito.py
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

DIAS_EM_UM_ANO = 365


@dataclass(frozen=True)
class Especificacao[T]:
    descricao: str
    avaliar: Callable[[T], bool]

    def __call__(self, alvo: T) -> bool:
        return self.avaliar(alvo)

    def __and__(self, outra: Especificacao[T]) -> Especificacao[T]:
        return Especificacao(
            f"({self.descricao} e {outra.descricao})",
            lambda alvo: self(alvo) and outra(alvo),
        )

    def __or__(self, outra: Especificacao[T]) -> Especificacao[T]:
        return Especificacao(
            f"({self.descricao} ou {outra.descricao})",
            lambda alvo: self(alvo) or outra(alvo),
        )

    def __invert__(self) -> Especificacao[T]:
        return Especificacao(f"não {self.descricao}", lambda alvo: not self(alvo))


@dataclass(frozen=True)
class Cliente:
    em_atraso: bool
    vip: bool
    dias_de_cliente: int


ADIMPLENTE: Especificacao[Cliente] = Especificacao(
    "adimplente", lambda cliente: not cliente.em_atraso
)
VIP: Especificacao[Cliente] = Especificacao("vip", lambda cliente: cliente.vip)
CLIENTE_HA_UM_ANO: Especificacao[Cliente] = Especificacao(
    "cliente há um ano ou mais",
    lambda cliente: cliente.dias_de_cliente >= DIAS_EM_UM_ANO,
)
ELEGIVEL_A_CREDITO = ADIMPLENTE & (VIP | CLIENTE_HA_UM_ANO)
```

## .NET
```csharp
public sealed record Especificacao<T>(string Descricao, Func<T, bool> Avaliar)
{
    public bool EAtendidaPor(T alvo) => Avaliar(alvo);

    public static Especificacao<T> operator &(Especificacao<T> esquerda, Especificacao<T> direita) =>
        new($"({esquerda.Descricao} e {direita.Descricao})",
            alvo => esquerda.Avaliar(alvo) && direita.Avaliar(alvo));

    public static Especificacao<T> operator |(Especificacao<T> esquerda, Especificacao<T> direita) =>
        new($"({esquerda.Descricao} ou {direita.Descricao})",
            alvo => esquerda.Avaliar(alvo) || direita.Avaliar(alvo));

    public static Especificacao<T> operator !(Especificacao<T> especificacao) =>
        new($"não {especificacao.Descricao}", alvo => !especificacao.Avaliar(alvo));
}

public sealed record Cliente(bool EmAtraso, bool Vip, int DiasDeCliente);

public static class RegrasDeCredito
{
    private const int DiasEmUmAno = 365;

    public static readonly Especificacao<Cliente> Adimplente =
        new("adimplente", cliente => !cliente.EmAtraso);

    public static readonly Especificacao<Cliente> Vip = new("vip", cliente => cliente.Vip);

    public static readonly Especificacao<Cliente> ClienteHaUmAno =
        new("cliente há um ano ou mais", cliente => cliente.DiasDeCliente >= DiasEmUmAno);

    public static readonly Especificacao<Cliente> ElegivelACredito =
        Adimplente & (Vip | ClienteHaUmAno);
}
```

## Como testar
- Cada especificação simples com um caso que atende e um que não atende.
- A regra composta com os casos que mudam o resultado (cada lado do "ou", o "e" que barra) e a descrição gerada.

```python
# test_credito.py
from credito import ELEGIVEL_A_CREDITO, Cliente


def test_elegivel_a_credito_vip_adimplente_e_elegivel() -> None:
    assert ELEGIVEL_A_CREDITO(Cliente(em_atraso=False, vip=True, dias_de_cliente=10))


def test_elegivel_a_credito_em_atraso_nao_e_elegivel() -> None:
    cliente = Cliente(em_atraso=True, vip=True, dias_de_cliente=900)
    assert not ELEGIVEL_A_CREDITO(cliente)


def test_elegivel_a_credito_descricao_explica_a_regra() -> None:
    esperada = "(adimplente e (vip ou cliente há um ano ou mais))"
    assert ELEGIVEL_A_CREDITO.descricao == esperada
```

```csharp
public class RegrasDeCreditoTests
{
    [Fact]
    public void ElegivelACredito_VipAdimplente_EhElegivel() =>
        Assert.True(RegrasDeCredito.ElegivelACredito.EAtendidaPor(
            new Cliente(EmAtraso: false, Vip: true, DiasDeCliente: 10)));

    [Fact]
    public void ElegivelACredito_EmAtraso_NaoEhElegivel() =>
        Assert.False(RegrasDeCredito.ElegivelACredito.EAtendidaPor(
            new Cliente(EmAtraso: true, Vip: true, DiasDeCliente: 900)));

    [Fact]
    public void ElegivelACredito_Descricao_ExplicaARegra() =>
        Assert.Equal(
            "(adimplente e (vip ou cliente há um ano ou mais))",
            RegrasDeCredito.ElegivelACredito.Descricao);
}
```
