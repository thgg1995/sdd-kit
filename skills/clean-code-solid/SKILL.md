---
name: clean-code-solid
description: Regras de escrita e de desenho de código para qualquer linguagem de aplicação — Clean Code (nomes, funções, classes, objetos e dados, erros, comentários, simplicidade, concorrência), os cinco princípios SOLID e os limites que o linter mede (complexidade e parâmetros). Use quando o dev implementa ou o reviewer revisa código de aplicação, de back-end ou de front-end (não se aplica a IaC).
---

# Clean Code e SOLID

Complementa a skill da stack (linter, formatter e convenções da linguagem), a `unit-testing` (testes) e, no back-end, a `clean-architecture` (camadas e portas) e a `design-patterns` (padrões). O que já está nelas não se repete aqui: veja "Fora desta skill". Em conflito, vale a constitution.

## Limites medidos pelo linter (constitution §29)
- Complexidade ciclomática por função: até 10. <!-- TIME: ajustar -->
- Parâmetros por função: até 5. <!-- TIME: ajustar -->
- A skill da stack configura o linter com esses limites; acima deles, o build ganha um warning novo (§29). Limite que o linter da stack não mede: o reviewer confere no diff.
- Repositório novo: a configuração entra na tarefa que cria a estrutura do projeto. Repositório existente: só com tarefa explícita, porque o dev não muda configuração fora do escopo.
- Exceção: supressão na própria linha ou função, com o motivo escrito (formato na skill da stack). Supressão sem motivo conta como warning novo.

## Nomes
- Um termo de negócio, um nome: o mesmo identificador em código, contrato e testes, sem sinônimos (ex.: não misturar `cliente`, `customer` e `user` para a mesma entidade).
- Nome que é só uma palavra genérica é proibido: `data`, `info`, `obj`, `manager`, `helper`, `util`, `temp`. Diga o que é: `pedido_pendente`, `CalculadoraDeFrete`. Exceção: função genérica de infraestrutura cujo argumento é de fato qualquer dado (ex.: serializador).
- Classe com sufixo genérico (`Manager`, `Helper`, `Util`, `Processor`) esconde mais de uma responsabilidade: nomeie pelo que ela faz (`CalculadoraDeFrete`, não `FreteManager`).
- Abreviação só se for termo da spec ou convenção da linguagem (`i` em laço, `id`, `ctx`).
- Booleano nomeado como afirmação: `is_active`, `HasItems`, `deve_reprocessar`.

## Funções
- Uma responsabilidade: se a descrição precisa de "e", divida.
- Parâmetro booleano que escolhe entre dois comportamentos é proibido: crie duas funções ou receba um valor enumerado.
- Função que devolve dado não altera estado; função que altera estado não devolve o dado consultado. Exceção: operação atômica que precisa dos dois (ex.: retirar da fila e devolver o item), com o nome dizendo os dois.
- Nada de parâmetro de saída: devolva o resultado em vez de alterar o argumento recebido.
- Aninhamento de blocos até 3 níveis; passou disso, use retorno antecipado ou extraia uma função.

## Classes e módulos
- Coesão: os métodos de uma classe usam os mesmos campos. Métodos que usam grupos separados de campos são duas classes: divida.
- Uma classe muda por um motivo só: alterada no mesmo diff por dois assuntos diferentes (ex.: regra de preço e formato de exportação), separe os assuntos.
- Composição em vez de herança. Herança só para as variações fechadas de um tipo (ex.: `Cpf` e `Cnpj` como `Documento`) ou quando o framework a exige (ex.: `ControllerBase`, `BaseModel`). Para reaproveitar código, receba a parte que varia (função ou objeto).

## Objetos e dados
- Diga, não pergunte: regra sobre os dados de um objeto fica no próprio objeto (`pedido.pode_cancelar()`), não em quem o usa (`if pedido.status == ... and pedido.enviado_em is None`).
- Lei de Deméter: não navegue por objetos alheios para decidir (`pedido.cliente.endereco.cidade.nome`); peça a quem tem o dado ou receba o dado pronto. Não vale para estrutura de dados (DTO, record de contrato), API fluente e consulta encadeada (LINQ, builders).
- Estrutura de dados só carrega dados, sem regra; objeto com regra não expõe os campos para outro decidir por ele.
- Valor e dado são imutáveis (`@dataclass(frozen=True)`, `record`, `readonly`); só a entidade muda, e por métodos com regra.

## Erros
- Todo bloco de captura relança, converte em erro da aplicação ou executa o tratamento que o plano define, registrando com contexto. Bloco vazio, ou que só registra e segue sem o plano prever, é proibido.
- Captura genérica (`Exception`, `except Exception`) só na borda da aplicação: adaptador de entrada ou composition root; no front-end, error boundary ou tratador global.
- Erro não é sinalizado por `null`/`None`, código numérico ou texto: use exceção ou o tipo de resultado da linguagem.
- Exceção com contexto: a mensagem diz o que se tentava e com quais identificadores; nunca dado pessoal ou segredo (§19).
- Parâmetro só aceita `None`/`null` quando a ausência faz parte da regra e o tipo declara isso (`X | None`, `X?`). Para "use o padrão", valor padrão ou outra função.

## Comentários
- O comentário explica o porquê (decisão, restrição externa, requisito); o que o código faz está nos nomes.
- Código comentado é proibido: o histórico fica no git.
- `TODO` só com referência a tarefa ou issue.

## Simplicidade
- Nada para o futuro: parâmetro, método, classe ou configuração que esta tarefa não usa não entra; função nova que nada chama sai antes do commit.
- Número ou texto com significado de negócio vira constante nomeada; no front-end, cor, espaçamento e tamanho vêm de token de design. Exceção: `0`, `1`, `-1` e índices.
- Lógica repetida é extraída na terceira ocorrência. Trechos parecidos que mudam por motivos diferentes (ex.: regras de dois casos de uso) ficam separados.

## Concorrência
- Objeto compartilhado entre execuções concorrentes (tempo de vida singleton, variável de módulo) não guarda estado mutável. Quando precisa (cache, contador), usa estrutura concorrente ou trava (`ConcurrentDictionary`, `lock`, `threading.Lock`), com o porquê em comentário.
- Bloqueio em código assíncrono: regra da skill da stack (§30).

## SOLID
| Princípio | Regra verificável | No back-end, também |
|---|---|---|
| **S**: um motivo para mudar | uma responsabilidade por função e por classe, com coesão (Funções; Classes e módulos) | um caso de uso por pasta (`clean-architecture`) |
| **O**: aberto para extensão, fechado para modificação | ponto de extensão (interface, registro de variações) só com duas ou mais variações reais; com ele, variação nova é código novo, sem editar as existentes | a forma do ponto de extensão: `design-patterns`. Porta de I/O com uma implementação é outro caso (`clean-architecture`) |
| **L**: substituição | quem implementa uma interface cumpre o contrato inteiro: não lança "não implementado" ou "não suportado", não exige mais na entrada nem devolve menos na saída, sinaliza os mesmos erros. Precisou de "não suportado": a interface está grande (I) ou a herança está errada | o fake de teste cumpre o contrato do real (suíte de contrato: `design-patterns`, `references/repository.md`) |
| **I**: interfaces segregadas | interface que junta grupos de operações usados por clientes diferentes: divida por cliente. Exceção: porta de repositório por entidade. Função recebe o dado de que precisa, não o objeto inteiro | portas com as operações dos casos de uso (`clean-architecture`); repositório: `design-patterns`, `references/repository.md` |
| **D**: inversão de dependência | dependências entram pelo construtor ou por parâmetro; código de regra não cria as próprias dependências de I/O | regra de dependência entre camadas (§32) e composition root (`clean-architecture`) |

## Fora desta skill
| Assunto do Clean Code | Onde está |
|---|---|
| Formatação | formatter da stack (ex.: `ruff format`); estilo que ele resolve não é achado de review (`code-review`) |
| Testes limpos (um comportamento por teste, sem dependência de ordem, relógio ou rede) | `unit-testing` |
| Fronteira com código de terceiros | adaptador (`clean-architecture`; `design-patterns`, `references/adapter.md`) |
| Sistemas: separar a construção do uso | composition root (`clean-architecture`) |
| Tipos de erro por quem trata (negócio × falha transitória) | `clean-architecture`, regras dos níveis 1 a 3 |

## Classificação no review
- Limite medido estourado ou supressão sem motivo: viola o §29 (`bloqueante`).
- Demais regras: desvio de skill (`sugestão`), salvo quando também violam a constitution (ex.: mensagem descartada em silêncio, §11; dado sensível na mensagem de erro, §19) ou o Desenho técnico.

## Referências
Exemplos em Python e .NET; nas outras stacks, a forma equivalente com as convenções da skill da stack.
- `references/responsabilidade-unica.md` — ler quando uma classe ou módulo junta assuntos que mudam por motivos diferentes (regra, formato, I/O), ou o teste de uma regra precisa montar o formato ou o I/O de outro assunto.
- `references/aberto-fechado.md` — ler quando acrescentar uma variação ou regra exige editar o código das existentes, ou quando se cogita um ponto de extensão.
- `references/substituicao-de-liskov.md` — ler quando uma implementação lança "não implementado" ou "não suportado", quem chama testa o tipo concreto, ou implementações da mesma interface diferem no que aceitam, no que devolvem ou nos erros que lançam.
- `references/segregacao-de-interfaces.md` — ler quando um cliente depende de interface com operações que não usa, um fake de teste tem métodos vazios, ou uma função recebe um objeto inteiro para usar um ou dois campos.
- `references/inversao-de-dependencia.md` — ler quando código de regra cria cliente ou conexão, chama relógio ou gerador de id direto, ou lê configuração, ou quando o teste precisa de `patch` para trocar uma dependência.
