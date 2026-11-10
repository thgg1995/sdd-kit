# sdd-kit

Kit versionado do processo Spec-Driven. Mantenha-o num repositório próprio (ex.: `minha-org/sdd-kit`).

```
AGENTS.md             # configuração e roteamento; é o único arquivo que vai para a raiz de cada workspace
orquestrador.md       # roteiro do orquestrador (pipeline); a preparação o copia para .agents/
preparacao.md         # preparação do workspace, lida do kit quando o workspace é preparado
roles/                # pm, techlead, dev, reviewer, qa e donos.md (mapa de donos, lido por pm e techlead)
bin/                  # fluxo.py (registro do fluxo), consumo.py (consumo real de tokens, pelos transcritos), janela.py (acompanhamento em janela, abre sempre sozinha) e painel.py (o mesmo no terminal, só se a janela não abrir)
python_lib/           # biblioteca Python compartilhada (repositório git próprio; consumida do kit, não copiada)
skills/
  catalog.yaml        # quando cada skill é instalada e o gatilho no índice
  <skill>/SKILL.md    # suas skills (padrão Agent Skills)
  <skill>/references/ # detalhes da skill, lidos sob demanda
templates/
  workspace.yaml
  repo-notes.md
  spec-input.md       # modelo da spec de entrada (inclui a seção "Stack técnico")
  env.md              # modelo do ambiente preparado para os subagentes (etapa `ambiente`)
  constitution.md     # opcional: constitution padrão do time
```

## Biblioteca compartilhada
A `python_lib/` vive no kit, com o próprio `.git`. A preparação a registra no `workspace.yaml` (`kind: lib`, `source: kit`, `path: ../sdd-kit/python_lib`) e os repositórios Python a consomem de lá. O tech lead decide, pelo `CATALOGO.md` dela, se cada necessidade técnica dos consumidores reusa, altera ou cria um método na lib (skill `python-lib`); as alterações são commitadas na própria lib, no kit.

## Como usar
A janela de acompanhamento exibe um escritório em pixel art, com luminárias, plataformas, janela, plantas e um DEV descansando no sofá até o fluxo terminar. O painel à direita mostra progresso, etapa, situação, agente responsável e tempos calculados pelos eventos registrados. A área inferior mantém sempre visíveis a lista de etapas, os detalhes e os logs, com rolagem e opção de acompanhar automaticamente os eventos novos. As etapas concluídas ficam verdes; a atual fica amarela, com o orquestrador aguardando abaixo da mesa. A barra usa os passos anteriores à etapa atual sobre o total e exclui QA dispensado. Sem dados de tempo ou agente, o painel mostra “—”. Os nomes originais das etapas são preservados. Tudo usa tkinter, sem dependências externas.

Para experimentar o visual, execute `python bin/demo_janela.py`. A demonstração percorre automaticamente os 14 passos com dados simulados. Feche a janela pelo “X” para encerrar. Os componentes visuais ficam em `bin/interface.py`, copiado junto aos demais scripts na preparação.

Validação do painel: `python -B -m unittest discover -s tests`. Os testes de interface precisam de tkinter e de uma sessão gráfica.

1. Coloque suas skills em `skills/<nome>/SKILL.md` e registre cada uma no `catalog.yaml`.
2. Crie uma pasta de workspace e clone dentro dela os repositórios necessários.
3. Copie o `AGENTS.md` deste kit para a raiz do workspace e ajuste `KIT_SOURCE` e `IDIOMA`. Se a sua ferramenta de IA não ler `AGENTS.md` sozinha, crie o arquivo de instruções dela com uma linha apontando para ele (ex.: `CLAUDE.md` com `@AGENTS.md`; `GEMINI.md`, ou `contextFileName: AGENTS.md` nas configurações do Gemini CLI).
4. Escreva a spec seguindo `templates/spec-input.md`. A seção **Stack técnico** é obrigatória para repositórios vazios ou com stack não detectada (stack, versão, runtime, techs). Para os demais, ela é opcional e confirma o que foi detectado.
5. Abra qualquer agente de IA na raiz do workspace (o processo não depende de fornecedor: sem subagentes, os papéis rodam em sequência; o Spec Kit é instalado para o agente em uso) e peça: "implemente a spec em <arquivo>". Na primeira vez, o `AGENTS.md` obtém o kit e a preparação do workspace (`preparacao.md`) roda sozinha.

## Como escrever uma skill
O padrão completo (estrutura, regras verificáveis, catálogo e checklist) está na skill `skills/skill-authoring/`, que o tech lead segue ao propor skills. Resumo:
Toda skill usa divulgação progressiva: o essencial sempre é lido; o detalhe, só quando a tarefa pede.
```
skills/<skill>/
  SKILL.md              # sempre lido pelo subagente
  references/
    <assunto>.md        # lido só quando o gatilho do índice corresponder à tarefa
```
- **`SKILL.md`, no máximo 150 linhas** (a preparação do workspace avisa quando passar):
  - frontmatter `name` + `description`;
  - as regras que valem para qualquer tarefa da skill (o que é obrigatório e o que é proibido, com a seção da constitution que cada uma detalha);
  - um índice de referências, uma linha por arquivo, com o gatilho de leitura:
    `- references/iam.md — ler quando a tarefa cria ou altera role/policy`.
- **`references/`**: exemplos, padrões completos, tabelas e casos especiais. Pode crescer à vontade; cada arquivo trata de um assunto e deve ser entendível sozinho.
- Regra estrutural (layout do projeto, convenções que afetam a primeira tarefa) fica no `SKILL.md`, nunca só em `references/`, para não haver retrabalho.
- Registre a skill no `catalog.yaml` (`stacks`/`techs`/`always`, `trigger`, `loaded_by`, `rules`).
- Exemplos de código em Python e C# seguem a convenção de `skills/skill-authoring/references/modelo.md` e são validados com `python -I tests/validar_exemplos.py skills/<skill>` (lint, build e testes).

## Uso eficiente de tokens

A skill [`token-efficiency`](skills/token-efficiency/SKILL.md) traz as regras de economia que todo agente segue: chamadas agrupadas, leitura por trecho, saída curta de comandos, escrita por trecho e artefatos sem repetição. Ela é instalada sempre (`always: true`) e lida por todos os papéis junto com o arquivo do papel; o orquestrador a lê logo depois do roteiro (regra 5 da seção 1 e template 5.4 do `orquestrador.md`). Cada regra cita a métrica que a confere.

O consumo real sai do `bin/consumo.py`, que soma o uso de cada chamada nos transcritos do Claude Code ou do Codex e grava um relatório com as métricas da skill e, ao lado, os indicadores de qualidade da execução:
```
python .agents/bin/consumo.py <feature>     # num workspace: grava specs/<feature>/reports/consumo.md
python bin/consumo.py <feature> --raiz <workspace> --ate <AAAA-MM-DDTHH:MM> --saida <arquivo>   # a partir do kit
```
O `tokens` que o `fluxo.py` registra, e que o painel soma, é o contexto final de cada subagente, não o consumo. Como medir e comparar versões do kit: [`references/medicao.md`](skills/token-efficiency/references/medicao.md).

## Alterações recentes

### 2026-11-10 — uso eficiente de tokens
O consumo das execuções da feature 001 foi medido pelos transcritos das ferramentas, e não pelo número que o fluxo registra. Três descobertas guiaram as mudanças:
- O `tokens` registrado no `eventos.jsonl` é o contexto final de cada subagente, não o consumo. No teste3, o registrado foi 2,2 mi e o real, 47,0 mi; o orquestrador nem era registrado.
- O consumo é o número de chamadas vezes o contexto relido em cada uma. Cada subagente começa com 37 a 52 mil tokens no Claude Code (cerca de 25 mil no Codex) antes de ler qualquer arquivo, e cada resultado de ferramenta volta em todas as chamadas seguintes.
- O orquestrador está entre os maiores consumidores: de 28% a 40% nas execuções do Claude Code (no teste3, empatado com o dev e o QA) e 57% dos agentes de trabalho no Codex, onde só as esperas custaram 25% da execução.

| Tema | O que muda |
|---|---|
| Skill | `token-efficiency` reescrita: lida por todos os papéis, junto com o arquivo do papel |
| Medição | `bin/consumo.py` (consumo e qualidade de cada execução) e `tests/test_consumo.py`, novos |
| Processo | regra 5 da seção 1, registro do consumo e template 5.4 do `orquestrador.md` |
| Papéis | as regras de saída curta saem de dev, qa, pm e techlead e vão para a skill |

#### Skill `token-efficiency` (`SKILL.md` com 45 linhas e 2 referências)
- Abre pelo mecanismo: cada chamada relê todo o contexto, e o que entra nele volta em todas as chamadas seguintes.
- Salvaguarda: a economia nunca dispensa as leituras integrais, os donos, os gates nem as verificações obrigatórias. Leituras integrais são:
  - o roteiro, o papel e o `SKILL.md` das skills indicadas;
  - os arquivos de comando do Spec Kit;
  - o que o papel manda ler sem dizer "por trecho";
  - os artefatos que o analyze e o converge comparam.

  Na dúvida entre decidir por um trecho e ler mais, a regra é ler mais.
- Cada regra cita a métrica do `consumo.py` que a confere:
  - chamadas independentes na mesma resposta;
  - comandos de shell num comando só; no PowerShell 5.1, `;` só entre leituras e `if ($?)` quando há escrita;
  - espera pela notificação de término, sem laço;
  - repetir igual um comando que falhou só se o erro for passageiro;
  - começar pelos caminhos que a tarefa, o plano ou o diff citam;
  - não reler o que continua no contexto e não mudou; depois de contexto resumido, reler o que a decisão exige;
  - arquivo com mais de 200 linhas lido por intervalo, ampliado até a unidade inteira;
  - busca fora de dependências e saídas de build (`bin` só quando é saída de build);
  - usar o comando que o repositório ou o ambiente declaram, com as opções que só reduzem a saída;
  - saída longa num arquivo, deixando no contexto o código de saída e o trecho que a decisão usa;
  - arquivo existente alterado por trecho;
  - artefato que cita ID e caminho em vez de copiar, salvo na fatia que um papel lê sozinho (`repos/<repo>/`);
  - no orquestrador, registro no `fluxo.py` junto com a ação seguinte e, dos artefatos, só o que o roteiro manda ler.
- `references/comandos.md`:
  - a precedência do comando declarado;
  - a forma silenciosa dos comandos de Python, .NET, Terraform, Docker, Node, git e busca;
  - como ver o detalhe de uma falha.

  Cada linha foi verificada rodando o comando ou, quando marcada, no `--help`; o `uv` ficou como não verificado.
- `references/medicao.md`: o que medir, onde ficam os transcritos de cada ferramenta, como recortar a execução, as métricas, os indicadores de qualidade e como comparar versões do kit.
- A versão anterior, que não chegou a ser commitada, tinha dois problemas:
  - só era lida quando alguém pedia economia de tokens, e só pelo orquestrador, então não alcançava os agentes que mais gastam;
  - mandava medir pelo número que a ferramenta informa, que é o contexto final.

#### Auditoria de qualidade, antes do commit
Cada regra foi revista com a pergunta "um agente que a siga ao pé da letra entrega um trabalho pior?". A primeira versão desta mudança tinha os problemas abaixo, todos corrigidos:

| Risco | Correção |
|---|---|
| A tabela de comandos podia substituir o comando que o repositório declara (ex.: `uv run pytest`, o `integration.up` do QA) | Vale o comando declarado; da tabela, só as opções que reduzem a saída |
| Regressão: o exemplo antigo do QA tinha `terraform apply -auto-approve`, e a consolidação o perdeu. Sem ele, o apply não interativo falha | Linha própria para o apply no ambiente de teste; na pipeline, vale o plano salvo |
| "Cite o ID em vez de copiar" deixaria o dev e o reviewer sem o requisito, porque eles leem só a fatia `repos/<repo>/` | Exceção para a fatia que um papel lê sozinho |
| A regra de não reler tinha perdido o "que está em contexto": depois de o contexto ser resumido, o agente trabalharia só com o resumo. E `git diff` não serve para `specs/` | Não reler só o que continua no contexto; o que mudou vem do prompt de continuação ou do relatório; depois de um resumo, reler |
| `dotnet build -clp:ErrorsOnly` mostra só a contagem de avisos (testado: "2 Aviso(s)"), e um aviso novo passaria despercebido | `dotnet build --nologo -v q`, com um aviso por linha |
| "No contexto, só o código de saída e o erro" esconderia a saída útil de um comando que deu certo (ex.: o que um plan vai criar) | "…e o trecho que a decisão usa: o erro, o resumo ou as linhas buscadas" |
| No PowerShell 5.1, o `;` continua depois de uma falha | `;` só entre leituras; com escrita, `if ($?) { … }` |
| O `--wait` acrescentado ao `docker compose up` mudava o comportamento do exemplo antigo | Retirado; vale o `integration.up` |
| "Mude a hipótese antes de repetir" desestimulava repetir uma falha passageira | Repetir igual só se o erro indicar falha passageira |
| Excluir `bin` da busca esconderia código onde `bin/` é fonte, como neste kit | Excluir `bin` só quando é saída de build |
| A regra das 200 linhas poderia alcançar leituras que o papel exige inteiras e os artefatos do analyze. Hoje não alcança: planos até 110 linhas, tarefas até 94, constitution com cerca de 60 | Salvaguarda explícita das leituras integrais |
| `pytest --tb=short` pode não bastar para diagnosticar uma falha | Em falha, rodar só o teste, com `--tb=long` |

A auditoria também trouxe:
- **Busca extra evitada:** da versão anterior, "comece pelos caminhos que a tarefa, o plano ou o diff citam", que evita uma busca a mais (cada chamada extra relê o contexto inteiro).
- **Métricas como indícios:** o relatório e a `medicao.md` dizem que as métricas são indícios, não portões.
- **Mais duas funções no `consumo.py`:** a seção de qualidade e o aviso de chamadas antes do início da feature.

#### Medição (`bin/consumo.py`)
- Lê os transcritos do Claude Code (`~/.claude/projects/...`, com a sessão e a pasta `subagents/`) e do Codex (`~/.codex/sessions/`, filtrados pelo `cwd`).
- Soma cada chamada nos quatro tipos (entrada nova, escrita de cache, leitura de cache e saída) e grava `specs/<f>/reports/consumo.md`, com:
  - o resumo e o consumo por papel, com o registrado ao lado;
  - a qualidade da execução:
    - rodadas do tech lead e paradas para o humano;
    - analyze e passagens do converge;
    - rodadas e resultado do QA;
    - achados `[handoff]`;
    - por repositório, as execuções do dev e as revisões reprovadas;
  - o consumo por agente e as métricas da skill;
  - os resultados de ferramenta mais caros (tokens × chamadas que os releem);
  - os parágrafos copiados entre artefatos.
- O fim da feature é o evento CONCLUÍDO do `eventos.jsonl`. O script avisa quando há chamadas mais de 2 h antes do primeiro evento ou depois do fim, e sugere o recorte; `--desde` e `--ate` recortam.
- Sem dependências, no Python 3.10 ou mais novo. A preparação já o copia para `.agents/bin/` com os demais scripts.

#### Processo e papéis
- `orquestrador.md`:
  - a regra 5 da seção 1 ("Ler uma vez") vira "Comportamento econômico", que aponta para a skill; o orquestrador a lê logo depois do roteiro;
  - no template 5.4, o subagente lê o papel e a skill na mesma chamada;
  - o consumo que chega depois do `fim` é registrado na mesma resposta da próxima ação, sem uma chamada só para isso, e o texto explica que o número é o contexto final;
  - a seção 2 lista o `bin/consumo.py`.
- `roles/dev.md`, `qa.md`, `pm.md` e `techlead.md`: a "Saída curta", o "Em falha" e a leitura por trecho dão lugar a uma linha que aponta para a skill. O limite de tentativas e o que cada papel lê continuam nos papéis.
- `skills/catalog.yaml`: `loaded_by` de todos os papéis, com o gatilho "início do trabalho de qualquer papel".

#### Como validar
```
python -B -m unittest tests.test_consumo
python bin/consumo.py 001-disparo-cadastro-lote --raiz ../teste4_codex --ate 2026-11-01T20:31 --saida <arquivo>
```
- Os 11 testes passam no Python 3.10 e no 3.14, e o ruff não aponta nada.
- O `consumo.py` reproduz a auditoria de consumo do teste4 (Codex), feita à parte: recortado em 2026-11-01T20:31, dá 16.475.641 tokens no orquestrador e 28.745.128 nos 14 agentes de trabalho, os números de `reports/auditoria-consumo.md`.
- Linha de base da feature 001, recortada do pedido que iniciou cada execução até o CONCLUÍDO:

  | Execução | Recorte | Total | Orquestrador | Destaque |
  |---|---|---:|---:|---|
  | teste1 (Claude Code) | `--desde 2026-10-31T20:33 --ate 2026-11-01T00:25` | 73,3 mi | 39,5% | sessão sem limpeza: o orquestrador começou com 174 mil tokens de contexto |
  | teste2 (Claude Code) | `--ate 2026-11-01T02:10` | 21,2 mi | 35,9% | sem QA |
  | teste3 (Claude Code) | `--ate 2026-11-01T17:31` | 47,0 mi | 27,8% | dev 27,9% e QA 26,2%; um QA de 76 chamadas consumiu 10 mi |
  | teste4 (Codex) | `--ate 2026-11-01T20:31` | 31,8 mi | 51,7% | 86 esperas do orquestrador: 8,0 mi (25%); aprovação de permissões: 3,1 mi |

  A seção de qualidade do relatório dá o outro lado da comparação. No teste3, por exemplo:
  - 3 rodadas do tech lead;
  - converge em 2 passagens;
  - QA em 3 rodadas, com 13 de 14 critérios;
  - no `infra_process`, 3 execuções do dev e 1 revisão reprovada.
- A sessão do teste1 juntava dias de conversa e execuções anteriores. Sem o recorte no início, o total sobe para 234,5 mi; o aviso novo do script aponta esse caso.

#### Pendências conhecidas
- O efeito da skill ainda não foi medido. Falta rodar a feature 001 com o kit novo, 2 a 3 vezes, e comparar consumo e qualidade com a linha de base. As execuções antigas usaram versões diferentes do kit; a comparação mais limpa também roda o kit sem a skill.
- O limite de 200 linhas é um ponto de partida: num arquivo pouco acima disso, a busca extra pode custar mais que a leitura inteira. Precisa ser calibrado com as medições.
- Mudanças de estrutura, fora do alcance de uma skill:
  - trocar o registro de consumo do orquestrador pelo `consumo.py`;
  - tirar a preparação do contexto do orquestrador;
  - sugerir `/clear` e `continue` nas paradas para o humano;
  - reduzir o contexto de partida dos subagentes (ferramentas por papel, sem conectores que o fluxo não usa);
  - pôr um teto de chamadas por agente.
- O painel continua chamando de consumo o contexto final registrado.

### 2026-11-09 — arquitetura de back-end, Clean Code e SOLID, padrões de projeto e Terraform
Estas mudanças dão ao tech lead, ao dev e ao reviewer padrões escritos para três assuntos que o kit não cobria: a estrutura interna das aplicações de back-end, a escrita do código (Clean Code, SOLID e padrões de projeto) e a IaC com Terraform. Os exemplos de código das skills passam a ser validados por script. A primeira parte (a skill `clean-architecture`, a primeira versão da `clean-code` e o §32) já está no commit `8bef73a`; o resto entra neste commit.

| Tema | O que muda | Commit |
|---|---|---|
| Constitution | §32 (versão 2.1.0) e §33 (2.2.0) | `8bef73a` e este |
| Arquitetura de back-end | skill `clean-architecture`, com níveis 0 a 3 | `8bef73a` |
| Código | `clean-code` vira `clean-code-solid`, com SOLID e 5 referências com exemplos | este |
| Padrões de projeto | skill `design-patterns`, com 26 referências | este |
| Terraform e AWS | skill `terraform`; `aws-infra` e `aws-serverless` reorganizadas | este |
| Validação de exemplos | `tests/validar_exemplos.py` | este |
| Processo | skills por papel, regra 8 do orquestrador, tech `terraform` | `8bef73a` e este |

#### Constitution (`templates/constitution.md`, 2.0.0 → 2.2.0)
- **§32** (2.1.0, `8bef73a`): "No back-end, regra de negócio NUNCA depende de framework, SDK, driver ou formato de transporte; entrada e saída ficam em adaptadores."
- **§33** (2.2.0): "Recurso que guarda dado persistente DEVE ter proteção contra destruição acidental." Fica na seção V, depois do §23, separado por um comentário HTML para o Markdown não renumerar a lista. A numeração não muda porque as skills citam as regras pelo número.

#### Skills novas
**`clean-architecture`** (`8bef73a`; `SKILL.md` com 75 linhas e 6 referências)
- Estrutura interna proporcional à regra de negócio: nível 0 (sem regra: integração direta, ou adaptador chamando adaptador), 1 (um caso de uso: três módulos), 2 (serviço: pastas por camada) e 3 (domínio rico). Na dúvida entre dois níveis, vale o menor.
- Tabela de camadas (domain, application, entrypoints, infrastructure e composition root) com o que cada uma pode importar; regras dos níveis 1 a 3 (adaptador de entrada, tipos, erros, portas, composition root, transação); proibições (classe que só repassa, repositório genérico, pasta `utils/`, mediator e CQRS sem decisão registrada).
- Só back-end (`dotnet`, `python`, `node`, `go`, `java`), exceto biblioteca; nunca front-end nem IaC.
- Referências por papel da aplicação: `api.md`, `consumer.md`, `producer.md`, `tarefa-orquestrada.md`, `job.md` e `dominio-rico.md` (nível 3).
- Os nomes de pastas e projetos de cada nível estão na `python-backend` e na `dotnet-backend` (seção "Estrutura (§32)").

**`clean-code-solid`** (substitui a `clean-code` de `8bef73a`, renomeada com `git mv`; `SKILL.md` com 91 linhas e 5 referências)
- Clean Code: limites do linter (complexidade até 10 e parâmetros até 5; o ruff mede os dois com `C901` e `PLR0913`; no .NET, a CA1502 mede a complexidade e o reviewer confere os parâmetros), nomes, funções, classes e módulos, objetos e dados, erros, comentários, simplicidade e concorrência.
- SOLID: uma tabela com a regra verificável de cada princípio e, no back-end, a skill que aplica a parte estrutural.
- "Fora desta skill": formatação, testes, fronteira com terceiros, composition root e tipos de erro apontam para a skill dona do assunto.
- Vale para back-end e front-end (`react`, `angular`, `vue`); nunca IaC.
- Sem repetição, três regras vieram de outras skills, que agora só apontam para cá:
  - composição em vez de herança, que estava na `design-patterns`;
  - interface com uma implementação só, que estava na `clean-architecture` e virou a linha O;
  - "diga, não pergunte", para onde a `dominio-rico.md` agora aponta.
- A linha I tem exceção explícita para a porta de repositório por entidade, para não contradizer a `design-patterns`.
- Referências com exemplos em Python e .NET, validados pelo script:
  - `responsabilidade-unica.md`: comissão de vendas, com a regra e o layout do CSV em módulos separados;
  - `aberto-fechado.md`: lista de regras de risco; para os outros sintomas, aponta para Strategy, Decorator e Observer;
  - `substituicao-de-liskov.md`: descontos, com uma suíte de contrato que roda em todas as implementações;
  - `segregacao-de-interfaces.md`: uma porta por canal de notificação;
  - `inversao-de-dependencia.md`: o que entra pelo construtor, o que entra por parâmetro e o que o composition root cria; teste sem `patch`.

**`design-patterns`** (`SKILL.md` com 67 linhas e 26 referências)
- Organizada por sintoma: um padrão só entra com sintoma no plano ou no código, e "pode precisar no futuro" não conta. Há regras para o tech lead (campo `Padrões` do Desenho técnico), para o dev (`Decisões não previstas`) e para o reviewer (sintoma sem padrão, padrão sem sintoma).
- Tabela de sintomas de excesso (ex.: Strategy com uma estratégia só → código direto).
- Um arquivo por padrão: os 23 GoF mais Repository, Unit of Work e Specification. Cada um tem as seções Quando não usar, Forma, Python, .NET e Como testar. Os padrões de integração (outbox, consumer idempotente, retentativa) continuam nas skills de tecnologia.
- Só back-end, como a `clean-architecture`.

**`terraform`** (`SKILL.md` com 84 linhas e 6 referências)
- Regras sobre:
  - estrutura: três layouts e os arquivos de uma raiz;
  - versões: Terraform 1.11 ou mais novo, a raiz fixa a versão exata, e o lock file leva os hashes das plataformas;
  - estado e ambientes: backend S3 com lock nativo, um estado por componente e ambiente, `envs/<env>.tfvars` e `envs/<env>.backend.hcl`, `allowed_account_ids`;
  - código HCL;
  - proteção de dados (§33): `prevent_destroy` mais a proteção do próprio serviço, e destruir um recurso protegido leva dois PRs;
  - segredos: nunca no estado, com argumentos write-only e valores efêmeros;
  - refatoração: blocos `moved`, `import` e `removed`;
  - testes, plan e apply, e o que vai no Desenho técnico.
- Proibições, entre elas workspace do CLI para separar ambientes, `terraform_remote_state` entre donos diferentes e provider dentro de módulo.
- Referências:
  - `estrutura-e-ambientes.md`, `estado.md`, `modulos.md` e `testes.md`;
  - `pipeline.md`: GitHub Actions com OIDC (`fmt`, `validate`, `test`, `plan`, e `apply` do plano salvo, com aprovação em produção);
  - `entre-repositorios.md`: valores trocados por SSM, que estavam na `aws-serverless`.
- Decisões:
  - ambientes por tfvars e backend por ambiente;
  - sem tflint nem scanner de segurança por enquanto;
  - políticas IAM montadas com `jsonencode`, porque o `mock_provider` inventa o JSON do `aws_iam_policy_document` e quebrava o teste por `jsondecode` (lição que a `skill-authoring` já registrava);
  - todo `run` de teste com `command = plan`: nada é criado, e a limpeza no fim do teste não esbarra no `prevent_destroy`.

#### Skills alteradas
- `aws-infra`: agora cobre o que a AWS exige de qualquer recurso: tags, segredos, IAM (com as ações que só aceitam `*`), criptografia, rede e SQS (que veio da `aws-serverless`). Foram para a `terraform` a escolha de ferramenta, a pasta `infra/`, o plan antes do apply e os módulos. Ganhou a `references/limites.md`, com os limites de SQS e DynamoDB que estavam na `limites.md` da `aws-serverless`. Passa a ser carregada também pelo tech lead.
- `aws-serverless`: fica só com Lambda, Scheduler e Step Functions.
  - Foram para a `terraform` a estrutura do repositório, os testes de Terraform, a forma das políticas IAM e os valores entre repositórios.
  - Foram para a `aws-infra` as regras de SQS, as ações que exigem `*` e os limites de SQS e DynamoDB. A `limites.md` da `aws-serverless` ficou com Step Functions, JSONata, Lambda, Scheduler e as permissões de log.
  - A estrutura da Lambda segue o nível da `clean-architecture` (`8bef73a`).
- `code-review`: o mapa área → regra ganhou linhas para `clean-architecture`, `clean-code-solid`, `design-patterns`, `terraform`, `aws-infra` e `aws-serverless`.
- `python-backend` e `dotnet-backend`: limites do linter e seção "Estrutura (§32)" com os nomes de cada nível (`8bef73a`); referências renomeadas para a `clean-code-solid`.
- `unit-testing`: xUnit com o `Assert` do próprio xUnit, sem FluentAssertions.
- `skill-authoring`:
  - a regra 5 e o checklist exigem exemplos Python e C# validados pelo `tests/validar_exemplos.py`;
  - a `modelo.md` ganhou a seção "Exemplos validáveis (Python e C#)";
  - os exemplos de regra boa deixaram de citar o `aws_iam_policy_document`.
- `clean-architecture`: a `consumer.md` aponta SQS para a `aws-infra`.

#### Processo
- `orquestrador.md`, seção 5:
  - o tech lead carrega `clean-architecture` e `design-patterns` quando a feature tem back-end;
  - dev e reviewer carregam a `clean-code-solid` em todo repositório de aplicação, e a `clean-architecture` e a `design-patterns` só no back-end (nunca em front-end, IaC ou biblioteca).
- `orquestrador.md`, regra 8: no trabalho pequeno, a sessão principal implementa seguindo o papel `dev`, inclusive o relatório, com as skills da seção 5.3.
- `roles/techlead.md`:
  - classificação de cada repositório por papéis (API, consumer, producer, tarefa orquestrada, job...) e por nível;
  - o campo `Nível` na primeira linha do Desenho técnico (os dois itens acima são de `8bef73a`);
  - a `design-patterns` entre as skills lidas.
- `preparacao.md` e `templates/spec-input.md`: tech nova `terraform`, detectada por `*.tf` em qualquer pasta. Antes, um serviço Python com `infra/` nunca ativaria a skill.
- `skills/catalog.yaml`: entradas novas (`clean-architecture`, `clean-code-solid`, `design-patterns`, `terraform`) e gatilhos, regras e `loaded_by` revistos nas skills AWS.

#### Validador de exemplos (`tests/validar_exemplos.py`)
- Extrai os blocos Python e C# dos `.md` de uma skill e valida todos de uma vez:
  - Python: `ruff format --check`, `ruff check` com a configuração da `python-backend` e `pytest`;
  - C#: compilação com `Nullable` e `TreatWarningsAsErrors`, e testes xUnit.
- Convenção:
  - Python: bloco cuja 1ª linha é `# <arquivo>.py`;
  - C#: bloco com `[Fact]`/`[Theory]` é teste, bloco que começa com `// composition root` vira um método que recebe `services`, e bloco que começa com `// trecho` não é validado.
- Exige o Python da versão mínima da `python-backend` (3.12+). Use `--python <executável>` quando o padrão da máquina for mais antigo; `--formatar` aplica o `ruff format` aos blocos.

#### Como validar
```
python -I tests/validar_exemplos.py skills/design-patterns --python <python 3.12+ com pytest>
python -I tests/validar_exemplos.py skills/clean-code-solid --python <python 3.12+ com pytest>
```
- Resultado esperado:
  - `design-patterns`: 67 testes Python (52 arquivos) e 62 testes C#;
  - `clean-code-solid`: 25 testes Python (11 arquivos) e 23 testes C#.

  Requer ruff, pytest e o SDK do .NET.
- Teste negativo já feito: sem o piso em zero do `DescontoFixo`, a suíte de contrato de Liskov falha nas duas linguagens.
- Terraform: os 14 blocos HCL passam no `terraform fmt -check`. `validate` e `test` não foram rodados, porque baixam o provider AWS; cada referência traz o aviso "Não verificado" com o comando. O ponto mais incerto é o `override_during = plan` da `testes.md`.
- Todo `SKILL.md` alterado tem até 150 linhas, o índice de referências de cada skill bate com os arquivos, e cada regra movida aparece num lugar só.

#### Pendências conhecidas
- Verificar os exemplos da `terraform` (`init`, `validate` e `test`) e, se o time quiser, ensinar o validador a ler HCL.
- A `aws-serverless` não cobre Lambda em .NET.
- Discutidos e não implementados: um portão de simplicidade no processo (regra na constitution, critério do reviewer para abstração nova e um padrão explícito para o trabalho pequeno) e a skill de front-end.
