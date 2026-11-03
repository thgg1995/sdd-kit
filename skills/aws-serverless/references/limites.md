# Limites a conferir antes de congelar contratos

Ler quando o tech lead desenha contratos ou fluxos entre serviços AWS. Para cada fluxo de dados: calcule o **pior caso** (maior mensagem × quantidade por leitura × expansão por escape JSON + metadados) e compare com o limite. Estourou → ajuste o contrato (limite de tamanho, formato, outro serviço), não aceite como "improvável". Registre em `research.md`, seção `Limites verificados`.

Marcas: **Medido** = observado em teste neste kit; **Documentado** = valor conhecido da documentação da AWS, que muda com o tempo: confirme na documentação vigente antes de usá-lo como argumento.

| Serviço | Limite | O que acontece | Marca |
|---|---|---|---|
| Step Functions | 256 KiB por entrada/saída de estado e da execução | `States.DataLimitExceeded`; um lote do `ReceiveMessage` (10 corpos, escapes JSON, metadados) estoura antes do `Map` | Medido: 10 mensagens de 262144 B estouraram; 12288 B por mensagem cabem. Contrato com `MaximumMessageSize` alto exige limite menor na fila |
| JSONata no ASL | `$parse` e a aritmética usam ponto flutuante de 64 bits | inteiros ≥ 2^53 e números com mais de 15 dígitos significativos chegam arredondados, sem erro | Medido no LocalStack (o motor porta o jsonata-js); confirmar na AWS. Decisão do plano: recusar o número ou exigi-lo como texto |
| Step Functions EXPRESS | duração máxima de 5 minutos; histórico só em logs; execução assíncrona é pelo menos uma vez | trabalho longo ou que não tolera repetição precisa de STANDARD | Documentado |
| Step Functions STANDARD | histórico de até 25.000 eventos por execução | `Map` grande estoura o histórico; divida o lote | Documentado |
| SQS | `ReceiveMessage` devolve no máximo 10 mensagens; visibilidade até 12 h; retenção até 14 dias; contagens de atributos são aproximadas | lote > 10 exige mais leituras; contagem não serve de garantia exata | Documentado |
| Lambda | timeout até 15 min; payload síncrono de 6 MB; o payload assíncrono tem limite próprio que mudou ao longo do tempo | confira o valor vigente se o evento carrega dados | Documentado |
| DynamoDB | item até 400 KB; números com até 38 dígitos de precisão | item grande ou número longo vira erro na gravação | Documentado |
| EventBridge Scheduler | resolução mínima de 1 minuto | `rate(30 seconds)` não existe | Documentado |

## Limite que o ambiente de teste não prova
Se o LocalStack (ou o teste unitário) não reproduz o limite, registre como lacuna em `reports/techlead.md` com o pior caso calculado, para ser validado na AWS real. Cálculo no papel não substitui teste, mas evita contrato que já nasce inviável.
