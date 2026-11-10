# Medir o consumo de tokens

## O que medir
- O consumo é a soma do uso de cada chamada ao modelo, em quatro tipos: entrada nova, escrita de cache, leitura de cache e saída. Cada tipo tem preço diferente; compare os quatro, não só o total.
- O `tokens` que o orquestrador registra no `eventos.jsonl` (vindo da notificação de conclusão do subagente) é o contexto da última chamada, não o consumo: fica uma ordem de grandeza abaixo do real e não inclui o orquestrador.
- Não confunda caracteres com tokens, nem prometa percentual de economia sem medir antes e depois.

## Como medir
`python .agents/bin/consumo.py <f>` lê os transcritos da ferramenta e grava `specs/<f>/reports/consumo.md`; no kit, `python bin/consumo.py <f> --raiz <workspace> --saida <arquivo>`. Rode fora do agente; dentro dele, só a linha de resumo entra no contexto.
- **Claude Code:** `~/.claude/projects/<raiz do workspace, com todo caractere que não é letra nem número trocado por "-">/`. A sessão do orquestrador é o `<id>.jsonl`; os subagentes ficam em `<id>/subagents/`, com o papel na linha `Papel:` do prompt de delegação.
- **Codex:** `~/.codex/sessions/AAAA/MM/DD/rollout-*.jsonl`, filtrados pelo `cwd` da sessão. O papel sai do `agent_path` (`/root/techlead_1`); as sessões `guardian_review` (aprovação de permissões) aparecem como `guardian`.
- **Recorte:** a sessão pode ter outra conversa antes ou depois da execução. O fim da feature é o evento CONCLUÍDO do `eventos.jsonl`. O relatório avisa e sugere o valor; recorte com `--desde` no pedido que iniciou a execução e com `--ate` logo depois do CONCLUÍDO (hora local).

## Métricas do relatório
São indícios para investigar, não portões: confira no transcrito antes de concluir. Uma leitura conta como repetida mesmo quando outro agente ou um script (ex.: o `fluxo.py`, no `status.md`) alterou o arquivo no meio.

| Métrica | O que conta | Regra da skill |
|---|---|---|
| ferramentas por chamada | chamadas de ferramenta ÷ chamadas ao modelo | chamadas agrupadas |
| esperas | chamadas com `wait_agent`, `wait`, `sleep` ou consulta a processo em segundo plano | esperar a notificação |
| comandos repetidos | execuções de um mesmo comando repetido 3 vezes ou mais, fora o registro no `fluxo.py` | mudar a hipótese antes de repetir |
| leituras repetidas | mesmo arquivo e mesmo intervalo lidos de novo sem alteração do próprio agente no meio, pela ferramenta de leitura ou por `cat`, `type` e `Get-Content` | não reler |
| leituras inteiras | arquivo com mais de 200 linhas lido sem intervalo | ler por trecho |
| maior resultado e resultados grandes | o maior resultado de ferramenta; os acima de ~3 mil tokens (~100 linhas) | saída curta |
| reescritas | arquivo já lido e depois reescrito inteiro (n/d no Codex, que altera por patch) | escrever por trecho |
| só registro | chamadas do orquestrador cujo único efeito é registrar no `fluxo.py` | registro junto com a ação seguinte |
| parágrafos repetidos | parágrafos com 120 caracteres ou mais copiados entre artefatos da feature | citar ID e caminho |
| resultados mais caros | tokens do resultado × chamadas seguintes que o releem | mostra onde o contexto pesou |

## Qualidade
O relatório põe ao lado do consumo os indicadores de qualidade da execução, lidos do `eventos.jsonl` e dos relatórios da feature:
- rodadas do tech lead e paradas para o humano;
- resultado do analyze e passagens do converge até convergir;
- rodadas de QA, com as linhas `Resultado:` e `Critérios de aceite:` do `qa.md`;
- achados `[handoff]` no review;
- por repositório, as execuções do dev (cada uma depois da primeira é ciclo de correção ou de convergência) e as revisões reprovadas.

## Comparar versões do kit
- Mesma feature de referência, mesma ferramenta e mesmo modelo, 2 a 3 execuções por versão: separa o efeito da mudança da variação entre execuções.
- Critério de aceite: consumo menor e nenhum indicador de qualidade pior que a faixa da linha de base. Um corte que economiza tokens mas gera um ciclo de correção a mais custa mais.
- Se um indicador piorar, a métrica de cada regra mostra qual mudança causou: reverta só ela.
- Recorte cada execução do pedido que a iniciou até o CONCLUÍDO, para não somar outras conversas.
