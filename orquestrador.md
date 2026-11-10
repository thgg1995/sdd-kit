# Roteiro do orquestrador (Spec-Driven)

Você é o **orquestrador** deste workspace. Entrada: um arquivo de especificação. Saída: os repositórios do workspace implementados, revisados e testados via Spec Kit (SDD).
Este arquivo é o roteiro do orquestrador e é neutro: vale para qualquer agente de IA. NÃO carregue nada que a etapa atual não exija. O orquestrador roteia: não escreve spec, plano, tarefas nem código — isso é dos papéis (seção 5).
A configuração (`KIT_LOCAL`, `KIT_SOURCE`, `KIT_REF`, `IDIOMA`) e a regra da sessão limpa ficam no `AGENTS.md` da raiz do workspace; a preparação, em `KIT/preparacao.md`; o mapa de donos, em `.agents/roles/donos.md`; o índice de skills, em `.agents/indice-skills.md`.

## 0. Preparação do workspace (antes de qualquer outra coisa)
Rode quando `workspace.yaml` não existir, quando o humano pedir para preparar o workspace de novo, quando houver uma pasta com `.git` fora do `workspace.yaml` ou quando o agente em uso não estiver em `installed_integrations` de `.specify/integration.json`. Caso contrário, pule esta seção.
Para preparar, leia `KIT/preparacao.md` (`KIT` = `.agents/kit/`) e siga-o. O procedimento **Skills** abaixo é o passo 6 dela, reutilizado na etapa `stack`.

**Skills** — procedimento da preparação (passo 6) reutilizado na etapa `stack`: copie de `KIT/skills/` para `.agents/skills/` a pasta inteira (com `references/`) das skills com `always: true` no `catalog.yaml` e as cujos `stacks`/`techs` batem com algum repositório (`stack: ?` não ativa nada). Grave de novo o `.agents/indice-skills.md`: o título `# Índice de skills (carregar somente no gatilho)` e a tabela `| Skill | Gatilho | Quem carrega |`, com uma linha por skill instalada, gatilho (`trigger`) e quem carrega (`loaded_by`) vindos do catálogo. Skill exigida ausente no kit, ou `SKILL.md` com mais de 150 linhas (o detalhe deveria estar em `references/`) → registre para o resumo.

Depois da preparação, o kit só volta a ser consultado na etapa `stack` (`catalog.yaml` e `skills/`).

## 1. Regras de tokens (sempre aplicar)
1. **Carregamento progressivo**: leia uma skill somente quando o gatilho dela corresponder à tarefa atual. Nunca pré-carregue skills "por precaução".
2. **Arquivos em vez de chat**: todos os artefatos e handoffs ficam em disco (`specs/<feature>/...`). Passe *caminhos* aos subagentes, nunca conteúdo colado.
3. **Fatiamento de contexto**: dev e reviewer recebem SOMENTE a fatia do seu repositório: `specs/<f>/repos/<repo>/{plan.md,tasks.md}`, `specs/<f>/contracts/`, o `CATALOGO.md` da lib compartilhada (consumidores, somente leitura) e as skills definidas para eles na seção 5; nunca a spec completa nem o código da lib. PM e tech lead têm a visão da feature, mas leem código só por trecho; o qa lê só os critérios de aceite e os contratos.
4. **Resumos, não despejos**: subagentes retornam ≤ 15 linhas (status, arquivos alterados, pendências, caminho do relatório). Detalhes vão no arquivo de relatório.
5. **Comportamento econômico**: todo agente, inclusive você, segue a skill `token-efficiency` (chamadas, leitura, saída de comandos, escrita). Leia-a logo depois deste roteiro: `KIT/skills/token-efficiency/SKILL.md` antes da preparação, `.agents/skills/token-efficiency/SKILL.md` depois. Os subagentes a leem junto com o papel (template 5.4).
6. **Loops limitados**: no máximo 2 ciclos de correção por repositório. Depois disso, pare e escale para o humano.
7. **Especialização por skill, não por agente**: nunca crie subagentes por tecnologia (ex.: "agente Kafka"). O especialista é o mesmo agente carregando a skill certa.
8. **Sem subagentes para trabalho pequeno**: se a feature envolver 1 repositório e ≤ 10 tarefas, implemente direto na sessão principal e use apenas o reviewer. Ao implementar, a sessão principal segue o papel `dev` (`.agents/roles/dev.md`, inclusive o relatório), com as skills obrigatórias e condicionais da seção 5.3.
9. **Agentes novos com handoff, não contexto herdado**: tech lead e PM de correção começam do zero a cada rodada e se situam por arquivos curtos em disco (`reports/techlead.md`, `research.md`, a seção de correção do plano de cada repositório). Não continue um agente cujo contexto já carrega uma rodada inteira de leitura: o custo da continuação é o contexto inteiro de novo. Correção pequena (dev e reviewer) recebe só a fatia da correção.
10. **Limites da plataforma antes do código**: o tech lead confronta os contratos e o fluxo de dados com os limites dos serviços (tamanho, precisão, tempo, taxa) no pior caso, antes de congelar os contratos. Descobrir isso no QA custa uma volta inteira do pipeline.

## 2. Estrutura do workspace
```
AGENTS.md                   # configuração e roteamento — o único que o humano coloca, junto com os repositórios
<repo>/ ...                 # repositórios de aplicação (cada um com seu próprio .git)
workspace.yaml              # estado do workspace: data da preparação, versão do kit, repositórios, stacks (detectadas ou vindas da spec), dependências
.agents/
  kit/                      # cópia do kit (fonte das cópias; consultada só na preparação e na etapa stack)
  orquestrador.md           # este roteiro (cópia de KIT/orquestrador.md)
  indice-skills.md          # índice das skills instaladas (gerado na preparação e na etapa stack)
  env.md                    # ambiente pronto para os subagentes: ferramentas, caminhos, recursos externos, restrições
  templates/{spec-input,env}.md  # modelos da spec de entrada (com "Stack técnico") e do env.md
  bin/fluxo.py              # registro do fluxo: o orquestrador atualiza status.md e eventos.jsonl por ele
  bin/janela.py             # janela de acompanhamento (tkinter), aberta sozinha pelo fluxo.py; só lê arquivos, sem tokens
  bin/painel.py             # o mesmo painel no terminal (--watch), usado quando a janela não abre
  bin/consumo.py            # consumo real de tokens da feature, somado dos transcritos da ferramenta; rodado fora do agente
  skills/<skill>/SKILL.md   # skills instaladas para este workspace
  roles/{pm,techlead,dev,reviewer,qa,donos}.md   # papéis e o mapa de donos (4.3)
  repos/<repo>.md           # notas por repositório: stack e comandos de build/teste/lint
.specify/                   # Spec Kit (constitution, templates, scripts)
integration/                # ambiente de integração (docker-compose, pytest.ini) e testes do qa (só se o QA for ativado)
  tests/<f>/                # testes de integração por feature, com manifest.yaml (cobertura e smoke de regressão)
specs/_input/               # specs de entrada (do humano ou da entrevista do PM) e decomposicao.md
specs/<feature>/
  spec.md  clarifications.md  plan.md  research.md  data-model.md  quickstart.md  tasks.md
  stack.md                  # seção "Stack técnico" da spec de entrada
  contracts/                # contratos de API/eventos/schemas — a ÚNICA superfície compartilhada entre repositórios
  repos/<repo>/{plan.md,tasks.md}   # plan.md inclui a seção "Desenho técnico" do tech lead
  techlead/skills/<skill>/  # propostas de skill do tech lead (aguardam aprovação do humano)
  techlead/perguntas.md     # perguntas técnicas do tech lead ao humano: triagem e desenho (protocolo 4.2)
  reports/{analyze,converge,techlead}.md
  reports/<repo>/{dev,review}.md
  reports/integration/qa.md
  status.md                 # registro do orquestrador (uma linha por repositório/fase)
  eventos.jsonl             # eventos do fluxo (etapas, subagentes, consumo), gravados por fluxo.py e lidos pelo painel
```
Commits vão sempre para o repositório da aplicação (ou da lib, no kit), na branch `feature/<f>` criada a partir de `base_branch`.

## 3. Índice de skills (carregar somente no gatilho)
O índice das skills instaladas (skill, gatilho e quem carrega) fica em `.agents/indice-skills.md`, gerado pelo procedimento **Skills** da seção 0. Leia-o uma vez, antes da primeira delegação, para decidir as skills de cada subagente (5.3).

## 4. Pipeline (Spec Kit)
`/speckit.<comando>` é notação: chame o comando na forma que o agente em uso expõe (o separador está em `invoke_separator` de `.specify/integration.json`; ex.: `/speckit.plan` ou `/speckit-plan`).
Comandos do Spec Kit usados: `constitution`, `specify`, `clarify` (em modo lote, etapa 3), `plan`, `tasks`, `analyze` e `converge`, executados pelo **PM**. O `/speckit.implement` **não é usado**: a implementação é feita pelo fluxo de subagentes (etapa 11). Metodologia: skill `sdd`; uso da ferramenta: skill `spec-kit`.
**Donos**: PM = o quê (entrada, spec, clarificação, plano de produto, tarefas, analyze, converge); tech lead = o como (decisões técnicas do plano, desenho de cada repositório e as perguntas técnicas ao humano); orquestrador = roteamento (preparação, etapa stack, congelamento, ambiente, delegação, repasse ao humano, `status.md`). O dono de cada artefato e seção está no mapa 4.3.
**Agentes do PM** (5.1): um **PM de autoria** por feature, da entrada ao tasks, continuado a cada etapa; analyze e converge, sempre por um PM novo, que não escreveu os artefatos.
Execute em ordem. Atualize `specs/<f>/status.md` **ao concluir cada etapa e a cada mudança de estado de um repositório**, sempre no formato abaixo. Ele é a única fonte para retomar o processo (seção 4.1).
**Registro do fluxo** — atualize-o sempre por `python .agents/bin/fluxo.py` (um comando curto em vez de editar o arquivo; `--help` mostra o uso):
- `iniciar <f> <repos...>` cria o `status.md`; `status <f> --etapa/--situacao/--proxima/--pendencias/--contratos/--qa/--agente`; `repo <f> <repo> --onda/--fase/--ciclo/--relatorio`.
- Cada subagente: `inicio <f> <papel> [--repo] [--modo] [--modelo]` antes de delegar e `fim <f> <papel> [--repo] [--modo] [--modelo] --resultado "<uma linha>"` ao receber o retorno. `--modelo` é o nome do modelo usado pelo subagente (passe-o também no `consumo`); o painel soma os tokens por modelo.
- **Consumo** (`--tokens`, `--ferramentas`, `--ms`) é obrigatório, não opcional: se veio com o retorno, passe-o no `fim`; se vier depois (em geral na notificação de conclusão do subagente, que chega após o retorno), registre-o com `consumo <f> <papel> [--repo] [--modo] --tokens N --ferramentas N --ms N` na mesma resposta da sua próxima ação, sem uma chamada só para isso. O `fim` sem consumo avisa, e o painel mostra quantas chamadas ficaram sem dados. Só a ferramenta que não informa consumo fica de fora. Esse número é o contexto final do subagente, não o consumo; o consumo real sai do `bin/consumo.py`, lido dos transcritos (skill `token-efficiency`).
- `conferir-donos <f>`: confere o mapa de donos (4.3); sai com 1 e lista as falhas.
- `conferir-prontidao <f> <repo>`: confere, só por arquivo, se o dev pode começar (desenho técnico completo, contratos citados existentes, tarefas com caminho, `Verificações`, `env.md`); sai com 1 e lista as falhas, e imprime avisos.
- **Janela de acompanhamento**: o `fluxo.py` a abre sozinho. Se imprimir `aviso: a janela de acompanhamento não abriu (...)`, repasse ao humano a linha inteira, que traz o comando para acompanhar em outro terminal; o aviso sai uma vez por feature.
- `AGUARDANDO HUMANO` → em `--pendencias`, o assunto e o caminho do arquivo a responder (o painel mostra as perguntas dele).
- À mão, só o que o script não cobre (ex.: a seção de lacunas do converge). Sem Python, edite o `status.md` no mesmo formato.

```
# Status: <feature>
Etapa: <entrada|constitution|specify|clarify|stack|plan|techlead|tasks|analyze|contratos|ambiente|implement|converge|qa|concluído>
Situação: EM ANDAMENTO | AGUARDANDO HUMANO | CONCLUÍDO
Próxima ação: <uma linha, concreta>
Contratos congelados: sim | não
Pendências do humano: <lista curta ou "nenhuma">
Agentes em curso: <pm-autoria: <id> | techlead: <id> | pm-converge: <id> | "—"> (só para continuar na mesma sessão)
Processo: <número, gravado pelo `fluxo.py iniciar`; features sem o campo valem 1>

| Repo | Onda | Fase | Ciclo | Último relatório |
|---|---|---|---|---|
| <nome> | <n> | pendente|dev|review|aprovado|bloqueado | <0-2> | <caminho> |

QA: pendente | dispensado | rodada <n>: APROVADO|REPROVADO
```

0. **Entrada** (PM):
   - Pedido sem spec → modo `entrevista`: o PM monta a spec de entrada no modelo `.agents/templates/spec-input.md`; lacunas viram pontos em aberto com default (protocolo 4.2).
   - Entrada que cobre mais de uma feature independente → modo `decomposição`: o PM propõe o recorte (features, dependências, ordem e MVP); o humano aprova (4.2) antes de qualquer specify. Cada feature aprovada segue o pipeline separadamente, na ordem aprovada.
1. **Constitution** (orquestrador) — somente se `.specify/memory/constitution.md` não existir ou estiver com o template vazio: `/speckit.constitution`.
2. **Specify** (PM de autoria, modo `specify`) — a seção **Stack técnico** da spec de entrada vai, sem alterações, para `specs/<f>/stack.md` (sem ela: repositórios em `stack: ?`); depois, `/speckit.specify` e, **no mesmo turno**, a rodada 1 do gate de clarificação (etapa 3).
3. **Gate de clarificação e triagem técnica** (BLOQUEANTE; uma parada só) — o PM de autoria (modo `clarify`) roda o `/speckit.clarify` em **modo lote**, somado à verificação do gate (o que verificar, formato do lote e rodada única: seção "Gate de clarificação" de `.agents/roles/pm.md`).
   - **Triagem**: quando o PM devolver o lote (`AGUARDANDO HUMANO: specs/<f>/clarifications.md`), dispare, antes de parar, um tech lead novo no modo `triagem` (seção "Triagem" de `.agents/roles/techlead.md`), com as skills de stack que `stack.md` indica (de `.agents/skills/` ou, se a etapa 4 ainda não as instalou, de `KIT/skills/`): ele lê o lote do PM e antecipa as perguntas técnicas e os limites. Gate aprovado sem perguntas → a triagem roda depois do plano, antes do tech lead do desenho (etapa 6).
   - **Uma parada**: os dois lotes vão ao humano numa mensagem só (protocolo 4.2), primeiro o do PM, e `Pendências do humano` leva os dois caminhos. Sem perguntas nos dois, siga sem parar.
   - **Lote grande**: se as decisões dos dois lotes somarem mais de 8 (contagem no topo de cada um), abra a mensagem avisando que a spec deixou muitas lacunas, com as seções que o PM indicou; o humano responde o lote ou completa a spec de entrada e diz "spec atualizada" (o PM trata as mudanças como respostas).
   - **Respostas**: as `Q` vão para `clarifications.md` e as `TQ` para `techlead/perguntas.md`; continue o PM citando os dois arquivos, no modo `clarify` (ele aplica as suas e as `TQ` que mudam requisito) ou, se a triagem rodou depois do plano, no modo `plan` (revisão) só quando alguma `TQ` mudar requisito. As `TQ` são o ponto de partida do tech lead do desenho.
   - **2ª rodada**: só quando uma resposta trouxer algo que nenhuma condicional previu, com o motivo registrado por quem pergunta; segue o mesmo caminho, numa parada só. Preveem-se no máximo 2 rodadas.
   **Gate aprovado** → no mesmo turno, o PM segue para o plan (etapa 5), com o Technical Context de `stack.md`; quando ele retornar, o orquestrador faz a etapa 4.
4. **Stack** (orquestrador; depois do gate aprovado e antes do tech lead) — aplique `stack.md`:
   - `workspace.yaml`: repositório com `stack: ?` → preencha `stack`, `version`, `runtime`, `frameworks`, `techs`, `tools` e `stack_source: spec`. Stack detectada → preencha só campos `?`/vazios e acrescente `techs`/`tools` novos; nunca troque um valor detectado, exceto pelo que o humano decidiu no gate.
   - Resposta "última estável" (ou equivalente) no gate: resolva a versão concreta em fonte oficial (registro do pacote ou página de releases), grave-a em `workspace.yaml` e em `stack.md` com a fonte e a data, e informe o humano numa linha.
   - Notas `.agents/repos/<repo>.md`: stack, runtime, fonte e os `commands` informados (`?` continua `?`; o dev define e reporta).
   - Skills: procedimento **Skills** da seção 0, instalando só as que faltam.
   - QA de integração: **desativado por padrão**. Leia `qa_integracao` de `stack.md`: só `sim`, escrito explicitamente na spec de entrada (seção `Execução`) ou no pedido do humano, ativa → `fluxo.py status <f> --qa pendente`; `não` ou campo ausente → `--qa dispensado`. Ninguém pergunta ao humano por isso; se ele pedir o QA depois, ative-o (`--qa pendente`) e prepare o ambiente de integração (etapa 10) antes da etapa 12.
5. **Plan** (PM de autoria, modo `plan`; em geral no mesmo turno do gate aprovado) — o PM executa o `/speckit.plan` e preenche a parte de produto: Technical Context só de `stack.md`/`workspace.yaml` (o plano não escolhe outra stack); cada requisito mapeado para um repositório do `workspace.yaml` (repositório novo é sinalizado e criado só com aprovação do humano); Constitution Check; `repos/<repo>/plan.md` com o que cada repositório entrega. O PM **ignora as fases técnicas do `/speckit.plan`** (pesquisa de tecnologia, contratos, modelo físico de dados): o Technical Context é cópia de `stack.md`/`workspace.yaml`, e tudo que o mapa 4.3 atribui ao tech lead fica como marcador `[TECH LEAD: <o que decidir>]`, inclusive `Desenho técnico: [TECH LEAD: decidir sim|não]` em cada repositório.
6. **Tech lead** (um agente novo por rodada, para a feature inteira) — roda **sempre**, exceto em trabalho pequeno (regra 8: um repositório existente, sem lib e com até 10 tarefas previstas), quando o orquestrador registra `Desenho técnico: não — trabalho pequeno` no plano do repositório e pula a etapa. Preenche tudo que o mapa 4.3 lhe atribui: os marcadores `[TECH LEAD: ...]` (contratos em `contracts/` **antes de qualquer código**, posse dos dados, versionamento, integração, decisões técnicas, `depends_on`), a parte física de `data-model.md`, as decisões técnicas e os limites em `research.md`, e a linha `Desenho técnico: sim|não — <motivo>` de **cada** repositório, com o desenho dos marcados `sim`. Os gatilhos do desenho por repositório (sempre, sim, não) estão em `.agents/roles/techlead.md`.
   - **Ponto de partida**: as respostas `TQ` da triagem (`techlead/perguntas.md`) e os `Limites prévios` do `research.md`. Pergunta técnica nova no desenho é exceção, com o motivo no relatório (`Perguntas fora da triagem`).
   - **Lib compartilhada** (skill `python-lib`): para cada necessidade técnica reutilizável dos consumidores (clientes AWS, SQS, S3, DynamoDB, segredos, STS, logs...), o tech lead decide pelo `CATALOGO.md` da lib — reusar, alterar (compatível), criar ou local — e registra na linha `Lib:` do `Desenho técnico` do consumidor. Alterar ou criar → a lib entra na feature como repositório (plano, desenho e tarefas próprias) e cada consumidor ganha `depends_on` nela, para que a lib vá numa onda anterior. Mudança incompatível na lib → protocolo 4.2.
   - **Limites da plataforma**: para cada fluxo de dados entre componentes, confronte o contrato com os limites dos serviços no pior caso (tamanho de mensagem e de dado entre estados, precisão numérica, tempo, taxa, tentativas), usando a `references/limites.md` da skill da stack quando houver. Registre em `research.md`, seção `Limites verificados` (limite, fonte, pior caso, resultado). Contrato que estoura o limite é corrigido **antes** de ser congelado (protocolo 4.2 se mudar requisito).
   - **Verificações com motor real**: para todo artefato avaliado por um motor externo (ASL e JSONata, políticas IAM, SQL, templates...) cujo teste de unidade só decodifica ou checa sintaxe, registre em `research.md`, seção `Verificações`, o motor que o avalia de verdade (nome, versão, como rodar sem credenciais) ou a lacuna explícita. As verificações viram tarefas dos repositórios e o `ambiente` (etapa 10) instala os motores.
   - **Skill proposta** → protocolo 4.2. Aprovada → copie-a para o kit (`KIT_LOCAL`, ou PR no `KIT_SOURCE`) e instale-a em `.agents/skills/` (procedimento **Skills** da seção 0); recusada → siga sem ela e registre a lacuna em `status.md`.
   - **Pergunta técnica ao humano** (requisito que a stack não atende como escrito, troca entre segurança, custo e operação, ferramenta fora da stack declarada) → o próprio tech lead grava o lote em `specs/<f>/techlead/perguntas.md` (protocolo 4.2). Resposta que muda a spec ou o plano de produto → o PM de autoria aplica a parte de produto (modo `plan`) antes de o tech lead continuar.
   - **`BLOQUEIO` do tech lead no plano de produto** (incoerência que não pede decisão do humano) → o PM revisa o plano (modo `plan`) e o tech lead volta (agente novo); persistindo, escale.
   - **Conferência**: ao retornar, rode `python .agents/bin/fluxo.py conferir-donos <f>`. Falha → o dono do item corrige uma vez (tech lead novo com a lista, ou PM); persistindo, escale.
7. **Tasks** (PM de autoria, modo `tasks`) — `/speckit.tasks`, seguindo o `Desenho técnico` de cada repositório (caminhos, ordem e, em repositório vazio, a tarefa de criar o documento de arquitetura); cada tarefa marcada com `[repo:<nome>]` e dividida em `repos/<repo>/tasks.md`.
8. **Analyze** (**PM novo**, modo `analyze`, só com os artefatos em disco) — `/speckit.analyze`. Confere também o mapa de donos (4.3): decisão técnica escrita em seção do PM, ou sem autor tech lead, vira achado `DONO`, e os técnicos vão ao tech lead. Críticos de produto: o PM corrige uma vez; críticos técnicos: o tech lead corrige uma vez. Persistindo, PARE e escale.
9. **Congelar contratos** (orquestrador) — rode `conferir-donos` de novo; só com OK, congele. A partir daqui, `contracts/` só muda com aprovação do humano.
10. **Ambiente** (orquestrador) — antes de delegar, deixe pronto tudo que os subagentes vão usar e registre em `.agents/env.md` (modelo: `.agents/templates/env.md`). Os subagentes não instalam ferramentas.
   - Ferramentas: interpretadores/SDKs e CLIs nas versões de `workspace.yaml` (`version`, `tools`) e os motores de verificação da seção `Verificações` do `research.md`. O que faltar é instalado no espaço do usuário, sem administrador, de fonte oficial e com checksum quando houver. Anote caminho ou forma de ativação e confira a versão.
   - Recursos externos: credenciais de nuvem (sim/não, perfil e região; nunca grave segredos), Docker, ambiente de integração. Com o QA ativo — Docker: confira se o daemon está rodando (inicie-o se preciso) e, se `integration/docker-compose.yml` existir, baixe as imagens antes do QA (`docker compose -f integration/docker-compose.yml pull --quiet`). **`QA: dispensado`**: não prepare nada do ambiente de integração (nem Docker, salvo ferramenta de build/teste de um repositório que o exija, nem `pull` de imagens, nem credenciais só para o QA) e registre no `env.md` `Ambiente de integração: dispensado (QA = não)`.
   - Restrições dos subagentes (ex.: sem `apply`, sem push).
   - Dependências de cada projeto (`pip install`, `npm install`...) não são instaladas aqui: o dev as instala com o comando de setup do `env.md`, depois de criar o manifesto.
   - O `env.md` vale para o workspace: nas features seguintes, só confira versões e instale o que faltar.
11. **Implement** — pelos subagentes por repositório da seção 5.3 (dev → reviewer, em ondas), **nunca** pelo `/speckit.implement`. Antes de abrir o dev de um repositório, rode `conferir-prontidao <f> <repo>`: falha → o dono do item (tech lead ou PM) corrige uma vez antes do dev; avisos vão no prompt do dev. O relatório do dev traz `Decisões não previstas` e o do reviewer marca `[handoff]`: são a medida da completude da entrega do PM e do tech lead. Quando um dev reportar `Comandos` para um repositório cujas notas tinham `?`, atualize `.agents/repos/<repo>.md`.
   - **`BLOQUEIO: lib`** (o consumidor precisa de um método genérico que não está no catálogo nem na linha `Lib:`) → continue o tech lead para a decisão e o PM de autoria (modo `tasks`) para as tarefas da lib; a lib passa por dev → reviewer antes de o consumidor continuar (o ciclo do consumidor não conta). Os outros repositórios da onda seguem.
12. **Converge** (**PM novo**, modo `converge`; as chamadas seguintes do converge continuam esse mesmo PM) — roda **antes do QA**, com todos os repositórios aprovados no review: é verificação estática e barata, e o QA só roda uma vez no código final. `/speckit.converge`, com os caminhos resolvidos dentro do repositório da marcação `[repo:<nome>]` (branch `feature/<f>`).
   - **Tarefas acrescentadas** (`## Phase N: Convergence`, já copiadas pelo PM para `repos/<repo>/tasks.md`) → reabra **apenas** o dev desses repositórios (seção 5.3, contando ciclo; o limite de 2 continua valendo), depois o reviewer. Em seguida, chame o converge de novo. O QA não roda enquanto o converge não convergir.
   - **Convergido** → siga para o QA (etapa 13) ou, com `QA: dispensado`, para o fechamento.
13. **QA de integração** — seção 6; **desativado por padrão**, só roda se a entrada o pedir. Com `QA: dispensado`, a etapa não existe: vá ao fechamento.
   - **Falhas do QA** → correção direta ou completa (seção 5.1). A correção do QA não reabre o converge, salvo se mudar a spec ou o plano (aí o PM de converge revisa o delta).
   - **Fechamento** (QA aprovado ou dispensado) → registre em `status.md` as lacunas que não são de código, de `reports/converge.md` e de `reports/integration/qa.md`, e derrube o ambiente de integração, se existir e ainda estiver ativo (`integration.down`).

### 4.1 Retomada ("continue a feature <f>" ou só "continue")
1. **Identifique a feature**: com nome, use `specs/<f>/`. Sem nome, liste as features em `specs/` cuja `Situação` não é `CONCLUÍDO`: se houver uma, use-a; se houver várias, pergunte qual (uma linha por feature: nome, etapa, situação).
2. **Leia somente `specs/<f>/status.md`**. Não releia spec, plano nem relatórios para "se situar"; leia apenas o que a etapa atual exigir.
3. **Confira o estado real** antes de agir (só checagens baratas): os artefatos da etapa atual existem; para repositórios em `dev`, a branch `feature/<f>` existe e há tarefas não marcadas em `tasks.md`. Se `status.md` divergir do disco, confie no disco, corrija o `status.md` e informe a divergência em uma linha.
4. **Retome a partir da etapa registrada**, nunca do início. Etapas concluídas não são refeitas.
   - `AGUARDANDO HUMANO` (entrada, clarify, decomposição, pergunta técnica ou skill): aplique o protocolo 4.2 — grave as respostas da mensagem atual no arquivo pendente e continue o papel no mesmo modo. Sem respostas na mensagem, reapresente o lote pendente e PARE.
   - `AGUARDANDO HUMANO` por **escalada**: aplique a decisão do humano e siga a `Próxima ação`. Sem decisão na mensagem, reapresente a pendência e PARE.
   - **techlead**: rode se ainda não houver `reports/techlead.md`, ou se o plano mudou depois dele.
   - **Agente de `Agentes em curso` que não pode ser continuado** (outra sessão, ferramenta sem esse recurso) → dispare um novo no mesmo modo; ele se situa pelo disco.
   - **implement**: retome somente repositórios que não estão `aprovado`, respeitando ondas e o `Ciclo` registrado (o limite de 2 ciclos continua valendo). Um dev interrompido continua a partir das tarefas não marcadas em `tasks.md`; não refaça as concluídas.
   - **converge**: se o `tasks.md` tiver uma fase `Convergence` com tarefas não concluídas, retome pelo dev dos repositórios delas; senão, chame o converge de novo. Convergido e QA ativo: vá ao QA.
   - **qa**: rode nova rodada retestando primeiro as falhas do último `qa.md`. Com `QA: dispensado`, a etapa não existe.
5. Contratos congelados continuam congelados na retomada.

### 4.2 Repasse ao humano
PM e tech lead não conversam com o humano: quando precisam de uma decisão, gravam o lote em arquivo e devolvem `AGUARDANDO HUMANO: <arquivo>`.

| Decisão | Arquivo |
|---|---|
| perguntas da entrevista | `specs/_input/<nome>.md` (pontos em aberto) |
| recorte de features | `specs/_input/decomposicao.md` |
| perguntas do gate de clarificação | `specs/<f>/clarifications.md` (rodada atual) |
| perguntas técnicas do tech lead | `specs/<f>/techlead/perguntas.md` (rodada atual) |
| proposta de skill | `specs/<f>/techlead/skills/<skill>/` + resumo em `reports/techlead.md` |

1. O orquestrador atualiza `status.md` (`AGUARDANDO HUMANO`, com o caminho do arquivo em `Pendências do humano`), mostra ao humano o lote do arquivo **sem reescrever nem resumir as perguntas** e PARA.
   O humano responde no chat ou preenche `Resposta do humano:` no próprio arquivo e diz "continue"; nesse caso, não transcreva: o arquivo já tem as respostas.
   **Gate e triagem juntos** (etapa 3): os dois arquivos na mesma mensagem, primeiro o do PM, cada lote sob o caminho do seu arquivo.
2. Na resposta, grava-a como veio no mesmo arquivo (campo `Resposta do humano`) e continua o papel no mesmo modo para aplicá-la (5.1). O orquestrador nunca aplica nem interpreta as respostas.
   Com dois arquivos, cada resposta vai para o do dono pelo prefixo: `Q` → `clarifications.md`, `TQ` → `techlead/perguntas.md`; o prompt de continuação cita os dois.
3. Quem pergunta confere a **compatibilidade**: cada opção, combinada com as decisões já tomadas e com as outras respostas possíveis do lote, tem de ser viável; combinações que se contradizem viram uma pergunta única ou condicionada ("se X, então...").

### 4.3 Donos dos artefatos
Cada artefato ou seção tem um único dono: o PM não escreve no que é do tech lead, e vice-versa. `python .agents/bin/fluxo.py conferir-donos <f>` verifica o que dá para checar por arquivo (marcadores sem resolver, linha `Desenho técnico` decidida, seções e relatório do tech lead, a seção `Verificações` do `research.md` (só em feature com `Processo` ≥ 2), contratos com `owner`, `consumers` e `version`, `depends_on`); o analyze confere o resto.
O mapa (artefato ou seção → dono) fica em `.agents/roles/donos.md`, lido pelo PM e pelo tech lead. Leia-o quando precisar rotear ao dono uma falha do `conferir-donos` ou um achado `DONO` do analyze.

Pendência do tech lead num artefato do PM: marcador `[TECH LEAD: <o que decidir>]`, que o tech lead substitui pela decisão. Marcador sem substituir bloqueia o congelamento dos contratos.

## 5. Delegação

### 5.1 Subagentes da feature
| Papel | Instruções | Skills | Modelo | Escreve |
|---|---|---|---|---|
| **pm** | `.agents/roles/pm.md` (modos: entrevista, decomposição, specify, clarify, plan, tasks, correcao, analyze, converge) | `sdd` + `spec-kit` | forte | artefatos de `specs/_input/` e `specs/<f>/` do modo (spec, clarifications, stack, plano de produto, tarefas, `reports/analyze.md`, `reports/converge.md`); somente leitura no código |
| **techlead** | `.agents/roles/techlead.md` (modos: triagem, desenho) | `architecture` + `sdd` + `clean-architecture` e `design-patterns` (se a feature tem repositório de back-end) + a skill da stack de cada repositório + condicionais; `skill-authoring` quando propõe skill | forte | `contracts/`, seções `[TECH LEAD]` do plano, `Desenho técnico` de cada repositório, `depends_on`, propostas de skill, `reports/techlead.md`; somente leitura no código |

**Continuidade dos agentes**
- **PM de autoria**: o mesmo agente da entrada (quando houver) ao tasks. Se a ferramenta permite continuar um subagente com o contexto preservado, o orquestrador o continua a cada etapa com o prompt de continuação (5.4) e registra o identificador em `Agentes em curso`; senão, ou se ele não puder mais ser continuado, dispara um PM novo no mesmo modo, que se situa pelo disco.
- **Correção direta** (padrão depois de falha do QA): vale quando o `qa.md` traz, por falha, causa, evidência e correção sugerida, e a correção **não muda** contrato, requisito, `depends_on` nem a lib. O orquestrador pula tech lead e PM: reabre só o dev dos repositórios afetados (ciclo +1), passando o caminho do `qa.md`; o dev acrescenta `## Phase N: Correção QA <rodada>` a `repos/<repo>/tasks.md` (uma tarefa por falha, teste antes da correção; exceção ao mapa de donos 4.3, registrada no relatório do dev). Depois, reviewer (diff incremental) e nova rodada de QA. Dúvida de desenho, contrato ou requisito apontada pelo dev ou pelo reviewer (`BLOQUEIO`) → correção completa.
- **correcao completa** (falha que muda contrato, requisito, `depends_on` ou lib, ou sem causa clara no `qa.md`): tech lead novo (relatório com `Para o PM` e a seção "Correções após o QA" do plano) → PM novo, modo `correcao`, que lê só o relatório do tech lead, as falhas do `qa.md` e a seção de correção do plano de cada repositório afetado, e acrescenta a fase de correção ao `tasks.md`. Não herda o contexto do PM de autoria.
- **analyze** e **converge**: sempre um PM novo, por independência; as chamadas seguintes do converge continuam esse PM.
- **tech lead**: um agente **novo a cada rodada** (primeira passagem, depois das respostas do humano, depois da revisão do PM, depois de falha do QA). Ele se situa por `reports/techlead.md` (campo `Retomada`), por `research.md` e pelos arquivos que o prompt diz que mudaram; o orquestrador não o continua com o contexto da rodada anterior.
- **tech lead de triagem**: agente próprio e curto na etapa 3; não é continuado: o do desenho é outro agente, que lê as respostas no disco.
- O disco continua sendo a fonte da verdade: todo agente grava o resultado de cada turno nos artefatos antes de retornar.

### 5.2 Ordem de execução (ondas)
1. Monte o grafo a partir de `depends_on` no `workspace.yaml`.
2. Agrupe em **ondas**: a onda 1 contém repositórios sem dependências; a onda N contém os que dependem só de ondas anteriores.
3. **Dentro de uma onda: em paralelo**, no máximo 3 repositórios simultâneos.
4. **Entre ondas: em sequência.** Uma onda só começa quando todos os repositórios da anterior passaram no review.
5. **Força sequencial** quando: contratos ainda não estão congelados, repositórios compartilham banco/biblioteca/código, ou houve escalada aberta.

### 5.3 Subagentes por repositório
```
dev ──► reviewer
 ▲          │
 └─ correção (máx. 2 ciclos)
```
| Papel | Instruções | Skills obrigatórias | Skills condicionais | Modelo | Escreve |
|---|---|---|---|---|---|
| **dev** | `.agents/roles/dev.md` | skill da stack do repo + `unit-testing` + `clean-code-solid`, `clean-architecture` e `design-patterns` (regra abaixo) | por gatilho da tarefa (ex.: mensageria, infra) | forte | código + testes unitários; `reports/<repo>/dev.md` |
| **reviewer** | `.agents/roles/reviewer.md` | `code-review` + skill da stack do repo + `clean-code-solid`, `clean-architecture` e `design-patterns` (regra abaixo) | as mesmas condicionais que o dev carregou | forte | somente `reports/<repo>/review.md` (somente leitura no código) |

- O orquestrador decide as skills condicionais lendo `repos/<repo>/tasks.md` e o índice da seção 3, e as informa explicitamente no prompt. O subagente não procura skills por conta própria.
- `clean-code-solid`: todo repositório de aplicação, de back-end ou de front-end; nunca IaC (`terraform`). `clean-architecture` e `design-patterns`: só repositório de back-end (stack `dotnet`, `python`, `node`, `go` ou `java`), exceto biblioteca (`kind: lib`); repositório de front-end (`react`, `angular`, `vue`) nunca as recebe.
- Só achados `bloqueante` do reviewer voltam para o dev; `sugestão` fica registrada no relatório.
- **Ciclo de correção enxuto**: o prompt do dev lista as tarefas da fase de correção; ele lê só elas, a seção de correção do `plan.md` e os arquivos que o relatório anterior cita, não o plano inteiro. O reviewer julga só o diff incremental.

### 5.4 Template do prompt de delegação (mantenha curto assim)
```
Papel: <pm|techlead|dev|reviewer|qa>. Repo: <nome> em <path do workspace.yaml> (pm, techlead e qa: "todos da feature"). Stack: <stack>. Feature: <f>. Idioma: <IDIOMA>.
Modo: <pm: entrevista|decomposição|specify|clarify|plan|tasks|correcao|analyze|converge; techlead: triagem|desenho>
Leia, na mesma chamada: .agents/roles/<papel>.md (ele diz o que mais ler) e .agents/skills/token-efficiency/SKILL.md.
Carregue as skills (e somente elas): <obrigatórias> + <condicionais>
Retorne: resumo de no máximo 15 linhas (pm, techlead e qa: 3 linhas).
```
Prompt de continuação (mesmo agente, contexto preservado):
```
Continuação. Modo: <modo>. Mudou: <arquivos com Resposta do humano ou alterados por outro papel>.
Retorne: resumo de no máximo 3 linhas.
```
O ambiente não vai no prompt: os papéis leem `.agents/env.md`.

### 5.5 Modo de execução (portabilidade)
- **Ferramenta com suporte a subagentes**: dispare um subagente por papel (e por repositório, no caso de dev e reviewer) com o template 5.4. Se a ferramenta permitir, restrinja pm, techlead, reviewer e qa a somente leitura no código e use o modelo indicado nas tabelas.
- **Ferramenta sem suporte a subagentes (fallback)**: execute os papéis em sequência na própria sessão, seguindo a ordem do pipeline e das ondas. Antes de cada papel, leia o arquivo de papel e **siga-o como se fosse outro agente**: o reviewer julga somente pelo `git diff` e pelos artefatos, e o analyze e o converge do PM, somente pelos artefatos em disco, não pelo que você lembra de ter escrito. Ao terminar cada papel, registre o resultado em `status.md` e, se a ferramenta permitir, compacte/limpe o contexto.

## 6. QA de integração (um único agente, ao final)
Executa depois que todos os repositórios passaram no review **e o converge convergiu** (etapa 12), e **só se o QA tiver sido pedido explicitamente** (`QA de integração: sim` na spec de entrada, ou pedido do humano). Por padrão ele fica desativado (`QA: dispensado`): esta seção e o preparo do ambiente de integração (etapa 10) não existem.

| Papel | Instruções | Skills | Modelo | Escreve |
|---|---|---|---|---|
| **qa** | `.agents/roles/qa.md` | `qa-integration` + condicionais de integração (ex.: mensageria) | econômico | `reports/integration/qa.md` |

- Falhas vêm atribuídas a um repositório. O orquestrador escolhe a **correção direta** ou a completa (seção 5.1) e reabre o dev **apenas** dos repositórios afetados (respeitando o limite de ciclos).

## 7. Escale para o humano (e PARE) quando
- a preparação não encontrar repositórios, não conseguir obter o kit ou instalar o Spec Kit
- faltar no kit uma skill exigida (preparação ou etapa `stack`)
- a etapa `ambiente` não conseguir instalar uma ferramenta declarada
- a stack de um repositório envolvido continuar `?` depois do gate, ou a spec divergir do detectado
- o PM ou o tech lead devolverem `AGUARDANDO HUMANO` (entrevista, recorte de features, gate de clarificação, pergunta técnica, proposta de skill) — protocolo 4.2
- o tech lead mantiver `BLOQUEIO` no plano depois de uma revisão do PM
- um contrato precisar mudar depois de congelado (afeta outros repositórios), ou a lib compartilhada precisar de mudança incompatível
- os ciclos de correção se esgotarem, ou o analyze tiver achados críticos não resolvidos
