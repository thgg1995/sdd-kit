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

## Exemplos validáveis (Python e C#)
O `tests/validar_exemplos.py` do kit extrai os blocos de código dos `.md` da skill e valida todos de uma vez. Para um bloco entrar na validação:
- **Python**: a 1ª linha é `# <arquivo>.py`, com nome único na skill. O teste fica em outro bloco, `# test_<arquivo>.py`, e importa do módulo pelo nome (`from <arquivo> import ...`). Roda `ruff format --check`, `ruff check` com a configuração da `python-backend` e `pytest`.
- **C#**: bloco com `[Fact]` ou `[Theory]` é teste xUnit; bloco que começa com `// composition root` usa a variável `services` (`IServiceCollection`); os demais são código de produção, compilado com `Nullable` e `TreatWarningsAsErrors`. Não declare namespace: cada `.md` ganha o seu. Tudo o que o código usa precisa estar nos blocos do mesmo `.md`.
- Trecho ilustrativo, que não compila sozinho, não entra: em Python, sem a 1ª linha `# <arquivo>.py`; em C#, começando com `// trecho`.
- Rodar: `python -I tests/validar_exemplos.py skills/<nome>`; `--formatar` aplica o `ruff format` aos blocos Python no próprio `.md`. Requer ruff, pytest e o SDK do .NET (com acesso ao NuGet na primeira execução).
- O Python dos exemplos precisa ser da versão mínima da `python-backend` (o ruff analisa para ela). Se o Python padrão da máquina for mais antigo, o validador recusa e pede outro: `--python <executável>`, com pytest instalado.

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
