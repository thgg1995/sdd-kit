# Producer de eventos

Aplica-se quando o repositório publica eventos. O *como* (outbox, chave, schema) está na skill da tecnologia (ex.: `kafka-messaging`); aqui fica a camada de cada parte.

## Onde fica cada parte
| Parte | Onde |
|---|---|
| decisão de publicar e conteúdo do evento, em tipo da aplicação | caso de uso |
| porta de publicação | application (junto do caso de uso ou em `application/ports`) |
| conversão para o payload do contrato e validação do schema (§12) | implementação da porta, em `infrastructure/` |
| chave da mensagem e headers (id do evento, correlação) | implementação da porta, a partir de campos do evento definidos no contrato (§13, §24) |
| gravação na outbox (§14) | implementação da porta, na transação aberta pelo caso de uso |
| publicador da outbox (lê pendentes, publica, marca) | componente de `infrastructure/`, iniciado por um composition root próprio (processo, job ou função); sem caso de uso, porque não tem regra |

## Evento ligado a uma escrita no banco (§14)
1. O caso de uso abre a transação (porta de unidade de trabalho), grava o efeito de negócio e chama a porta de publicação.
2. A implementação da porta grava o evento na outbox, na mesma transação, em vez de publicar no broker.
3. O publicador da outbox, ou o CDC, envia ao broker fora do caso de uso.
- Evento sem escrita no banco ligada a ele: a implementação da porta publica direto no broker.
