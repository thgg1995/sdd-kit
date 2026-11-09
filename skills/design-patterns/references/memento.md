# Memento

Aplica-se quando uma operação precisa voltar um objeto em memória a um estado anterior: desfazer numa edição em várias etapas, ou tentar uma alteração e voltar se uma validação reprovar. É raro no back-end.

## Quando não usar
- Histórico persistente, auditoria ou "voltar a versão" de dado salvo: versões ou eventos no banco, desenhados no modelo de dados (`data-relational`, `data-nosql`).
- Reverter efeito externo (cobrança, envio): é compensação (`references/mediator.md`).
- Uma alteração só: guarde o objeto anterior numa variável.

## Forma
- Com objetos imutáveis, o memento é a própria versão anterior: cada alteração cria uma versão nova (`replace` no Python, `with` no C#), e a anterior vai para uma pilha.
- Desfazer tira o topo da pilha; desfazer sem histórico é erro de negócio.
- A pilha fica com quem controla a edição (o caso de uso ou um objeto de edição), não dentro da entidade.

## Python
```python
# edicao.py
from dataclasses import dataclass, replace
from decimal import Decimal


class NadaADesfazer(Exception):
    """Erro de negócio: não há alteração anterior."""


@dataclass(frozen=True)
class Proposta:
    cliente: str
    desconto: Decimal
    prazo_em_dias: int


class EdicaoDeProposta:
    """Guarda as versões anteriores (os mementos) para desfazer."""

    def __init__(self, inicial: Proposta) -> None:
        self._atual = inicial
        self._anteriores: list[Proposta] = []

    @property
    def atual(self) -> Proposta:
        return self._atual

    def alterar_desconto(self, desconto: Decimal) -> None:
        self._alterar(replace(self._atual, desconto=desconto))

    def alterar_prazo(self, prazo_em_dias: int) -> None:
        self._alterar(replace(self._atual, prazo_em_dias=prazo_em_dias))

    def desfazer(self) -> None:
        if not self._anteriores:
            raise NadaADesfazer()
        self._atual = self._anteriores.pop()

    def _alterar(self, nova: Proposta) -> None:
        self._anteriores.append(self._atual)
        self._atual = nova
```

## .NET
```csharp
public sealed class NadaADesfazerException() : Exception("Nada a desfazer");

public sealed record Proposta(string Cliente, decimal Desconto, int PrazoEmDias);

// Guarda as versões anteriores (os mementos) para desfazer.
public sealed class EdicaoDeProposta(Proposta inicial)
{
    private readonly Stack<Proposta> _anteriores = new();

    public Proposta Atual { get; private set; } = inicial;

    public void AlterarDesconto(decimal desconto) => Alterar(Atual with { Desconto = desconto });

    public void AlterarPrazo(int prazoEmDias) => Alterar(Atual with { PrazoEmDias = prazoEmDias });

    public void Desfazer() =>
        Atual = _anteriores.TryPop(out var anterior) ? anterior : throw new NadaADesfazerException();

    private void Alterar(Proposta nova)
    {
        _anteriores.Push(Atual);
        Atual = nova;
    }
}
```

## Como testar
- Alterações seguidas de desfazer voltam exatamente à versão anterior.
- Desfazer sem histórico lança o erro de negócio.

```python
# test_edicao.py
from decimal import Decimal

import pytest

from edicao import EdicaoDeProposta, NadaADesfazer, Proposta

INICIAL = Proposta("c-1", Decimal(0), 30)


def test_desfazer_volta_a_versao_anterior() -> None:
    edicao = EdicaoDeProposta(INICIAL)
    edicao.alterar_desconto(Decimal("0.05"))
    edicao.alterar_prazo(45)
    edicao.desfazer()
    assert edicao.atual == Proposta("c-1", Decimal("0.05"), 30)


def test_desfazer_sem_alteracao_lanca_erro() -> None:
    with pytest.raises(NadaADesfazer):
        EdicaoDeProposta(INICIAL).desfazer()
```

```csharp
public class EdicaoDePropostaTests
{
    private static readonly Proposta Inicial = new("c-1", 0m, 30);

    [Fact]
    public void Desfazer_DepoisDeDuasAlteracoes_VoltaAVersaoAnterior()
    {
        var edicao = new EdicaoDeProposta(Inicial);
        edicao.AlterarDesconto(0.05m);
        edicao.AlterarPrazo(45);

        edicao.Desfazer();

        Assert.Equal(new Proposta("c-1", 0.05m, 30), edicao.Atual);
    }

    [Fact]
    public void Desfazer_SemAlteracao_LancaNadaADesfazer() =>
        Assert.Throws<NadaADesfazerException>(() => new EdicaoDeProposta(Inicial).Desfazer());
}
```
