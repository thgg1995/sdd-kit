# Facade

Aplica-se quando o código de negócio repete a sequência de chamadas de uma biblioteca ou subsistema (abrir, configurar, escrever, fechar) para uma operação que o negócio vê como uma só, ou quando o plano pede uma operação que exige vários passos de uma API de baixo nível.

## Quando não usar
- A biblioteca já oferece a operação numa chamada: use-a, sem camada a mais.
- A fachada só repassa uma chamada: remova (sintoma de excesso no `SKILL.md`).

## Forma
- Uma operação de alto nível, na língua da aplicação (`empacotar(arquivos)`), que concentra os passos da API de baixo nível.
- Sobre biblioteca com I/O (SDK, rede, disco), a fachada é o adaptador de saída: implementa uma porta e mora em infrastructure. Sem I/O (ex.: compressão em memória, abaixo), é uma função ou classe concreta, sem interface.
- Recursos abertos pela sequência (streams, conexões) são fechados dentro da fachada, inclusive no erro (`with` no Python, `using` no C#).
- Regras do time: `clean-architecture` (portas e adaptadores).

## Python
```python
# empacotamento.py
import io
import zipfile
from collections.abc import Mapping


def empacotar(arquivos: Mapping[str, bytes]) -> bytes:
    """Fachada: um zip em memória com os arquivos dados, numa chamada."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as pacote:
        for nome, conteudo in arquivos.items():
            pacote.writestr(nome, conteudo)
    return buffer.getvalue()
```

## .NET
```csharp
using System.IO.Compression;

public static class Empacotamento
{
    // Fachada: um zip em memória com os arquivos dados, numa chamada.
    public static byte[] Empacotar(IReadOnlyDictionary<string, byte[]> arquivos)
    {
        using var buffer = new MemoryStream();
        using (var pacote = new ZipArchive(buffer, ZipArchiveMode.Create, leaveOpen: true))
        {
            foreach (var (nome, conteudo) in arquivos)
            {
                var entrada = pacote.CreateEntry(nome, CompressionLevel.Optimal);
                using var destino = entrada.Open();
                destino.Write(conteudo);
            }
        }

        return buffer.ToArray();
    }
}
```
O `ZipArchive` só grava o índice do arquivo ao ser fechado; por isso ele fica num bloco `using` próprio, antes do `ToArray()`.

## Como testar
- A operação de alto nível com entradas reais e a verificação do resultado pela própria biblioteca (abrir o zip e conferir os arquivos).
- Fachada sobre I/O real (SDK, rede): o caso de uso usa um fake da porta; a fachada vai para o QA de integração.

```python
# test_empacotamento.py
import io
import zipfile

from empacotamento import empacotar


def test_empacotar_gera_zip_com_os_arquivos() -> None:
    pacote = empacotar({"a.txt": b"um", "b.txt": b"dois"})
    with zipfile.ZipFile(io.BytesIO(pacote)) as lido:
        assert sorted(lido.namelist()) == ["a.txt", "b.txt"]
        assert lido.read("b.txt") == b"dois"
```

```csharp
using System.IO.Compression;

public class EmpacotamentoTests
{
    [Fact]
    public void Empacotar_DoisArquivos_GeraZipComOsDois()
    {
        var pacote = Empacotamento.Empacotar(new Dictionary<string, byte[]>
        {
            ["a.txt"] = "um"u8.ToArray(),
            ["b.txt"] = "dois"u8.ToArray(),
        });

        using var lido = new ZipArchive(new MemoryStream(pacote), ZipArchiveMode.Read);
        Assert.Equal(new[] { "a.txt", "b.txt" }, lido.Entries.Select(entrada => entrada.FullName).Order());
    }
}
```
