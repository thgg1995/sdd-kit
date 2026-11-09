# Segregação de interfaces (I)

Aplica-se quando um cliente depende de uma interface com operações que ele não usa, ou quando uma função recebe um objeto inteiro para usar um ou dois campos.

## Sintomas
- Interface que junta grupos de operações usados por clientes diferentes (ex.: `Notificador` com e-mail, SMS e push; `ServicoDeClientes` com cadastro, crédito e relatório), e cada cliente usa um grupo.
- Implementação que lança "não suportado" ou deixa vazia uma operação que o seu provedor não oferece (`references/substituicao-de-liskov.md`).
- Fake de teste com métodos vazios ou que lançam, só para satisfazer a interface.
- Função que recebe a entidade, a configuração inteira ou a requisição e usa um ou dois campos.

## Quando não aplicar
- Porta de repositório por entidade, com as operações que os casos de uso usam e um fake compartilhado que passa na suíte de contrato (`design-patterns`, `references/repository.md`): casos de uso que usam partes dela não são violação.
- Interface por operação, por reflexo: divida por cliente (o grupo de operações que um cliente usa junto), não por método.
- Tipo pequeno que é o próprio conceito tratado (ex.: `Endereco` para calcular frete) pode ir inteiro, mesmo que a função não use todos os campos.

## Forma
- Cada cliente depende da interface com as operações que usa, nomeada pelo papel (`EnvioDeEmail`), não por quem implementa (`ProvedorXyz`).
- A implementação concreta cumpre as interfaces dos papéis que o seu provedor oferece: no Python, com `Protocol`, basta ter os métodos; no C#, ela lista as interfaces na declaração.
- No .NET, registre o adaptador uma vez e encaminhe cada interface para esse registro (composition root abaixo). Registrar `AddTransient<IEnvioDeEmail, ProvedorDeMensagens>()` cria outro registro, sem a configuração do primeiro: no cliente HTTP tipado, sem endereço nem resiliência.
- Função: receba os campos que usa (dentro do limite de parâmetros) ou um tipo menor só com eles.

## Python
```python
# notificacoes.py
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from typing import Protocol

ASSUNTO_DO_LEMBRETE = "Sua fatura vence em breve"


@dataclass(frozen=True)
class FaturaAVencer:
    fatura_id: str
    email: str
    vencimento: date


# Uma porta por canal: cada caso de uso depende só do canal que usa.
class EnvioDeEmail(Protocol):
    def enviar_email(self, destinatario: str, assunto: str, corpo: str) -> None: ...


class EnvioDeSms(Protocol):
    def enviar_sms(self, telefone: str, texto: str) -> None: ...


def lembrar_vencimentos(faturas: Iterable[FaturaAVencer], envio: EnvioDeEmail) -> None:
    for fatura in faturas:
        corpo = f"A fatura {fatura.fatura_id} vence em {fatura.vencimento:%d/%m/%Y}."
        envio.enviar_email(fatura.email, ASSUNTO_DO_LEMBRETE, corpo)


def enviar_codigo_de_acesso(telefone: str, codigo: str, envio: EnvioDeSms) -> None:
    envio.enviar_sms(telefone, f"Seu código de acesso: {codigo}")
```

## .NET
```csharp
public sealed record FaturaAVencer(string FaturaId, string Email, DateOnly Vencimento);

// Uma porta por canal: cada caso de uso depende só do canal que usa.
public interface IEnvioDeEmail
{
    Task EnviarEmailAsync(string destinatario, string assunto, string corpo, CancellationToken cancellationToken);
}

public interface IEnvioDeSms
{
    Task EnviarSmsAsync(string telefone, string texto, CancellationToken cancellationToken);
}

public sealed class LembrarVencimentos(IEnvioDeEmail envio)
{
    private const string Assunto = "Sua fatura vence em breve";

    public async Task ExecutarAsync(IEnumerable<FaturaAVencer> faturas, CancellationToken cancellationToken)
    {
        foreach (var fatura in faturas)
        {
            var corpo = $"A fatura {fatura.FaturaId} vence em {fatura.Vencimento:dd'/'MM'/'yyyy}.";
            await envio.EnviarEmailAsync(fatura.Email, Assunto, corpo, cancellationToken);
        }
    }
}

public sealed class EnviarCodigoDeAcesso(IEnvioDeSms envio)
{
    public Task ExecutarAsync(string telefone, string codigo, CancellationToken cancellationToken) =>
        envio.EnviarSmsAsync(telefone, $"Seu código de acesso: {codigo}", cancellationToken);
}
```

```csharp
using System.Net.Http.Json;

// Adaptador (infrastructure): o provedor oferece os dois canais, então cumpre as duas portas.
public sealed class ProvedorDeMensagens(HttpClient http) : IEnvioDeEmail, IEnvioDeSms
{
    public async Task EnviarEmailAsync(string destinatario, string assunto, string corpo, CancellationToken cancellationToken)
    {
        using var resposta = await http.PostAsJsonAsync("emails", new { destinatario, assunto, corpo }, cancellationToken);
        resposta.EnsureSuccessStatusCode();
    }

    public async Task EnviarSmsAsync(string telefone, string texto, CancellationToken cancellationToken)
    {
        using var resposta = await http.PostAsJsonAsync("sms", new { telefone, texto }, cancellationToken);
        resposta.EnsureSuccessStatusCode();
    }
}
```

```csharp
// composition root (Program.cs, em builder.Services): um registro do adaptador; cada porta é encaminhada a ele
services.AddHttpClient<ProvedorDeMensagens>(); // endereço, timeout e resiliência: api-design
services.AddTransient<IEnvioDeEmail>(provider => provider.GetRequiredService<ProvedorDeMensagens>());
services.AddTransient<IEnvioDeSms>(provider => provider.GetRequiredService<ProvedorDeMensagens>());
services.AddTransient<LembrarVencimentos>();
services.AddTransient<EnviarCodigoDeAcesso>();
```

## Como testar
- O fake implementa só a interface do cliente testado: uma operação, sem método vazio.
- O adaptador, contra o provedor real: QA de integração (`qa-integration`).

```python
# test_notificacoes.py
from datetime import date

from notificacoes import FaturaAVencer, enviar_codigo_de_acesso, lembrar_vencimentos


class CaixaDeEmails:
    """Fake do canal de e-mail: só a operação que o lembrete usa."""

    def __init__(self) -> None:
        self.enviados: list[tuple[str, str, str]] = []

    def enviar_email(self, destinatario: str, assunto: str, corpo: str) -> None:
        self.enviados.append((destinatario, assunto, corpo))


class CaixaDeSms:
    def __init__(self) -> None:
        self.enviados: list[tuple[str, str]] = []

    def enviar_sms(self, telefone: str, texto: str) -> None:
        self.enviados.append((telefone, texto))


def test_lembrar_vencimentos_uma_fatura_envia_email_com_o_vencimento() -> None:
    caixa = CaixaDeEmails()
    fatura = FaturaAVencer("f-1", "cliente@exemplo.com", date(2026, 12, 10))
    lembrar_vencimentos([fatura], caixa)
    assert caixa.enviados == [
        (
            "cliente@exemplo.com",
            "Sua fatura vence em breve",
            "A fatura f-1 vence em 10/12/2026.",
        )
    ]


def test_enviar_codigo_de_acesso_com_codigo_envia_sms_com_o_codigo() -> None:
    caixa = CaixaDeSms()
    enviar_codigo_de_acesso("+550000000000", "123456", caixa)
    assert caixa.enviados == [("+550000000000", "Seu código de acesso: 123456")]
```

```csharp
public class LembrarVencimentosTests
{
    // Fake do canal de e-mail: só a operação que o lembrete usa.
    private sealed class CaixaDeEmails : IEnvioDeEmail
    {
        public List<(string Destinatario, string Assunto, string Corpo)> Enviados { get; } = [];

        public Task EnviarEmailAsync(string destinatario, string assunto, string corpo, CancellationToken cancellationToken)
        {
            Enviados.Add((destinatario, assunto, corpo));
            return Task.CompletedTask;
        }
    }

    [Fact]
    public async Task Executar_UmaFatura_EnviaEmailComOVencimento()
    {
        var caixa = new CaixaDeEmails();
        var fatura = new FaturaAVencer("f-1", "cliente@exemplo.com", new DateOnly(2026, 12, 10));

        await new LembrarVencimentos(caixa).ExecutarAsync([fatura], CancellationToken.None);

        Assert.Equal(
            new[] { ("cliente@exemplo.com", "Sua fatura vence em breve", "A fatura f-1 vence em 10/12/2026.") },
            caixa.Enviados);
    }
}

public class EnviarCodigoDeAcessoTests
{
    private sealed class CaixaDeSms : IEnvioDeSms
    {
        public List<(string Telefone, string Texto)> Enviados { get; } = [];

        public Task EnviarSmsAsync(string telefone, string texto, CancellationToken cancellationToken)
        {
            Enviados.Add((telefone, texto));
            return Task.CompletedTask;
        }
    }

    [Fact]
    public async Task Executar_ComCodigo_EnviaSmsComOCodigo()
    {
        var caixa = new CaixaDeSms();

        await new EnviarCodigoDeAcesso(caixa).ExecutarAsync("+550000000000", "123456", CancellationToken.None);

        Assert.Equal(new[] { ("+550000000000", "Seu código de acesso: 123456") }, caixa.Enviados);
    }
}
```
