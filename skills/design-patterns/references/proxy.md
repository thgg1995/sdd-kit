# Proxy

Aplica-se quando uma dependência é cara de criar (carrega modelo, fontes ou certificados, abre conexão) e só parte das execuções a usa, mas é criada sempre na inicialização; ou quando o acesso à implementação real precisa ser controlado sem que quem chama perceba.

## Quando não usar
- Objeto barato de criar: crie direto (sintoma de excesso no `SKILL.md`).
- Cache, métrica ou retentativa em volta da porta: é Decorator (`references/decorator.md`), mesma estrutura com outro objetivo.
- Cliente remoto gerado (HTTP, gRPC): é o próprio adaptador de saída (`clean-architecture`), não um proxy a escrever.

## Forma
- Uma classe que implementa a mesma porta e guarda uma função que cria a implementação real; cria na primeira chamada e reaproveita nas seguintes.
- Criação segura entre threads: `Lazy<T>` no .NET (seguro por padrão); trava (`threading.Lock`) no Python.
- O composition root entrega o proxy no lugar da implementação real (`GeradorDePdfSobDemanda(lambda: GeradorDePdfReal(config.modelos))`); o caso de uso não muda.
- Fica em infrastructure, junto da implementação real.

## Python
```python
# pdf.py
import threading
from collections.abc import Callable
from typing import Protocol


class GeradorDePdf(Protocol):
    def gerar(self, html: str) -> bytes: ...


class GeradorDePdfSobDemanda:
    """Proxy: cria o gerador real, caro de iniciar, só na primeira chamada."""

    def __init__(self, criar: Callable[[], GeradorDePdf]) -> None:
        self._criar = criar
        self._real: GeradorDePdf | None = None
        self._trava = threading.Lock()

    def gerar(self, html: str) -> bytes:
        return self._obter_real().gerar(html)

    def _obter_real(self) -> GeradorDePdf:
        with self._trava:
            if self._real is None:
                self._real = self._criar()
            return self._real
```

## .NET
```csharp
public interface IGeradorDePdf
{
    byte[] Gerar(string html);
}

// Proxy: cria o gerador real, caro de iniciar, só na primeira chamada.
public sealed class GeradorDePdfSobDemanda(Func<IGeradorDePdf> criar) : IGeradorDePdf
{
    private readonly Lazy<IGeradorDePdf> _real = new(criar);

    public byte[] Gerar(string html) => _real.Value.Gerar(html);
}
```

## Como testar
- Com uma fábrica fake que conta as criações: nada é criado antes do primeiro uso, e duas chamadas criam uma vez só.
- A implementação real é testada sem o proxy.

```python
# test_pdf.py
from pdf import GeradorDePdfSobDemanda


class GeradorFake:
    def gerar(self, html: str) -> bytes:
        return html.encode()


class Contador:
    def __init__(self) -> None:
        self.criacoes = 0

    def criar(self) -> GeradorFake:
        self.criacoes += 1
        return GeradorFake()


def test_proxy_nao_cria_o_real_antes_do_primeiro_uso() -> None:
    contador = Contador()
    GeradorDePdfSobDemanda(contador.criar)
    assert contador.criacoes == 0


def test_proxy_cria_o_real_uma_vez_e_reaproveita() -> None:
    contador = Contador()
    gerador = GeradorDePdfSobDemanda(contador.criar)
    gerador.gerar("<p>a</p>")
    assert gerador.gerar("<p>b</p>") == b"<p>b</p>"
    assert contador.criacoes == 1
```

```csharp
public class GeradorDePdfSobDemandaTests
{
    private sealed class GeradorFake : IGeradorDePdf
    {
        public byte[] Gerar(string html) => System.Text.Encoding.UTF8.GetBytes(html);
    }

    [Fact]
    public void Construtor_SemUso_NaoCriaOReal()
    {
        var criacoes = 0;

        _ = new GeradorDePdfSobDemanda(() => { criacoes++; return new GeradorFake(); });

        Assert.Equal(0, criacoes);
    }

    [Fact]
    public void Gerar_DuasChamadas_CriaORealUmaVez()
    {
        var criacoes = 0;
        var gerador = new GeradorDePdfSobDemanda(() => { criacoes++; return new GeradorFake(); });

        gerador.Gerar("<p>a</p>");
        gerador.Gerar("<p>b</p>");

        Assert.Equal(1, criacoes);
    }
}
```
