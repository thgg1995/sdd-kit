# Job agendado, em lote ou de linha de comando

Aplica-se quando o repositório roda por agendamento, em lote ou por linha de comando.

## Onde fica cada parte
| Parte | Onde |
|---|---|
| leitura dos argumentos ou do evento de agendamento; resultado da execução (código de saída, status) | adaptador de entrada (`entrypoints/jobs/`; no nível 1, o módulo de entrada) |
| seleção e processamento dos itens | caso de uso |
| leitura paginada da origem e escrita no destino | portas, implementadas em `infrastructure/` |
| trava de execução única, quando o plano proíbe execuções simultâneas | porta chamada pelo caso de uso no início |
| checkpoint, quando o plano exige retomar de onde parou | porta gravada pelo caso de uso a cada lote |

## Regras
- O caso de uso devolve um resumo (processados, ignorados, falhas); o adaptador o registra e o converte no resultado da execução.
- Falha de um item: seguir ou abortar é decisão do plano; ao seguir, o item entra no resumo de falhas e nunca é descartado em silêncio.
- Rodar de novo sobre os mesmos dados não duplica efeito: escrita idempotente pela chave do item (§7).
