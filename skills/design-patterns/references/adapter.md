# Adapter

Aplica-se quando o caso de uso precisa de uma operação que uma biblioteca, SDK ou sistema externo oferece em outro formato (nomes, unidades, tipos, códigos de erro), ou quando esse formato externo aparece espalhado pelo código de negócio (ex.: centavos e códigos numéricos de um sistema legado dentro do caso de uso).

## Quando não usar
- Biblioteca sem I/O que o domínio pode usar como está (datas, dinheiro): a `clean-architecture` diz quando ela entra direto, sem adaptador.
- Conversão de entrada (request, mensagem recebida): é adaptador de entrada, também na `clean-architecture`.

## Forma
- A porta fala a língua da aplicação: tipos, unidades e erros dela. O adaptador implementa a porta e traduz nos dois sentidos.
- Erros: "não encontrado" do sistema externo vira erro de negócio; indisponibilidade vira falha transitória, com tipo próprio, para quem decide retentar.
- O cliente do sistema externo entra pelo construtor; o adaptador não lê configuração nem cria cliente.
- Regras do time: `clean-architecture` (porta em application, adaptador em infrastructure).

## Python
```python
# saldo.py
from decimal import Decimal
from typing import Protocol

CENTAVOS_POR_REAL = Decimal(100)
CODIGO_OK = 0
CODIGO_CONTA_INEXISTENTE = 404


class ContaInexistente(Exception):
    """Erro de negócio: a conta não existe."""


class SaldoIndisponivel(Exception):
    """Falha transitória: o sistema de saldo não respondeu; pode ser retentada."""


class ConsultaDeSaldo(Protocol):
    """Porta, na língua da aplicação: saldo em reais."""

    def saldo(self, conta: str) -> Decimal: ...


class ClienteLegado(Protocol):
    """Formato do sistema externo: código numérico e valor em centavos."""

    def consultar(self, numero_conta: str) -> dict[str, int]: ...


class SaldoDoSistemaLegado:
    def __init__(self, cliente: ClienteLegado) -> None:
        self._cliente = cliente

    def saldo(self, conta: str) -> Decimal:
        resposta = self._cliente.consultar(conta)
        codigo = resposta["cod"]
        if codigo == CODIGO_CONTA_INEXISTENTE:
            raise ContaInexistente(conta)
        if codigo != CODIGO_OK:
            raise SaldoIndisponivel(f"código {codigo}")
        return Decimal(resposta["saldo_centavos"]) / CENTAVOS_POR_REAL
```

## .NET
```csharp
public sealed class ContaInexistenteException(string conta)
    : Exception($"Conta inexistente: {conta}");

public sealed class SaldoIndisponivelException(int codigo)
    : Exception($"Sistema de saldo indisponível: código {codigo}");

// Porta, na língua da aplicação: saldo em reais.
public interface IConsultaDeSaldo
{
    Task<decimal> SaldoAsync(string conta, CancellationToken cancellationToken);
}

// Formato do sistema externo: código numérico e valor em centavos.
public sealed record RespostaLegada(int Cod, long SaldoCentavos);

public interface IClienteLegado
{
    Task<RespostaLegada> ConsultarAsync(string numeroConta, CancellationToken cancellationToken);
}

public sealed class SaldoDoSistemaLegado(IClienteLegado cliente) : IConsultaDeSaldo
{
    private const decimal CentavosPorReal = 100m;
    private const int CodigoOk = 0;
    private const int CodigoContaInexistente = 404;

    public async Task<decimal> SaldoAsync(string conta, CancellationToken cancellationToken)
    {
        var resposta = await cliente.ConsultarAsync(conta, cancellationToken);
        return resposta.Cod switch
        {
            CodigoOk => resposta.SaldoCentavos / CentavosPorReal,
            CodigoContaInexistente => throw new ContaInexistenteException(conta),
            _ => throw new SaldoIndisponivelException(resposta.Cod),
        };
    }
}
```

## Como testar
- O adaptador com um fake do cliente externo: a conversão (centavos para reais) e cada código de erro traduzido.
- A chamada ao sistema real fica para o QA de integração (`qa-integration`).

```python
# test_saldo.py
from decimal import Decimal

import pytest

from saldo import ContaInexistente, SaldoDoSistemaLegado, SaldoIndisponivel


class ClienteFake:
    def __init__(self, resposta: dict[str, int]) -> None:
        self.resposta = resposta

    def consultar(self, numero_conta: str) -> dict[str, int]:
        return self.resposta


def test_saldo_converte_centavos_em_reais() -> None:
    adaptador = SaldoDoSistemaLegado(ClienteFake({"cod": 0, "saldo_centavos": 12345}))
    assert adaptador.saldo("c-1") == Decimal("123.45")


@pytest.mark.parametrize(
    ("codigo", "erro"), [(404, ContaInexistente), (503, SaldoIndisponivel)]
)
def test_saldo_traduz_codigos_de_erro(codigo: int, erro: type[Exception]) -> None:
    adaptador = SaldoDoSistemaLegado(ClienteFake({"cod": codigo}))
    with pytest.raises(erro):
        adaptador.saldo("c-1")
```

```csharp
public class SaldoDoSistemaLegadoTests
{
    private sealed class ClienteFake(RespostaLegada resposta) : IClienteLegado
    {
        public Task<RespostaLegada> ConsultarAsync(string numeroConta, CancellationToken cancellationToken) =>
            Task.FromResult(resposta);
    }

    [Fact]
    public async Task SaldoAsync_RespostaOk_ConverteCentavosEmReais()
    {
        var adaptador = new SaldoDoSistemaLegado(new ClienteFake(new RespostaLegada(Cod: 0, SaldoCentavos: 12345)));

        Assert.Equal(123.45m, await adaptador.SaldoAsync("c-1", CancellationToken.None));
    }

    [Fact]
    public async Task SaldoAsync_Codigo404_LancaContaInexistente() =>
        await Assert.ThrowsAsync<ContaInexistenteException>(() =>
            new SaldoDoSistemaLegado(new ClienteFake(new RespostaLegada(404, 0)))
                .SaldoAsync("c-1", CancellationToken.None));

    [Fact]
    public async Task SaldoAsync_OutroCodigo_LancaSaldoIndisponivel() =>
        await Assert.ThrowsAsync<SaldoIndisponivelException>(() =>
            new SaldoDoSistemaLegado(new ClienteFake(new RespostaLegada(503, 0)))
                .SaldoAsync("c-1", CancellationToken.None));
}
```
