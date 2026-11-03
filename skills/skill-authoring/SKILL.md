---
name: skill-authoring
description: Como criar ou atualizar uma skill no padrão do kit — estrutura (SKILL.md + references/), frontmatter, gatilhos, regras verificáveis, entrada do catálogo e checklist de qualidade. Use quando o tech lead precisa propor uma skill nova ou a atualização de uma existente.
---

# Criar e atualizar skills do kit

Uma skill é o padrão escrito que dev, reviewer e tech lead seguem para um tipo de repositório ou de tarefa. Ela é lida por agentes de qualquer ferramenta de IA: escreva para quem não conhece o projeto e vai obedecer ao pé da letra.

## Quando propor
- **Nova**: tipo de aplicação sem skill, ou assunto que nenhuma skill cobre (ex.: Step Functions, front-end React, worker de fila).
- **Atualização**: a skill existe, mas falta o caso da feature, ou uma regra dela se mostrou errada (dev, reviewer ou QA precisaram de desvio). Prefira atualizar a criar uma skill vizinha que se sobreponha.
- **Não proponha** para algo que vale só nesta feature: isso é `Desenho técnico`, não skill.

## Estrutura (padrão Agent Skills, neutro de ferramenta)
```
specs/<f>/techlead/skills/<nome>/
  SKILL.md              # sempre lido por quem carrega a skill — no máximo 150 linhas
  references/<assunto>.md  # lido só no gatilho; um assunto por arquivo, entendível sozinho
  catalog-entry.yaml    # entrada sugerida para skills/catalog.yaml (não vai para a skill publicada)
```
- `<nome>`: minúsculas, números e hífen, até 64 caracteres, igual ao nome da pasta (ex.: `aws-serverless`, `react-frontend`).
- Frontmatter só com `name` e `description`. Nada de campo específico de uma ferramenta (`allowed-tools`, `model`...): o kit roda em qualquer agente.
- `description` (até 1024 caracteres): o que a skill cobre + "Use quando <gatilho>". É por ela que o agente decide carregar.
- Atualização: mesma estrutura, com os arquivos completos já alterados e, no topo do resumo em `reports/techlead.md`, o que mudou e por quê.

## O que vai no SKILL.md e o que vai em references/
| SKILL.md | references/ |
|---|---|
| regras que valem para qualquer tarefa da skill | exemplos completos, padrões longos, tabelas |
| estrutura do repositório e convenções que afetam a 1ª tarefa | casos especiais e variações |
| proibições, cada uma com a seção da constitution que detalha | receitas passo a passo |
| índice de referências com gatilho de leitura | detalhes de uma ferramenta ou serviço |
- Regra estrutural nunca fica só em `references/`: o dev precisa dela antes da primeira tarefa.
- Índice no fim do `SKILL.md`, uma linha por arquivo: `- references/<assunto>.md — ler quando <gatilho concreto>`.

## Como escrever as regras
1. **Imperativo e verificável**: "Políticas por `aws_iam_policy_document`; teste por `jsondecode`", não "use boas práticas de IAM". O reviewer precisa conseguir dizer se foi cumprida olhando o diff.
2. **Uma regra, um lugar**: não repita a constitution nem outra skill. Aponte: "Complementa `aws-infra`; em conflito, vale a constitution". Cite a seção da constitution que a regra detalha (`§22`).
3. **Proporcional**: só o que o tipo de aplicação usa de fato. Nada de camada, padrão ou ferramenta "para o futuro".
4. **Sem escolha de stack**: a skill não troca linguagem, versão, runtime nem acrescenta ferramenta principal; ela diz como usar a stack declarada.
5. **Verificada**: todo exemplo de código e configuração tem de ser válido. Confira contra a documentação oficial, um comando de validação (`terraform validate`, `validate-state-machine-definition`, linter, compilador) ou código existente que funciona. O que não deu para verificar vai marcado `> Não verificado: <o quê> — <como verificar>`, para o dev provar na primeira tarefa.
6. **Exceções explícitas**: quando a regra tem exceção conhecida (ex.: ação AWS que só aceita `*`), escreva a exceção e o que exigir para usá-la ("registrada no plano").
7. **Idioma**: texto em `IDIOMA` do `AGENTS.md`; identificadores, comandos e nomes técnicos como estão.
8. **Sem dado do projeto**: nada de nomes de recursos, contas, URLs ou regras de negócio da feature. A skill vale para qualquer feature do mesmo tipo.

## Entrada do catálogo (`catalog-entry.yaml`)
```yaml
  - name: <nome>
    stacks: [<stack>]          # instala quando algum repositório tem essa stack; ou
    techs: [<tech>]            # quando tem essa tech; ou always: true
    rules: "§<n>-<m>"          # seções da constitution que a skill detalha
    trigger: <tarefa concreta que dispara a leitura>
    loaded_by: <techlead, dev, reviewer, qa — só quem precisa>
```
- `stacks`/`techs` no vocabulário de `.agents/templates/spec-input.md`.
- `trigger` descreve a tarefa ("tarefa cria ou altera função Lambda..."), não a tecnologia solta.

## Checklist antes de devolver a proposta
- [ ] `SKILL.md` com até 150 linhas; frontmatter só com `name` e `description`, e a `description` termina com o gatilho.
- [ ] Estrutura do repositório e convenções da 1ª tarefa estão no `SKILL.md`.
- [ ] Cada regra é verificável no diff e não repete constitution nem outra skill.
- [ ] Todo exemplo foi verificado, ou está marcado `Não verificado` com o modo de verificar.
- [ ] Cada arquivo de `references/` tem um gatilho no índice e se entende sozinho.
- [ ] Nada específico desta feature nem de uma ferramenta de IA.
- [ ] `catalog-entry.yaml` com `stacks`/`techs`, `rules`, `trigger` e `loaded_by`.
- [ ] Resumo da proposta em `reports/techlead.md` (`Skill proposta: sim: ...`).

## Referências
- `references/modelo.md` — ler ao começar a redigir: modelos completos de `SKILL.md`, de arquivo de referência e de `catalog-entry.yaml`.
- `references/exemplos.md` — ler ao revisar as regras redigidas: regras boas e ruins lado a lado e erros já vistos em propostas.
