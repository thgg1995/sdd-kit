# `CATALOGO.md` da lib

O catálogo é o que o tech lead, o dev e o reviewer dos consumidores leem da lib — nunca o código dela. Precisa bastar para decidir "reusar, alterar ou criar".

## Formato
```
# Catálogo — <pacote> <versão>
Importação: `from <pacote> import <módulo>`. Todas as funções que chamam a AWS recebem `client=` (ou `session=`) por nome.

## <módulo> — <uma linha: para que serve>
- `nome(arg: tipo, *, opcional: tipo = default) -> retorno` — o que faz; limites tratados; o que levanta ou devolve em falha. desde 0.2
- `Classe(campo: tipo, ...)` — dado de retorno. desde 0.2
- `antigo(...)` — obsoleto desde 0.4 → use `novo`.
```
- Uma linha por símbolo público, na ordem em que aparece no módulo.
- "Limites tratados" e "em falha" são obrigatórios para funções que chamam a AWS (ex.: "lotes de 10", "pagina até o fim", "devolve os ids que falharam", "levanta `ClientError`").
- Sem exemplos de uso longos: no máximo uma linha de exemplo por módulo, quando a assinatura não bastar.

## Exemplo
```
## sqs — envio e leitura em fila SQS
- `send_batch(queue_url: str, bodies: Sequence[str], *, client: SQSClient) -> list[SendFailure]` — envia em lotes de 10; devolve os itens recusados (`Failed`), sem retentar. desde 0.2
- `SendFailure(id: str, code: str)` — item recusado; `id` = posição em `bodies`. desde 0.2
- `approximate_count(queue_url: str, *, client: SQSClient) -> int` — `ApproximateNumberOfMessages`; levanta `ClientError`. desde 0.2
```

## Como buscar
- Por serviço e operação: `grep -n -i "sqs\|send" <lib>/CATALOGO.md`, depois leia só a seção do módulo.
- Não achou → procure pelo efeito ("lote", "pagina", "cache", "assume") antes de decidir por "criar".

## Teste de sincronia (na lib)
Garante que o catálogo e o `__all__` não divergem. Coloque em `tests/test_catalogo.py`:
```python
import re
from pathlib import Path

import <pacote>

CATALOGO = Path(__file__).resolve().parents[1] / "CATALOGO.md"


def test_catalogo_cobre_api_publica() -> None:
    texto = CATALOGO.read_text(encoding="utf-8")
    documentados = set(re.findall(r"^- `(\w+)\(", texto, flags=re.MULTILINE))
    publicos = {n for n in <pacote>.__all__ if not n.startswith("_")}
    assert publicos <= documentados, f"faltam no CATALOGO.md: {sorted(publicos - documentados)}"
```
- Pressupõe que o `__init__.py` reexporta cada símbolo público em `__all__`. Se a lib exporta por módulo (`from <pacote> import sqs`), troque `__all__` pela união dos `__all__` de cada módulo.
