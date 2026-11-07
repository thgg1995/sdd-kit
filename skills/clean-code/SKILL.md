---
name: clean-code
description: Regras de escrita de código para qualquer linguagem de aplicação — nomes, funções, tratamento de erro, comentários, constantes e duplicação — e os limites que o linter mede (complexidade e parâmetros). Use quando o dev implementa ou o reviewer revisa código de aplicação, de back-end ou de front-end (não se aplica a IaC).
---

# Clean Code

Complementa a skill da stack (configuração do linter e convenções da linguagem), a `unit-testing` (testes) e, no back-end, a `clean-architecture` (camadas). Em conflito, vale a constitution.

## Limites medidos pelo linter (constitution §29)
- Complexidade ciclomática por função: até 10. <!-- TIME: ajustar -->
- Parâmetros por função: até 5. <!-- TIME: ajustar -->
- A skill da stack configura o linter com esses limites; acima deles, o build ganha um warning novo (§29). Limite que o linter da stack não mede: o reviewer confere no diff.
- Repositório novo: a configuração entra na tarefa que cria a estrutura do projeto. Repositório existente: só com tarefa explícita, porque o dev não muda configuração fora do escopo.
- Exceção: supressão na própria linha ou função, com o motivo escrito (formato na skill da stack). Supressão sem motivo conta como warning novo.

## Nomes
- Um termo de negócio, um nome: o mesmo identificador em código, contrato e testes, sem sinônimos (ex.: não misturar `cliente`, `customer` e `user` para a mesma entidade).
- Nome que é só uma palavra genérica é proibido: `data`, `info`, `obj`, `manager`, `helper`, `util`, `temp`. Diga o que é: `pedido_pendente`, `CalculadoraDeFrete`. Exceção: função genérica de infraestrutura cujo argumento é de fato qualquer dado (ex.: serializador).
- Abreviação só se for termo da spec ou convenção da linguagem (`i` em laço, `id`, `ctx`).
- Booleano nomeado como afirmação: `is_active`, `HasItems`, `deve_reprocessar`.

## Funções
- Uma responsabilidade: se a descrição precisa de "e", divida.
- Parâmetro booleano que escolhe entre dois comportamentos é proibido: crie duas funções ou receba um valor enumerado.
- Função que devolve dado não altera estado; função que altera estado não devolve o dado consultado. Exceção: operação atômica que precisa dos dois (ex.: retirar da fila e devolver o item), com o nome dizendo os dois.
- Nada de parâmetro de saída: devolva o resultado em vez de alterar o argumento recebido.
- Aninhamento de blocos até 3 níveis; passou disso, use retorno antecipado ou extraia uma função.

## Erros
- Todo bloco de captura relança, converte em erro da aplicação ou executa o tratamento que o plano define, registrando com contexto. Bloco vazio, ou que só registra e segue sem o plano prever, é proibido.
- Captura genérica (`Exception`, `except Exception`) só na borda da aplicação: adaptador de entrada ou composition root; no front-end, error boundary ou tratador global.
- Erro não é sinalizado por `null`/`None`, código numérico ou texto: use exceção ou o tipo de resultado da linguagem.

## Comentários
- O comentário explica o porquê (decisão, restrição externa, requisito); o que o código faz está nos nomes.
- Código comentado é proibido: o histórico fica no git.
- `TODO` só com referência a tarefa ou issue.

## Constantes e duplicação
- Número ou texto com significado de negócio vira constante nomeada; no front-end, cor, espaçamento e tamanho vêm de token de design. Exceção: `0`, `1`, `-1` e índices.
- Lógica repetida é extraída na terceira ocorrência. Trechos parecidos que mudam por motivos diferentes (ex.: regras de dois casos de uso) ficam separados.

## Classificação no review
- Limite medido estourado ou supressão sem motivo: viola o §29 (`bloqueante`).
- Demais regras: desvio de skill (`sugestão`), salvo quando também violam a constitution (ex.: mensagem descartada em silêncio, §11).
