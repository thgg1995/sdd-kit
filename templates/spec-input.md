# Spec: <nome da feature>

<!-- Modelo do arquivo de especificação de entrada. Seções de negócio são texto livre;
     a seção "Stack técnico" é estruturada e lida pelo orquestrador. -->

## Contexto e objetivo

## Atores e papéis

## Requisitos funcionais

## Regras de negócio

## Casos de borda e comportamento em erro

## Integração entre repositórios
<!-- Quem produz/consome o quê; síncrono ou assíncrono; idempotência; retentativas. -->

## Requisitos não funcionais
<!-- Volume, latência, segurança, observabilidade. -->
<!-- Volumes e limites: a triagem do tech lead os confronta com os limites da plataforma logo depois do specify; o que faltar vira pergunta.
  - volume de referência e pico (por ciclo, por segundo ou por dia)
  - tamanho máximo de cada item (mensagem, arquivo, registro)
  - números: maior valor e precisão exigidos
  - exceções de segurança aceitas (ex.: permissões que a plataforma só concede com curinga) -->

## Critérios de aceite
<!-- Testáveis, um por linha. -->

## Execução
<!-- QA de integração: não (padrão) | sim.
  O QA vem DESATIVADO por padrão e só roda se esta linha disser `sim`.
  sim = sobe um ambiente de integração (Docker/emulador) e roda testes de ponta a ponta contra os contratos.
  não = não há QA nem preparo desse ambiente; os limites de integração só são conferidos pelo tech lead e pelos testes unitários. -->
QA de integração: não

## Stack técnico
<!--
Um bloco por repositório envolvido na feature. `name` = nome da pasta, igual ao workspace.yaml.
- OBRIGATÓRIO para repositório vazio ou com `stack: ?` no workspace.yaml: stack, version, runtime, techs.
- Repositório com stack detectada: opcional; serve para confirmar ou complementar. Divergência com o
  detectado vira pergunta no gate de clarificação (o código existente não é trocado sem aprovação).
- Use o vocabulário abaixo, pois é ele que ativa as skills (catalog.yaml do kit).
  stack:   dotnet | python | node | react | angular | vue | go | java | terraform
  techs:   kafka | aws | api | sql | nosql | docker
- Campos desconhecidos: use "?". O gate de clarificação pergunta somente os obrigatórios.
-->
```yaml
repos:
  - name: <pasta-do-repo>
    stack: python               # linguagem/stack predominante
    version: "3.12"             # versão da linguagem/SDK/ferramenta
    runtime: aws-lambda         # aws-lambda | ecs | eks | ec2 | container | browser | n/a
    frameworks: []              # ex.: [fastapi], [aws-lambda-powertools], [aspnetcore]
    techs: [aws]                # tecnologias que ativam skills condicionais
    tools: [pytest, ruff]       # ferramentas de teste, lint, empacotamento, IaC (ex.: terraform, cdk, sam)
    commands:                   # opcional; se "?", o dev define ao criar o projeto e reporta
      build: ?
      test: ?
      test_one: ?
      lint: ?
      run: ?
    conventions: ?              # até 3 linhas: estrutura de pastas, padrões obrigatórios etc.
```
