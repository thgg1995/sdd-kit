# API HTTP

Aplica-se quando o repositório expõe endpoints HTTP. O *como* (contrato, formato de erro, idempotência, paginação, validação, chamadas externas) está na `api-design`; aqui fica a camada de cada parte.

## Nível
- Um endpoint de negócio: nível 1. Vários: nível 2.
- API que só repassa para outra (proxy, BFF que só agrega): nível 0.

## Onde fica cada parte
| Parte | Onde |
|---|---|
| rotas ou controllers, um arquivo por recurso | `entrypoints/http/` |
| tipos de request e response do contrato e a validação deles (§23) | `entrypoints/http/`, junto das rotas |
| autenticação, id de correlação e tratamento global de erro (middleware) | `entrypoints/http/` |
| conversão de erro de negócio para o formato único de erro (§6) | tratamento global de erro, em `entrypoints/http/` |
| guarda e reenvio da resposta por `Idempotency-Key` (§7) | middleware ou filtro em `entrypoints/http/`; o armazenamento é uma porta em `application/ports`, implementada em `infrastructure/` |
| cursor e limite da paginação (§8) | a rota os converte em parâmetros do caso de uso; a porta de leitura recebe os dois e devolve o próximo cursor |
| cliente de API externa (§9) | `infrastructure/`, atrás de uma porta |
| criação da aplicação web e registro das dependências | composition root |

## Fluxo de uma rota
1. O framework valida o request contra o tipo do contrato; inválido → `400` (`api-design`).
2. A rota converte o request para a entrada do caso de uso e o chama; leitura sem regra chama a porta de leitura direto.
3. Sucesso → a rota converte o resultado para o response do contrato.
4. Erro de negócio → o tratamento global o converte em status e corpo do contrato; a rota não captura erro de negócio.
