# Domínio rico (nível 3)

Aplica-se quando o nível do repositório é 3: entidades com estados e regras que dois ou mais casos de uso precisam preservar.

## Modelo
- **Entidade**: tem identidade; o estado muda só por métodos que aplicam a regra (ex.: `cancelar()` recusa pedido já enviado). Campo com regra não tem setter público.
- **Value object**: imutável, igualdade por valor, válido desde a criação (ex.: `Dinheiro`, `Email`, `Periodo`).
- **Agregado**: entidades alteradas sempre juntas, com uma entidade raiz que é a única porta de entrada. Uma transação altera um agregado; outro agregado é referenciado pelo id e alterado por evento ou em outra transação. Exceção: decisão registrada em `research.md`.
- **Porta de persistência**: uma por raiz de agregado, com as operações que os casos de uso usam.

## Divisão do trabalho
- domain decide o que pode e o que não pode; application conduz o roteiro: carrega pela porta, chama o método da entidade, salva e publica.
- Condição de regra no caso de uso (ex.: `if pedido.status == ...` antes de alterar) → vira método da entidade.

## Fronteira e persistência
- A skill da stack define como a linguagem impõe a regra de dependência neste nível (ex.: um projeto por camada no .NET).
- domain não usa anotação nem classe base do ORM (§32): o mapeamento fica em `infrastructure/`.
