# Bridge

Aplica-se quando duas dimensões variam de forma independente e cada combinação vira uma classe (ex.: tipo de aviso × canal de envio: `LembretePorEmail`, `LembretePorSms`, `AlertaPorEmail`…), ou quando o plano já traz as duas listas de variações.

## Quando não usar
- Só uma dimensão varia: é Strategy (`references/strategy.md`) ou uma porta comum.
- As combinações são poucas, fixas e não crescem no plano: duas classes diretas são mais simples que a separação.

## Forma
- Cada dimensão vira uma hierarquia própria. A primeira (a abstração: o tipo de aviso) recebe a segunda (a implementação: o canal) no construtor e só fala com ela pela interface.
- Hoje é composição de uma porta: o canal é uma porta implementada em infrastructure; os tipos de aviso ficam em application.
- O composition root combina as duas dimensões (`Alerta(CanalSms(...))`). Um canal ou um aviso novo é uma classe a mais, não uma por combinação.

## Python
```python
# avisos.py
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Contato:
    principal: str
    plantao: str


class Canal(Protocol):
    def enviar(self, destino: str, texto: str) -> None: ...


class Aviso(Protocol):
    def notificar(self, contato: Contato, assunto: str) -> None: ...


class Lembrete:
    def __init__(self, canal: Canal) -> None:
        self._canal = canal

    def notificar(self, contato: Contato, assunto: str) -> None:
        self._canal.enviar(contato.principal, f"Lembrete: {assunto}")


class Alerta:
    """Vai para o contato principal e para o plantão."""

    def __init__(self, canal: Canal) -> None:
        self._canal = canal

    def notificar(self, contato: Contato, assunto: str) -> None:
        texto = f"ALERTA: {assunto}"
        self._canal.enviar(contato.principal, texto)
        self._canal.enviar(contato.plantao, texto)
```

## .NET
```csharp
public sealed record Contato(string Principal, string Plantao);

public interface ICanal
{
    Task EnviarAsync(string destino, string texto, CancellationToken cancellationToken);
}

public interface IAviso
{
    Task NotificarAsync(Contato contato, string assunto, CancellationToken cancellationToken);
}

public sealed class Lembrete(ICanal canal) : IAviso
{
    public Task NotificarAsync(Contato contato, string assunto, CancellationToken cancellationToken) =>
        canal.EnviarAsync(contato.Principal, $"Lembrete: {assunto}", cancellationToken);
}

// Vai para o contato principal e para o plantão.
public sealed class Alerta(ICanal canal) : IAviso
{
    public async Task NotificarAsync(Contato contato, string assunto, CancellationToken cancellationToken)
    {
        var texto = $"ALERTA: {assunto}";
        await canal.EnviarAsync(contato.Principal, texto, cancellationToken);
        await canal.EnviarAsync(contato.Plantao, texto, cancellationToken);
    }
}
```

## Como testar
- Cada tipo de aviso com um canal fake que registra os envios: confere destinos e textos.
- Cada canal real, sozinho, no teste do adaptador; nenhuma combinação precisa de teste próprio.

```python
# test_avisos.py
from avisos import Alerta, Contato, Lembrete

CONTATO = Contato(principal="principal@exemplo.com", plantao="plantao@exemplo.com")


class CanalFake:
    def __init__(self) -> None:
        self.enviados: list[tuple[str, str]] = []

    def enviar(self, destino: str, texto: str) -> None:
        self.enviados.append((destino, texto))


def test_lembrete_envia_so_ao_contato_principal() -> None:
    canal = CanalFake()
    Lembrete(canal).notificar(CONTATO, "reunião")
    assert canal.enviados == [("principal@exemplo.com", "Lembrete: reunião")]


def test_alerta_envia_ao_principal_e_ao_plantao() -> None:
    canal = CanalFake()
    Alerta(canal).notificar(CONTATO, "falha no pagamento")
    destinos = [destino for destino, _ in canal.enviados]
    assert destinos == [CONTATO.principal, CONTATO.plantao]
```

```csharp
public class AvisosTests
{
    private static readonly Contato ContatoPadrao = new("principal@exemplo.com", "plantao@exemplo.com");

    private sealed class CanalFake : ICanal
    {
        public List<(string Destino, string Texto)> Enviados { get; } = [];

        public Task EnviarAsync(string destino, string texto, CancellationToken cancellationToken)
        {
            Enviados.Add((destino, texto));
            return Task.CompletedTask;
        }
    }

    [Fact]
    public async Task NotificarAsync_Lembrete_EnviaSoAoContatoPrincipal()
    {
        var canal = new CanalFake();

        await new Lembrete(canal).NotificarAsync(ContatoPadrao, "reunião", CancellationToken.None);

        Assert.Equal(new[] { ("principal@exemplo.com", "Lembrete: reunião") }, canal.Enviados);
    }

    [Fact]
    public async Task NotificarAsync_Alerta_EnviaAoPrincipalEAoPlantao()
    {
        var canal = new CanalFake();

        await new Alerta(canal).NotificarAsync(ContatoPadrao, "falha no pagamento", CancellationToken.None);

        Assert.Equal(
            new[] { ContatoPadrao.Principal, ContatoPadrao.Plantao },
            canal.Enviados.Select(envio => envio.Destino));
    }
}
```
