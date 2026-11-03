# Spec Kit — comandos em detalhe (validado em 1.2.4.dev0)

Todos os comandos começam verificando hooks em `.specify/extensions.yml` (`before_<cmd>`) e terminam verificando `after_<cmd>`. Scripts ficam em `.specify/scripts/python/` (com `--script py`) e imprimem JSON com `--json`.

## constitution
- Cria ou atualiza `.specify/memory/constitution.md` a partir de princípios informados, com versionamento semântico (`CONSTITUTION_VERSION`: MAJOR/MINOR/PATCH). Só altera a própria constitution; não escreve nos templates.
- Neste kit: a constitution do time vem de `templates/constitution.md` do kit; o comando só roda se o arquivo estiver vazio ou com o template padrão.

## specify
- Entrada: a descrição da feature (o texto após o comando).
- Passos: gera um nome curto (2 a 4 palavras); cria `specs/<prefixo>-<nome>/` (prefixo `NNN` sequencial ou `AAAAMMDD-HHMMSS`, conforme `feature_numbering` em `.specify/init-options.json`); copia o `spec-template.md`; grava `.specify/feature.json` (`feature_directory`); escreve a spec; cria `checklists/requirements.md` e valida a spec contra ele (até 3 iterações).
- Regras do comando: no máximo 3 `[NEEDS CLARIFICATION]`; critérios de sucesso mensuráveis e sem tecnologia; sem checklist embutido na spec.
- Branch git: só via hook da extensão git (não usada neste kit).

## clarify
- Faz uma varredura de cobertura por categorias — escopo funcional e comportamento; domínio e modelo de dados; fluxo de interação/UX; atributos de qualidade não funcionais; integrações e dependências externas; casos de borda e falhas; restrições e trade-offs; terminologia e consistência; sinais de conclusão; pendências/placeholders — marcando cada uma como Clear/Partial/Missing.
- Monta uma fila priorizada de no máximo 5 perguntas (impacto × incerteza). Cada pergunta tem opções (tabela) ou resposta curta, com **opção recomendada** em destaque.
- Original: pergunta uma por vez. **Neste kit: modo lote** — a fila inteira vai num lote único, somada às lacunas do gate (stack agrupada em uma pergunta extra).
- Gravação: `## Clarifications` (logo após a seção de contexto) › `### Session AAAA-MM-DD` › `- Q: <pergunta> → A: <resposta>`, e atualização da seção afetada (requisito, entidade, caso de borda...).
- Ao final: resumo de cobertura por categoria (Resolved, Deferred, Clear, Outstanding).

## plan
- Script: `python .specify/scripts/python/setup_plan.py --json` → `FEATURE_SPEC`, `IMPL_PLAN`, `FEATURE_DIR`, `BRANCH`; copia o `plan-template.md` para `plan.md`.
- Fluxo: Technical Context (desconhecidos viram `NEEDS CLARIFICATION`) → Constitution Check (gate; violação sem justificativa é erro) → Fase 0: `research.md` (Decisão/Motivo/Alternativas, resolvendo todos os desconhecidos) → Fase 1: `data-model.md`, `contracts/`, `quickstart.md` → Constitution Check de novo.
- Exceções justificadas vão em **Complexity Tracking**.
- Neste kit: Technical Context só de `stack.md`/`workspace.yaml`; contratos entre repositórios; planos por repositório com a linha `Tech lead`.

## tasks
- Script: `python .specify/scripts/python/setup_tasks.py --json` → `FEATURE_DIR`, `TASKS_TEMPLATE`, `TASKS_TEMPLATE_CONTENT`, `AVAILABLE_DOCS`.
- Formato obrigatório: `- [ ] T### [P?] [US#?] descrição com caminho`. `[P]` só para tarefas paralelizáveis (arquivos diferentes, sem dependência pendente); `[US#]` só nas fases de história.
- Fases: Setup → Fundação (bloqueia as histórias) → uma fase por história, em ordem de prioridade (testes → modelos → serviços → integração) → Acabamento. Mais as seções de dependências, paralelismo e estratégia (MVP primeiro).
- Testes: o comando só gera se pedidos; a constitution deste kit (§26) torna-os obrigatórios.
- Neste kit: acrescentar `[repo:<nome>]`, seguir o Desenho técnico, dividir em `repos/<repo>/tasks.md`.

## analyze
- Script: `python .specify/scripts/python/check_prerequisites.py --json --require-spec --require-tasks --include-tasks`.
- Somente leitura. Passadas: duplicação, ambiguidade, subespecificação, alinhamento com a constitution, lacunas de cobertura, inconsistência. No máximo 50 achados.
- Severidade: **CRÍTICO** (viola regra DEVE da constitution, falta artefato central, requisito sem cobertura que bloqueia o básico), ALTO, MÉDIO, BAIXO. Conflito com a constitution é sempre crítico.
- Saída: tabela de achados, cobertura por requisito, tarefas sem requisito, métricas, próximas ações.
- Neste kit: gravar em `reports/analyze.md`; corrigir críticos uma vez; persistindo, PARE.

## converge
- Roda depois da implementação. Lê `spec.md`, `plan.md` e `tasks.md` como única fonte da intenção; monta o mapa de código a partir dos caminhos citados e de busca por conceitos; classifica achados (não feito, parcial, contraditório, excedente).
- **Só acrescenta**: uma seção `## Phase N: Convergence` no fim do `tasks.md`, com IDs continuando a numeração; nunca altera tarefas existentes nem código. Convergido → `tasks.md` intacto e mensagem "Converged".
- Neste kit: caminhos resolvidos dentro do repositório da marcação `[repo:<nome>]`; tarefas novas reabrem o dev desses repositórios (limite de ciclos).

## implement
- Executa as tarefas do `tasks.md` com um único agente. **Não usado neste kit**: tech lead → dev → reviewer por repositório (seção 5 do `AGENTS.md`).

## checklist
- Gera checklists de qualidade dos requisitos para um tema (ex.: segurança, acessibilidade), em `checklists/`: são "testes unitários da escrita dos requisitos" (clareza, completude, consistência), não testes do código. O `checklists/requirements.md` é o checklist próprio do specify/clarify. Opcional neste kit.

## taskstoissues
- Converte tarefas em issues do GitHub. Descontinuado.
