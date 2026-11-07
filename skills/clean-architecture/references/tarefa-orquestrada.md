# Tarefa de orquestrador de fluxo

Aplica-se quando o código é uma tarefa chamada por um orquestrador de fluxo (ex.: Step Functions). Sequência, retentativas e `Catch` ficam na definição do fluxo (skill do runtime, ex.: `aws-serverless`); aqui fica o código da tarefa.

## Nível
- A tarefa só mapeia dados entre estados: nível 0, com a integração direta do orquestrador (sem código) quando a skill do runtime a oferece.
- Uma operação de negócio: nível 1, o caso típico.
- Várias tarefas no mesmo repositório: nível 2, com um ponto de entrada por tarefa em `entrypoints/tasks/`.

## Regras
- O adaptador converte o estado recebido para a entrada do caso de uso e devolve só os campos que os estados seguintes usam (limite de payload na skill do runtime).
- Erro de negócio: o adaptador o converte no nome de erro exato que o `Catch` do fluxo espera; o nome faz parte do contrato do fluxo.
- Falha transitória: sobe com nome próprio, para o `Retry` do fluxo.
- A tarefa não repete a própria execução nem chama a tarefa seguinte: retentativa e sequência são do fluxo. A retentativa do SDK numa chamada idempotente continua permitida (skill do runtime).
- A tarefa não guarda estado entre execuções; o estado do processo é o do fluxo.
