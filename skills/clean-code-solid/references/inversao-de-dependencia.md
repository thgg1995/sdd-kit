# Inversão de dependência (D)

Aplica-se quando código de regra cria ou busca sozinho aquilo de que depende (cliente, conexão, relógio, gerador de id, configuração), ou quando o teste precisa de `patch` para trocar uma dependência.

## Sintomas
- Relógio ou aleatório chamado direto na regra: `datetime.now()`, `date.today()`, `uuid4()`, `random`; `DateTime.Now`, `DateTimeOffset.UtcNow`, `Guid.NewGuid()`, `Random.Shared`.
- Cliente, conexão ou sessão criados dentro da classe de regra ou no import do módulo de regra: `boto3.client(...)`, `httpx.AsyncClient()`; `new HttpClient()`, `new SqlConnection(...)`.
- Configuração lida fora do composition root: `os.environ`, `os.getenv`; `Environment.GetEnvironmentVariable`, `IConfiguration` no caso de uso (`clean-architecture`, regra 5 dos níveis 1 a 3).
- Acesso estático a recurso (`Banco.instancia()`, `Config.Valor`): `design-patterns`, `references/singleton.md`. Service locator: `dotnet-backend`.
- Teste com `monkeypatch.setattr`, `mock.patch("modulo.dependencia")` ou equivalente para trocar uma dependência do código testado.

## Quando não aplicar
- Regra pura, objeto de valor e biblioteca padrão sem I/O (`Decimal`, `re`, LINQ): chame direto, sem interface nem injeção. Porta é só para I/O e não determinismo (`clean-architecture`, regra 4 dos níveis 1 a 3).
- Composition root e adaptadores criam clientes e leem configuração: é o trabalho deles. No Lambda, o cliente criado no import do módulo do handler está no composition root.

## Forma
| Dependência | Entra por | Quem cria |
|---|---|---|
| porta de I/O (repositório, cliente de API, fila) | construtor, pelo tipo da porta | composition root |
| não determinismo (relógio, gerador de id) | construtor: função (`Callable`) ou porta; no .NET, o relógio é `TimeProvider` | composition root |
| configuração (prazo, limite) | construtor, como valor ou objeto de opções do componente | composition root, que lê e valida |
| dado da chamada (cliente, assunto) | parâmetro do método | quem chama |
| regra pura | chamada direta | — |
- Caso de uso em forma de função: as dependências entram como parâmetros, pelas mesmas regras.

## Python
```python
# chamados.py
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol


@dataclass(frozen=True)
class Chamado:
    protocolo: str
    cliente_id: str
    assunto: str
    responder_ate: datetime


class ChamadoRepository(Protocol):
    def salvar(self, chamado: Chamado) -> None: ...


class AbrirChamado:
    """Tudo de que depende entra pelo construtor; o dado da chamada, por parâmetro."""

    def __init__(
        self,
        repositorio: ChamadoRepository,
        prazo_de_resposta: timedelta,
        agora: Callable[[], datetime],
        novo_protocolo: Callable[[], str],
    ) -> None:
        self._repositorio = repositorio
        self._prazo_de_resposta = prazo_de_resposta
        self._agora = agora
        self._novo_protocolo = novo_protocolo

    def executar(self, cliente_id: str, assunto: str) -> Chamado:
        chamado = Chamado(
            protocolo=self._novo_protocolo(),
            cliente_id=cliente_id,
            assunto=assunto,
            responder_ate=self._agora() + self._prazo_de_resposta,
        )
        self._repositorio.salvar(chamado)
        return chamado
```

No composition root: `AbrirChamado(ChamadosDynamo(tabela), timedelta(hours=config.horas_para_responder), agora=lambda: datetime.now(UTC), novo_protocolo=lambda: uuid4().hex)`.

## .NET
```csharp
using System.ComponentModel.DataAnnotations;

public sealed record Chamado(string Protocolo, string ClienteId, string Assunto, DateTimeOffset ResponderAte);

public interface IChamadoRepository
{
    Task SalvarAsync(Chamado chamado, CancellationToken cancellationToken);
}

public interface IGeradorDeProtocolo
{
    string Novo();
}

public sealed class OpcoesDeChamado
{
    [Range(typeof(TimeSpan), "00:01:00", "30.00:00:00")]
    public TimeSpan PrazoDeResposta { get; init; }
}

// Tudo de que depende entra pelo construtor; o dado da chamada, por parâmetro.
public sealed class AbrirChamado(
    IChamadoRepository repositorio,
    IGeradorDeProtocolo protocolos,
    TimeProvider relogio,
    OpcoesDeChamado opcoes)
{
    public async Task<Chamado> ExecutarAsync(string clienteId, string assunto, CancellationToken cancellationToken)
    {
        var chamado = new Chamado(
            protocolos.Novo(),
            clienteId,
            assunto,
            relogio.GetUtcNow() + opcoes.PrazoDeResposta);
        await repositorio.SalvarAsync(chamado, cancellationToken);
        return chamado;
    }
}

// Adaptador (infrastructure) do não determinismo: o único lugar com Guid.NewGuid.
public sealed class ProtocoloAleatorio : IGeradorDeProtocolo
{
    public string Novo() => Guid.NewGuid().ToString("N");
}
```

```csharp
// composition root (Program.cs, em builder.Services): o único lugar que escolhe as implementações
services.AddOptions<OpcoesDeChamado>().BindConfiguration("Chamados").ValidateDataAnnotations().ValidateOnStart();
services.AddSingleton(provider => provider.GetRequiredService<IOptions<OpcoesDeChamado>>().Value);
services.AddSingleton(TimeProvider.System);
services.AddSingleton<IGeradorDeProtocolo, ProtocoloAleatorio>();
services.AddScoped<AbrirChamado>();
// IChamadoRepository: registrado junto do adaptador de dados (data-relational ou data-nosql).
```

## Como testar
- Relógio parado, gerador que devolve um valor conhecido e fake da porta entram pelo construtor, como no código de produção.
- Nenhum `patch` do módulo testado: se o teste precisou de um, a dependência está escondida; traga-a para o construtor.

```python
# test_chamados.py
from datetime import UTC, datetime, timedelta

from chamados import AbrirChamado, Chamado

AGORA = datetime(2026, 3, 2, 9, 0, tzinfo=UTC)


class ChamadosEmMemoria:
    def __init__(self) -> None:
        self.salvos: list[Chamado] = []

    def salvar(self, chamado: Chamado) -> None:
        self.salvos.append(chamado)


def abrir_chamado(repositorio: ChamadosEmMemoria) -> AbrirChamado:
    return AbrirChamado(
        repositorio,
        prazo_de_resposta=timedelta(hours=24),
        agora=lambda: AGORA,
        novo_protocolo=lambda: "000001",
    )


def test_executar_prazo_de_24_horas_responder_ate_no_dia_seguinte() -> None:
    chamado = abrir_chamado(ChamadosEmMemoria()).executar("c-1", "cobrança em dobro")
    assert chamado.responder_ate == datetime(2026, 3, 3, 9, 0, tzinfo=UTC)


def test_executar_chamado_novo_salva_com_o_protocolo_gerado() -> None:
    repositorio = ChamadosEmMemoria()
    abrir_chamado(repositorio).executar("c-1", "cobrança em dobro")
    assert [chamado.protocolo for chamado in repositorio.salvos] == ["000001"]
```

```csharp
public class AbrirChamadoTests
{
    private static readonly DateTimeOffset Agora = new(2026, 3, 2, 9, 0, 0, TimeSpan.Zero);

    private sealed class RelogioParado : TimeProvider
    {
        public override DateTimeOffset GetUtcNow() => Agora;
    }

    private sealed class ProtocoloFixo : IGeradorDeProtocolo
    {
        public string Novo() => "000001";
    }

    private sealed class ChamadosEmMemoria : IChamadoRepository
    {
        public List<Chamado> Salvos { get; } = [];

        public Task SalvarAsync(Chamado chamado, CancellationToken cancellationToken)
        {
            Salvos.Add(chamado);
            return Task.CompletedTask;
        }
    }

    private static AbrirChamado Criar(ChamadosEmMemoria repositorio) =>
        new(
            repositorio,
            new ProtocoloFixo(),
            new RelogioParado(),
            new OpcoesDeChamado { PrazoDeResposta = TimeSpan.FromHours(24) });

    [Fact]
    public async Task Executar_PrazoDe24Horas_ResponderAteNoDiaSeguinte()
    {
        var chamado = await Criar(new ChamadosEmMemoria())
            .ExecutarAsync("c-1", "cobrança em dobro", CancellationToken.None);

        Assert.Equal(Agora.AddDays(1), chamado.ResponderAte);
    }

    [Fact]
    public async Task Executar_ChamadoNovo_SalvaComOProtocoloGerado()
    {
        var repositorio = new ChamadosEmMemoria();

        await Criar(repositorio).ExecutarAsync("c-1", "cobrança em dobro", CancellationToken.None);

        Assert.Equal(new[] { "000001" }, repositorio.Salvos.Select(chamado => chamado.Protocolo));
    }
}
```
