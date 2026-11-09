# Limites de SQS e DynamoDB

Ler na triagem e quando o tech lead desenha contratos ou fluxos que passam por fila SQS ou tabela DynamoDB. Compare o pior caso que o contrato permite com o limite e registre como manda o papel do tech lead (`Limites prévios` na triagem, `Limites verificados` no desenho). Limites de Lambda, Step Functions e agendamento: `aws-serverless`, `references/limites.md`.

Marcas: **Medido** = observado em teste neste kit; **Documentado** = valor conhecido da documentação da AWS, que muda com o tempo: confirme na documentação vigente antes de usá-lo como argumento.

| Serviço | Limite | O que acontece | Marca |
|---|---|---|---|
| SQS | `ReceiveMessage` devolve no máximo 10 mensagens; visibilidade até 12 h; retenção até 14 dias; contagens de atributos são aproximadas | lote > 10 exige mais leituras; contagem não serve de garantia exata | Documentado |
| DynamoDB | item até 400 KB; números com até 38 dígitos de precisão | item grande ou número longo vira erro na gravação | Documentado |
