---
name: design-patterns
description: Padrões de projeto para código de back-end organizados por sintoma — o que no plano ou no código pede cada padrão, quando não usar, a forma em Python e .NET e como testar. Use quando o repositório é de back-end e o tech lead escreve o Desenho técnico, ou quando o dev ou o reviewer encontram no plano ou no código um sintoma listado no índice desta skill.
---

# Padrões de projeto (back-end)

Complementa `clean-architecture` (camadas e portas: onde cada parte fica) e a skill da stack. Padrões de integração (outbox, consumer idempotente, retentativa, saga) estão nas skills de tecnologia (`kafka-messaging`, `api-design`, `aws-serverless`); Service Locator já tem regra na `dotnet-backend`, e o barramento em memória, na `clean-architecture` (a alternativa está em `references/mediator.md`). Em conflito, vale a constitution.

## Quando se aplica
- Só a back-end: stack `dotnet`, `python`, `node`, `go` ou `java`, exceto biblioteca (`kind: lib`). Os exemplos são em Python e .NET; nas outras stacks, use a forma equivalente com as convenções da skill da stack.
- Precedência: `Desenho técnico` > padrões que o repositório já usa > esta skill.

## Regra de evidência
- Padrão só entra com sintoma presente no plano (código novo) ou no código (código existente). "Pode precisar no futuro" não é sintoma.
- Tech lead: sintoma no plano → linha em `Padrões` do Desenho técnico: `<padrão> → <onde> → design-patterns/references/<arquivo>`. Padrão considerado e descartado por falta de sintoma → `Não fazer`.
- Dev: sintoma que surge na implementação (ex.: a segunda decisão pelo mesmo critério) → aplique o padrão dentro do escopo da tarefa e registre em `Decisões não previstas`.
- Reviewer: aponte sintoma sem padrão e padrão sem sintoma. Padrão do Desenho técnico não seguido é `bloqueante` (aderência ao desenho); os demais achados desta skill são `sugestão`.

## Sintomas de excesso
| No código | Faça |
|---|---|
| Strategy com uma estratégia só | código direto |
| fábrica que cria um tipo só | chame o construtor |
| Builder de produção para objeto com poucos campos, todos obrigatórios | construtor |
| Decorator que só repassa a chamada | remova |
| pipeline com uma etapa | chamada direta |
| Specification usada num lugar só | função com nome |
| Abstract Factory com uma família só | crie as peças direto |
| Bridge em que só uma dimensão varia | porta comum ou Strategy |
| fachada que só repassa uma chamada | chame a biblioteca direto |
| proxy sob demanda para objeto barato de criar | crie direto |
| comando para chamada imediata com um ou dois parâmetros | chamada direta |
| unidade de trabalho para uma escrita só | grave pelo repositório |
| lista de observadores com um observador só | chamada direta no caso de uso |

## Proibido
- Padrão sem sintoma no plano ou no código.
- Singleton por acesso estático ou estado global: instância única é tempo de vida definido no composition root ou no container (`references/singleton.md`).

## Referências
- `references/strategy.md` — ler quando o plano lista duas ou mais variações de um comportamento, cada uma com regra própria, ou o mesmo critério decide o comportamento em dois ou mais lugares do código.
- `references/state.md` — ler quando uma entidade tem três ou mais estados com regras de transição, ou transições são validadas por `if` em vários lugares.
- `references/decorator.md` — ler quando cache, métrica, log ou retentativa precisam envolver uma porta sem mudar o adaptador, ou esse código aparece copiado em vários adaptadores.
- `references/factory-method.md` — ler quando o tipo do objeto a criar depende do dado recebido, ou a construção é escolhida por `if` em vários lugares.
- `references/builder.md` — ler quando um objeto tem muitos campos opcionais, uma função passa do limite de parâmetros da `clean-code-solid`, ou testes repetem a montagem de um objeto grande.
- `references/chain-of-responsibility.md` — ler quando o processamento é uma sequência de etapas que variam por tipo, canal ou configuração, ou uma função longa liga e desliga etapas por flags.
- `references/composite.md` — ler quando há estrutura em árvore em que item e grupo são tratados do mesmo jeito, ou o código testa o tipo do item para percorrer grupos.
- `references/specification.md` — ler quando a mesma condição de negócio aparece reescrita em vários lugares, ou condições se combinam com "e", "ou" e "não".
- `references/abstract-factory.md` — ler quando duas ou mais famílias de objetos variam juntas e são usadas em conjunto, ou o código escolhe cada peça por `if` e misturar famílias é bug.
- `references/prototype.md` — ler quando um objeto novo nasce de um existente com poucas mudanças, ou o código remonta campo a campo um objeto que já existe como modelo.
- `references/singleton.md` — ler quando um recurso deve existir uma vez por processo, ou o código tem instância global estática.
- `references/adapter.md` — ler quando o caso de uso precisa de uma operação que um sistema externo oferece em outro formato (nomes, unidades, códigos de erro), ou esse formato aparece no código de negócio.
- `references/bridge.md` — ler quando duas dimensões variam de forma independente e cada combinação vira uma classe.
- `references/facade.md` — ler quando o código repete a sequência de chamadas de uma biblioteca para uma operação que o negócio vê como uma só.
- `references/flyweight.md` — ler quando uma medição de memória mostra muitas instâncias com o mesmo valor imutável.
- `references/proxy.md` — ler quando uma dependência cara de criar só é usada em parte das execuções, ou o acesso à implementação real precisa ser controlado sem que quem chama perceba.
- `references/command.md` — ler quando uma operação precisa existir como objeto (validada, registrada, enfileirada, auditada), ou o caso de uso recebe vários parâmetros soltos que formam um pedido.
- `references/interpreter.md` — ler quando regras ou filtros vêm da configuração ou do usuário e são avaliados em tempo de execução.
- `references/iterator.md` — ler quando o código carrega uma coleção inteira só para percorrer (páginas de uma API, arquivo grande), ou repete o laço de paginação em vários lugares.
- `references/mediator.md` — ler quando componentes se chamam em teia (um serviço chama o outro, que chama o próximo), ou surge a vontade de um barramento em memória.
- `references/memento.md` — ler quando uma operação precisa voltar um objeto em memória a um estado anterior (desfazer, tentar e voltar).
- `references/observer.md` — ler quando, depois de uma mudança, outras partes precisam reagir e o caso de uso cresce chamando cada uma.
- `references/template-method.md` — ler quando duas ou mais operações seguem o mesmo roteiro e diferem em um ou dois passos, ou há classe base abstrata com passos para as subclasses preencherem.
- `references/visitor.md` — ler quando várias operações percorrem uma hierarquia fechada de tipos com `isinstance`/`is` espalhado.
- `references/repository.md` — ler quando um caso de uso precisa ler ou gravar uma entidade (ou um agregado), ou ao escrever o fake do repositório para teste.
- `references/unit-of-work.md` — ler quando um caso de uso grava mais de uma coisa que precisa ser atômica (ex.: a entidade e o evento na outbox).
