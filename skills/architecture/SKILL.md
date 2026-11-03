---
name: architecture
description: Como decompor uma feature entre repositórios e escrever contratos. Use na fase de plan e em qualquer decisão entre repositórios ou de contrato.
---

# Arquitetura e contratos

## Posse dos dados (constitution §1, §2)
- No `plan.md`, liste cada entidade com seu serviço dono. Uma linha por entidade.
- Outro serviço precisa do dado → consome evento do dono e mantém uma réplica local de leitura, ou chama a API do dono.
- Dúvida sobre o dono → é pergunta do gate de clarificação, não decisão do agente.

## Contratos (constitution §3)
Tudo em `specs/<f>/contracts/`, um arquivo por contrato:
| Tipo | Formato | Nome do arquivo |
|---|---|---|
| API HTTP | OpenAPI 3.1 | `<servico>.openapi.yaml` |
| Evento | AsyncAPI 3 + JSON Schema | `<topico>.asyncapi.yaml` |
<!-- TIME: troque por Avro/Protobuf se usarem Schema Registry com esses formatos -->

Cada contrato declara no topo: `owner` (produtor), `consumers` e `version`.

## Versionamento (constitution §4)
- Compatível: adicionar campo opcional, novo endpoint, novo tipo de evento.
- Quebra: remover/renomear campo, mudar tipo, tornar obrigatório, mudar semântica.
- Quebra → nova versão (`/v2/...` ou `<evento>.v2`), as duas convivem; o plano registra quando a antiga sai.

## Sync ou async
- Async (evento) quando o chamador não precisa da resposta para concluir sua operação.
- Sync (API) quando precisa da resposta imediata; aplique `api-design`.
- Cadeia de mais de 2 chamadas síncronas entre serviços → reavalie com eventos.

## Saída esperada no plan
1. Tabela entidade → dono.
2. Lista de contratos com produtor e consumidores.
3. `depends_on` de cada repositório derivado dos contratos.
