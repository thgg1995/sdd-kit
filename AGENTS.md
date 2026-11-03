# AGENTS.md — workspace Spec-Driven (SDD)

Este arquivo configura o workspace e diz o que cada agente lê. O roteiro do processo vem do kit (`orquestrador.md`); os papéis ficam em `.agents/roles/`.

## Configuração
```
KIT_LOCAL: ../sdd-kit                              # 1ª opção: pasta do kit uma acima do workspace (caminho relativo à raiz do workspace)
KIT_SOURCE: git@github.com:minha-org/sdd-kit.git   # 2ª opção: repositório remoto, usado só se KIT_LOCAL não for válido
KIT_REF: main                                      # branch/tag do KIT_SOURCE (não se aplica ao KIT_LOCAL)
IDIOMA: pt-BR                                      # idioma de todo texto ao humano e de todos os artefatos
```
Escreva todo texto ao humano e todo artefato (specs, planos, relatórios, commits, READMEs) em `IDIOMA`; identificadores técnicos ficam como estão.

## Subagente
Se o seu prompt começa com `Papel:`, ignore o restante deste arquivo e siga `.agents/roles/<papel>.md`.

## Sessão principal (orquestrador)

### Sessão limpa (primeiro passo de uma feature nova)
Ao receber uma spec ou um pedido de feature nova, antes de qualquer outra coisa (inclusive de obter o kit e da preparação), confira se esta sessão já tem conversa de outro assunto (discussão do kit, outra feature, análise). Se tiver, responda só isto e PARE:
"Esta sessão já tem histórico, e cada passo do fluxo o relê. Abra uma sessão nova (ex.: `/clear`) e reenvie a spec. Para seguir assim mesmo, responda 'seguir'."
Não se aplica ao "continue" (retomada, seção 4.1 do roteiro) nem às respostas do humano durante o fluxo.

### Kit e roteiro
1. **Kit**: se `.agents/orquestrador.md` não existir, obtenha o kit em `.agents/kit/`: cópia do `KIT_LOCAL` sem `.git` e sem as bibliotecas compartilhadas (pastas de primeiro nível com `.git` próprio); se `KIT_LOCAL` não for válido, clone raso de `KIT_SOURCE` em `KIT_REF`.
2. **Roteiro**: leia inteiro o `.agents/orquestrador.md` (na primeira vez, o `.agents/kit/orquestrador.md`) e siga-o; a preparação descrita nele instala o resto. Releia-o sempre que ele não estiver no seu contexto (sessão nova, contexto resumido ou compactado). Se a ferramenta cortar a saída, leia o restante por intervalo de linhas, até o fim.
