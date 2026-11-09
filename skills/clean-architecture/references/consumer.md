# Consumer de mensagens

Aplica-se quando o repositório consome mensagens de fila, tópico ou stream. O *como* (deduplicação, retentativas, DLQ, confirmação) está na skill da tecnologia (ex.: `kafka-messaging`; SQS na `aws-infra`); aqui fica a camada de cada parte.

## Nível
- Um tipo de mensagem com uma regra: nível 1.
- Vários tipos com regras distintas: nível 2, um caso de uso por tipo.

## Onde fica cada parte
| Parte | Onde |
|---|---|
| handler, um por tipo de mensagem | `entrypoints/consumers/` |
| desserialização e validação do schema (§12) | handler, antes de chamar o caso de uso |
| retentativa, envio à DLQ (§11) e confirmação (offset, exclusão da fila) | handler; o caso de uso não conhece offset, partição nem DLQ |
| deduplicação pelo id da mensagem (§10) | caso de uso, por uma porta gravada na mesma transação do efeito de negócio |
| efeito de negócio | caso de uso |

## Fluxo de uma mensagem
| Situação | Caminho |
|---|---|
| mensagem inválida (desserialização, schema) | falha permanente |
| sucesso, ou id já processado | confirma |
| falha transitória (tipo de erro de infraestrutura) | retentativa; esgotou → falha permanente |
| erro de negócio | o tratamento que o plano define (ex.: evento de rejeição); sem definição, falha permanente |
- Falha permanente: a mensagem vai para a DLQ sem novas tentativas quando a tecnologia permite (Kafka: publica na DLQ e confirma, conforme a `kafka-messaging`); onde só há redrive (SQS), ela chega à DLQ pelo redrive.
- Lote com falha parcial: o handler devolve à plataforma só as mensagens que falharam, pelo mecanismo dela (ex.: falha por item no SQS com Lambda).
