---
name: qa-integration
description: Como montar e rodar testes de contrato e ponta a ponta entre serviços, com dependências reais em contêiner. Use sempre no papel qa.
---

# QA de integração

## Ambiente (constitution §28)
- `integration/docker-compose.yml` sobe os serviços do workspace + dependências reais (banco, Kafka, LocalStack para AWS). <!-- TIME: ajustar -->
- Dados de teste criados pelos próprios testes; nada de base compartilhada suja.
- Testes de integração dentro de cada repositório usam Testcontainers (`Testcontainers.PostgreSql`, `Testcontainers.Kafka` no .NET; `testcontainers[postgres,kafka]` no Python).

## Testes de contrato (constitution §27)
- **HTTP**: valide as respostas reais do produtor contra o OpenAPI de `contracts/` (ex.: Schemathesis) e os requests do consumidor contra o mesmo contrato. <!-- TIME: ou Pact -->
- **Eventos**: valide o evento publicado pelo produtor contra o schema de `contracts/`, e alimente o consumidor com exemplos válidos do schema.
- Um teste por contrato e por lado.

## Ponta a ponta
- Um teste por critério de aceite da spec, nomeado com o id do critério.
- Para fluxos assíncronos, aguarde o efeito com polling e timeout (ex.: até 30s), nunca `sleep` fixo.
- Verifique também os caminhos de erro: mensagem inválida chega à DLQ (constitution §11), requisição repetida com a mesma chave é idempotente (constitution §7).

## Atribuição de falhas
- Falha de contrato → repositório do lado que divergiu do schema.
- Falha ponta a ponta → siga o `traceId` nos logs até o primeiro serviço com erro.

## Organização e regressão
```
integration/pytest.ini            # testpaths = tests; --strict-markers; marcador smoke registrado
integration/tests/conftest.py     # só o comum a todas as features (endpoints, credenciais de teste)
integration/tests/comum.py        # utilitários genéricos (polling com timeout)
integration/tests/<f>/
  manifest.yaml                   # covers: repos e contracts (<arquivo>@<versão>); smoke: lista dos testes
  apoio_<id>.py                   # fixtures e helpers da feature, importados pelos testes dela
  test_<id>_<assunto>.py          # nomes com o id da feature: o pytest não aceita nomes repetidos entre pastas
```
- Nada específico de uma feature no `conftest.py` raiz; fixtures `autouse` da feature ficam no `apoio_<id>.py`, para não afetarem as outras.
- `@pytest.mark.smoke` em 1 a 3 testes por feature: caminho feliz e contrato principal, os mais baratos que provam que a feature continua de pé.
- Regressão em camadas: feature atual completa; smoke de todas as anteriores; suíte completa das anteriores cujo `covers` intersecta os repositórios ou contratos alterados.

## Referências
- `references/localstack.md` — ler quando o ambiente de integração usa LocalStack.
