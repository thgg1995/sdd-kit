---
name: clean-architecture
description: Estrutura interna de aplicações de back-end pela Clean Architecture, proporcional à regra de negócio — níveis 0 a 3, camadas, regra de dependência e onde fica cada adaptador (API, consumer, producer, tarefa orquestrada, job). Use quando o repositório é de back-end (stack dotnet, python, node, go ou java) e a tarefa define o Desenho técnico ou cria ou altera módulo, caso de uso, ponto de entrada ou adaptador.
---

# Clean Architecture (back-end)

Complementa `architecture` (decisões entre serviços: posse dos dados e contratos) e a skill da stack (nomes concretos de arquivos, pastas e projetos). Em conflito, vale a constitution.

## Quando se aplica
- Só a aplicações de back-end: stack `dotnet`, `python`, `node`, `go` ou `java`. Front-end (`react`, `angular`, `vue`), IaC (`terraform`) e biblioteca (`kind: lib`): esta skill não se aplica.
- Precedência: `Desenho técnico` do plano > estrutura existente do repositório > esta skill.
- Repositório existente: siga a estrutura dele; esta skill orienta só o que a feature cria, encaixado nessa estrutura. Reestruturar exige tarefa explícita no plano.

## Camadas e regra de dependência (constitution §32)
Toda camada pode importar a biblioteca padrão da linguagem.

| Camada | Onde (nível 2+) | Contém | Pode importar | Nunca importa |
|---|---|---|---|---|
| domain | `domain/` | regras usadas por mais de um caso de uso; no nível 3, o modelo de domínio | — | as outras camadas; framework, SDK, driver |
| application | `application/<caso_de_uso>/` e `application/ports` | casos de uso, as regras puras de cada um e as portas | domain | entrypoints, infrastructure; framework, SDK, driver |
| entrypoints | `entrypoints/<papel>/` (`http`, `consumers`, `tasks`, `jobs`) | adaptadores de entrada | application, domain e a biblioteca do próprio transporte | infrastructure |
| infrastructure | `infrastructure/` | adaptadores de saída: implementações das portas (banco, fila, HTTP, SDK) | application, domain, SDKs e drivers | entrypoints |
| composition root | ponto de entrada do processo (nome na skill da stack) | lê a configuração, cria os adaptadores e os entrega aos casos de uso | todas | — |

- Biblioteca sem I/O (validação, datas, dinheiro) em domain ou application: só se listada em `Padrões` do Desenho técnico.
- Lib compartilhada (ex.: `python-lib`): função que faz I/O só em infrastructure ou no composition root (no nível 1, no módulo de adaptadores); utilitário sem I/O, em qualquer camada.
- Caso de uso não importa outro caso de uso; regra usada por dois ou mais vai para `domain/`.

## Níveis
O tech lead escolhe o nível pelo critério e o registra no Desenho técnico; na dúvida entre dois, use o menor. Subir de nível exige o critério cumprido e a mudança registrada no Desenho técnico.

| Nível | Critério (no plano do repositório) | Estrutura |
|---|---|---|
| 0 — sem regra | nenhuma regra de negócio: só valida formato, converte e repassa | integração direta da plataforma, quando a skill da stack ou do runtime a oferece; senão, o adaptador de entrada chama o de saída. Sem application nem domain; a tabela de camadas não se aplica |
| 1 — um caso de uso | uma única operação de negócio | três módulos, sem pastas por camada: entrada (adaptador e composition root), regra (caso de uso, regras puras e portas) e adaptadores de saída |
| 2 — serviço | duas ou mais operações de negócio | as pastas da tabela de camadas; `domain/` só se houver regra compartilhada |
| 3 — domínio rico | entidade com estados e regras que dois ou mais casos de uso precisam preservar | nível 2 com modelo de domínio (`references/dominio-rico.md`); fronteira imposta pela linguagem quando a skill da stack a definir |

## Regras dos níveis 1 a 3 (constitution §32)
1. **Adaptador de entrada**: converte a entrada para os tipos da aplicação, chama um caso de uso e converte o resultado ou o erro para o transporte. Nenhuma decisão de negócio nele. Leitura sem regra: chama a porta de leitura direto, sem caso de uso que só repassa.
2. **Tipos**: o caso de uso recebe e devolve tipos da aplicação, nunca objetos do transporte ou do framework (requisição HTTP, evento bruto do runtime, mensagem do broker, contexto do framework). Tipos do contrato (request, response, payload de evento) ficam no adaptador que fala aquele contrato.
3. **Erros**: erro de negócio tem tipo próprio, declarado em application ou domain; falha transitória de I/O sobe do adaptador de saída com outro tipo. O adaptador de entrada traduz cada um para o transporte (status e corpo de erro, retentativa, DLQ, erro nomeado do fluxo). O caso de uso nunca usa tipo de erro do framework.
4. **Portas**: só para I/O e não determinismo (banco, fila, HTTP, SDK, arquivo, relógio, gerador de id), com as operações que os casos de uso usam. Declarada junto do caso de uso que a usa (no nível 1, no módulo de regra) ou em `application/ports` quando mais de um usa; implementada em infrastructure.
5. **Composition root**: um por ponto de entrada do processo; único lugar que lê configuração e instancia adaptadores. O caso de uso nunca instancia adaptador nem lê variável de ambiente.
6. **Transação**: delimitada pelo caso de uso, por uma porta de unidade de trabalho ou por um método de porta que grava tudo junto. É assim que a deduplicação e a outbox entram na transação do efeito de negócio.

## Testes
- Caso de uso e regras: teste unitário com fakes das portas (`unit-testing`), sem framework, servidor, SDK nem rede.
- Adaptador de entrada: teste da conversão; entrada válida chama o caso de uso com os tipos certos, e cada erro vira a resposta do contrato.
- Adaptador de saída contra a dependência real: QA de integração (`qa-integration`).

## Proibido
- Regra de negócio em adaptador de entrada ou de saída (§32).
- domain ou application importando framework, SDK, driver ou tipo de transporte (§32).
- Interface com uma única implementação e sem I/O nem não determinismo por trás.
- Caso de uso ou classe que só repassa a chamada com os mesmos argumentos (ex.: serviço que só chama o repositório).
- Repositório genérico (`Repository<T>` com CRUD genérico): a porta tem só as operações que os casos de uso usam.
- O mesmo tipo duplicado em application e domain só para mapear um no outro.
- Pasta genérica fora das camadas (`utils/`, `helpers/`, `common/`, `shared/`): o código fica na camada a que pertence.
- Mediator ou barramento em memória entre adaptador e caso de uso: o adaptador chama o caso de uso direto. Exceção: decisão registrada em `research.md`.
- Modelos separados de leitura e escrita (CQRS) ou event sourcing sem decisão registrada em `research.md`.

## No Desenho técnico (tech lead)
- Primeira linha: `Tipo: <papéis> | Nível: <n> — <critério> | ...`; front-end, IaC e biblioteca: `Nível: não se aplica`.
- `Estrutura`: a árvore do nível, com os nomes da skill da stack; stack sem skill, com os nomes da tabela de camadas.
- `Padrões`: `clean-architecture nível <n>` e as referências de papel usadas.
- Repositório vazio: o `docs/arquitetura.md` registra o nível e a tabela de camadas aplicada.

## Referências
- `references/api.md` — ler quando o repositório expõe endpoints HTTP.
- `references/consumer.md` — ler quando o repositório consome mensagens de fila, tópico ou stream.
- `references/producer.md` — ler quando o repositório publica eventos.
- `references/tarefa-orquestrada.md` — ler quando o código é uma tarefa chamada por um orquestrador de fluxo (ex.: Step Functions).
- `references/job.md` — ler quando o repositório roda por agendamento, em lote ou por linha de comando.
- `references/dominio-rico.md` — ler quando o nível é 3.
