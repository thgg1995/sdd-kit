---
name: token-efficiency
description: Como trabalhar gastando menos tokens sem perder qualidade — chamadas agrupadas, leitura por trecho, saída curta de comandos, escrita por trecho e artefatos sem repetição, cada regra com a métrica que a confere. Use quando qualquer papel do fluxo, inclusive o orquestrador, começa a trabalhar.
---

# Uso eficiente de tokens

Cada chamada ao modelo relê todo o contexto do agente, e tudo o que entra nele (arquivo lido, saída de comando, resposta) volta em todas as chamadas seguintes. O consumo é o número de chamadas vezes o tamanho do contexto: o caro é chamada demais, sessão longa e saída grande no início. Entre parênteses, a métrica do relatório do `consumo.py` que confere a regra (`references/medicao.md`).

**A economia nunca dispensa:**
- as leituras integrais: o roteiro, o papel, o `SKILL.md` das skills indicadas, os arquivos de comando do Spec Kit, o que o papel manda ler sem dizer "por trecho" e os artefatos que o analyze e o converge comparam;
- os donos dos artefatos, os gates e as verificações obrigatórias.

Entre decidir por um trecho e ler mais, leia mais: uma ocorrência isolada ou uma saída cortada não prova ausência.

## Chamadas
- Chamadas de ferramenta independentes vão na mesma resposta: ler o papel, as skills e o plano de uma vez; buscar vários termos de uma vez. (ferramentas por chamada)
- Comandos de shell em sequência vão num comando só, ligados por `&&`, salvo quando a saída de um decide o próximo. No Windows PowerShell 5.1, que não tem `&&`, use `;` só entre comandos que apenas leem; com escrita, `if ($?) { ... }` entre eles. (ferramentas por chamada)
- Subagente ou processo em segundo plano: espere a notificação de término, com a espera mais longa que a ferramenta permitir, sem consultar o estado em laço. (esperas)
- Comando que falhou: leia o erro antes de tentar de novo. Repita igual só se ele indicar falha passageira (rede, tempo esgotado); senão, mude a hipótese ou o comando. Os limites de tentativas e de ciclos são os do papel e do roteiro. (comandos repetidos)

## Leitura
- Comece pelos caminhos que a tarefa, o plano ou o diff citam; busque só o que eles não respondem.
- Arquivo que continua no seu contexto e não mudou não se relê. O que mudou vem do prompt de continuação ou do relatório de quem alterou; no código, de `git diff -- <arquivo>`. Depois que o contexto for resumido ou compactado, releia o que a próxima decisão exige. (leituras repetidas)
- Fora as leituras integrais, arquivo com mais de 200 linhas: localize por busca e leia o intervalo, ampliado até a função, a seção ou o contrato inteiro de que a decisão depende. (leituras inteiras)
- Busca restrita à pasta relevante, fora de dependências e saídas de build (`node_modules`, `.venv`, `obj`, `dist`, `.terraform`, `.git`, e `bin` quando é saída de build, como no .NET): primeiro por nome de arquivo, depois por termo, com até 3 linhas de contexto. (maior resultado)

## Saída de comandos
- Teste, build, lint, instalação e implantação: o comando que o repositório ou o ambiente declaram (notas do repositório, `Teste específico`, seção `integration` do `workspace.yaml`), com as opções de `references/comandos.md` que reduzem a saída sem mudar o que ele faz. (maior resultado)
- Saída que pode passar de 100 linhas vai para um arquivo temporário fora do repositório; no contexto entram o código de saída e o trecho que a decisão usa: o erro, o resumo ou as linhas buscadas. (resultados grandes)
- Listagem sempre com limite: `head`, `git log --oneline -n 20`, `git diff --stat` antes do diff. (maior resultado)
- Saída cortada pela ferramenta: recupere o trecho que falta antes de concluir.

## Escrita
- Arquivo existente se altera por trecho; reescrever inteiro só quando a mudança passa da metade dele. (reescritas)
- Artefato cita o ID (`FR-001`, `SC-002`, `T012`, `CA03`) e o caminho do que já está em outro artefato que o mesmo leitor tem, em vez de copiar o texto. A fatia que um papel lê sozinho traz o texto de que ele precisa: o dev e o reviewer recebem `repos/<repo>/` sem a spec. A cópia das tarefas em `repos/<repo>/tasks.md` é do fluxo. (parágrafos repetidos)
- Trabalho interrompido (limite, bloqueio): o relatório do papel registra os arquivos já alterados e a próxima ação, para quem retomar não refazer a investigação.

## Orquestrador
- Registro no `fluxo.py` vai na mesma resposta da ação seguinte: `inicio` junto com o disparo do subagente; `fim` e `consumo` junto com o próximo passo. (só registro)
- Dos artefatos, leia só o que o roteiro manda (ex.: o `tasks.md`, para escolher as skills condicionais; o `qa.md`, para escolher a correção); spec, plano e código, os papéis leem, e você passa os caminhos.

## Referências
- `references/comandos.md` — ler ao rodar, pela primeira vez na sessão, teste, build, lint, instalação ou implantação de uma stack.
- `references/medicao.md` — ler ao medir o consumo de uma execução ou comparar versões do kit.
