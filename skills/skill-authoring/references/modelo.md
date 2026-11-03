# Modelos para uma skill do kit

Copie e preencha. Remova as seções que não se aplicam; não acrescente seções vazias.

## SKILL.md
```markdown
---
name: <nome>
description: <o que cobre, em uma frase>. Use quando <tarefa concreta que dispara a leitura>.
---

# <Título curto>

Complementa `<skill vizinha>` (<o que ela cobre>). Em conflito, vale a constitution.

## Estrutura do repositório
- <pasta/arquivo>: <responsabilidade>.
- <onde entra cada coisa nova do tipo de aplicação>.

## <Assunto 1> (constitution §<n>)
- <regra imperativa e verificável>.
- <exceção conhecida e o que exigir para usá-la>.

## <Assunto 2> (constitution §<n>)
- ...

## Testes
- <ferramenta e forma do teste unitário deste tipo de aplicação>.
- <o que fica para o QA de integração>.

## Proibido
- <o que parece tentador e quebra o padrão> (§<n>).

## Referências
- `references/<assunto>.md` — ler quando <gatilho concreto>.
```

## Arquivo de referência (`references/<assunto>.md`)
```markdown
# <Assunto>

<Uma frase: quando este arquivo se aplica.>

## <Caso ou receita>
<passos, exemplo completo e válido, explicação curta do porquê>

> Não verificado: <o quê> — <como verificar>   (só se não foi possível verificar)

## <Outro caso>
...
```
- Um assunto por arquivo; quem chega aqui pelo gatilho não leu os outros arquivos de `references/`.
- Exemplos completos o bastante para copiar, sem dados do projeto (use `<nome>`, `exemplo`, `000000000000`).

## catalog-entry.yaml
```yaml
# Entrada sugerida para skills/catalog.yaml do kit (proposta do tech lead, feature <f>).
  - name: <nome>
    stacks: [<stack>]
    techs: [<tech>]
    rules: "§<n>-<m>"
    trigger: tarefa cria ou altera <o quê>
    loaded_by: techlead, dev, reviewer
```

## Resumo em reports/techlead.md
```
Skill proposta: sim: specs/<f>/techlead/skills/<nome>/ (nova | atualização de <skill>) — <lacuna que ela cobre, em uma linha>
```
Atualização: acrescente em `Decisões` uma linha por regra alterada (antes → depois, e a evidência: relatório do dev, reviewer ou QA).
