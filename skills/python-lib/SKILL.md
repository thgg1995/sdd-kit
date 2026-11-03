---
name: python-lib
description: Biblioteca Python compartilhada do kit (python_lib, kind lib no workspace.yaml) — quando reusar, alterar ou criar um método nela em vez de escrever código local, o catálogo de métodos, compatibilidade e versão, desenho dos módulos (clientes AWS, SQS, S3, DynamoDB, Secrets Manager, STS, logs) e testes com Stubber. Use quando um repositório Python da feature precisa de código técnico reutilizável ou quando a tarefa altera a própria lib.
---

# Biblioteca Python compartilhada

A lib fica **no kit** (`<KIT_LOCAL>/python_lib`, repositório git próprio) e é a mesma para todos os workspaces. No `workspace.yaml` ela aparece com `kind: lib`, `source: kit` e `path` relativo (ex.: `../sdd-kit/python_lib`). Os repositórios Python a consomem de lá; nunca a copie para dentro do workspace nem de um consumidor.
Validado com Python 3.14, boto3/botocore 1.43 e `botocore.stub.Stubber`.

## O que entra na lib (e o que não entra)
- **Entra**: código técnico que qualquer aplicação reaproveitaria — fábrica de clientes AWS com timeouts e retentativas padrão; operações de SQS, S3, DynamoDB, Secrets Manager, SSM Parameter Store e STS; padrão de log estruturado; extração de código de erro; utilitários de lote, paginação e cache.
- **Não entra**: regra de negócio, nomes de fila/tabela/segredo, formato de mensagem de uma feature, configuração de uma aplicação. Isso fica no consumidor.
- Na dúvida entre lib e local: vai para a lib se a função não cita nada da feature e um segundo consumidor a usaria como está.

## Catálogo: `CATALOGO.md` na raiz da lib
- É o **contrato da lib** e a única coisa que o consumidor lê dela: uma linha por símbolo público, com assinatura, propósito e versão de entrada. Formato e teste de sincronia: `references/catalogo.md`.
- Toda mudança pública na lib atualiza o catálogo no mesmo commit. Lib sem `CATALOGO.md` → a primeira tarefa da lib na feature é criá-lo a partir do `__all__`.

## Decisão por necessidade (tech lead no plano; dev confere)
Para cada necessidade técnica dos repositórios Python da feature, busque no catálogo (serviço + operação) e decida:
| Situação | Decisão | Onde |
|---|---|---|
| um método cobre como está | **reusar** `<módulo.nome>` | consumidor |
| cobre quase, falta um ajuste compatível | **alterar** `<módulo.nome>`: parâmetro novo opcional, só por nome, com default que mantém o comportamento | lib (tarefa) + consumidor |
| não existe e é genérico (seção acima) | **criar** `<módulo.nome>(<assinatura>)` | lib (tarefa) + consumidor |
| não existe e é específico da feature | **local**, com o motivo | consumidor |
| o ajuste muda comportamento, retorno, exceção ou parâmetro existente | **criar** um método novo (ou nome novo) e manter o antigo; quebra só com aprovação do humano | lib |
- O tech lead registra as decisões no `Desenho técnico` de cada consumidor, na linha `Lib:` (uma decisão por necessidade). Havendo `alterar` ou `criar`, a lib entra na feature como repositório (plano, tarefas, desenho) e os consumidores ganham `depends_on` nela.
- **Dev do consumidor**: use somente o que o catálogo e a linha `Lib:` dizem. Precisou de algo genérico que não está lá → não escreva uma cópia local: reporte `BLOQUEIO: lib — <necessidade> (<serviço/operação>)`. Específico da feature → local, registrado em `Decisões tomadas`.
- **Código local que já existe** e repete um método da lib: não migre por conta própria; registre em `Fora do escopo`.

## Regras do código da lib
1. **Cliente injetável**: toda função que chama a AWS recebe `client` (ou `session`) só por nome; o default, quando houver, vem de `clients.client("<serviço>")`. Nada de cliente criado no import.
2. **Sem estado global**, exceto cache explícito (clientes, segredos) com função de limpeza (`clear_*`) para testes.
3. **Falha visível**: não engula exceção. Erro da AWS sobe como `ClientError`/`BotoCoreError`, salvo quando o catálogo define outro retorno; operação em lote devolve os itens que falharam (`Failed`, `UnprocessedItems`) em vez de descartá-los.
4. **Limites da AWS dentro da lib**: lote, paginação e tamanho máximo tratados pela função, documentados no catálogo (`references/modulos.md`).
5. **Nunca registre** valor de segredo, credencial, corpo de mensagem nem item de tabela; logs da lib só em `logging.getLogger("<pacote>.<módulo>")`, sem configurar handler (quem configura é `logs.configure_logging`, chamado pela aplicação).
6. **Tipagem**: `mypy --strict` limpo, `py.typed`, só tipos de `mypy-boto3-*` em `TYPE_CHECKING`.
7. **Dependências**: `boto3` em faixa compatível (`>=x,<y`), nunca versão fixa; dependência nova na lib é decisão do tech lead, registrada no plano.
8. **`requires-python`** não sobe acima da menor versão entre os consumidores do `workspace.yaml`.
9. **Testes**: cada função pública com teste de sucesso, de erro da AWS e de limite (lote/paginação), com `Stubber`, sem rede (`references/testes.md`).

## Compatibilidade e versão
- Versão semântica em `__version__`: correção → patch; método ou parâmetro novo → minor; remoção ou mudança de comportamento → major, só com aprovação do humano (afeta todos os consumidores).
- Método substituído: mantenha o antigo com `warnings.warn(..., DeprecationWarning, stacklevel=2)` e a linha `obsoleto desde x.y → use <novo>` no catálogo.
- Toda versão nova ganha uma entrada no `CHANGELOG.md` da lib.

## Reviewer
- Na lib: compatibilidade (assinaturas e retornos existentes intactos), catálogo e versão atualizados, regras acima. Falha → `bloqueante`.
- No consumidor: método local que repete um do catálogo, ou desvio da linha `Lib:` → `bloqueante`; cópia antiga, já existente, → `sugestão`.

## Referências
- `references/catalogo.md` — ler ao criar ou atualizar o `CATALOGO.md`, ou ao buscar nele.
- `references/modulos.md` — ler ao criar ou alterar um módulo da lib (clientes, SQS, S3, DynamoDB, Secrets Manager, SSM, STS, logs).
- `references/testes.md` — ler ao escrever testes da lib ou testes do consumidor que dependem dela.
- `references/consumo.md` — ler ao decidir ou configurar como o consumidor depende da lib (desenvolvimento local, CI, empacotamento da Lambda).
