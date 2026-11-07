# Constitution

Princípios inegociáveis de todos os projetos. Valem para o plan, o analyze e o review.
Aqui ficam **somente regras**. O "como" fica nas skills, que referenciam cada regra pelo número (ex.: `constitution §10`).
**DEVE** / **NUNCA** = obrigatório. **DEVERIA** = padrão; desvio precisa de justificativa no `plan.md`.

## I. Arquitetura e contratos
1. Cada entidade tem um único serviço dono; só o dono escreve nela.
2. Um serviço NUNCA acessa o banco de outro; integração só por API ou evento definidos em `contracts/`.
3. Contratos DEVEM ser definidos e versionados antes do código.
4. Mudança de contrato DEVE ser retrocompatível; quebra exige nova versão convivendo com a anterior.

## II. APIs
5. A implementação NUNCA diverge do contrato publicado.
6. Erros DEVEM seguir um formato único e NUNCA expor detalhes internos.
7. Operações com efeito colateral sujeitas a retentativa DEVEM ser idempotentes.
8. Listagens DEVEM ser paginadas e limitadas.
9. Toda chamada externa DEVE ter timeout; retentativa só para falhas transitórias.

## III. Mensageria
10. Todo consumer DEVE ser idempotente.
11. Mensagem que falha NUNCA é descartada em silêncio.
12. Eventos DEVEM ter schema versionado, validado por produtor e consumidor.
13. A ordenação exigida pelo domínio DEVE ser garantida.
14. Evento ligado a uma escrita no banco DEVE ser publicado com garantia (sem perda nem evento sem escrita).

## IV. Dados
15. Mudança de schema DEVE ser versionada no repositório e compatível com a versão em execução.
16. Entrada externa NUNCA é concatenada em consultas.
17. Consultas em caminhos críticos DEVEM ser suportadas por índice ou chave.
18. Modelos não relacionais DEVEM partir dos padrões de acesso; leitura sem chave em produção é proibida.
19. Dados pessoais e sensíveis DEVEM ser identificados no plano, protegidos em repouso e em trânsito, e NUNCA registrados em log.

## V. Infraestrutura e segurança
20. Infraestrutura DEVE ser código versionado.
21. Segredos NUNCA ficam em código, configuração versionada ou imagem.
22. Permissões DEVEM seguir o menor privilégio.
23. Toda entrada externa DEVE ser validada na borda.

## VI. Observabilidade
24. Logs DEVEM ser estruturados e carregar um id de correlação propagado entre serviços.
25. Todo serviço DEVE expor saúde e métricas de erro e latência; consumers, também atraso e falhas.

## VII. Testes
26. Nenhuma tarefa está concluída sem teste automatizado do comportamento e dos erros previstos.
27. Todo contrato DEVE ser testado dos dois lados (produtor e consumidor).
28. Integração com infraestrutura DEVERIA ser testada contra dependências reais.
29. O build NUNCA introduz novos warnings.

## VIII. Código
30. Código NUNCA bloqueia em operações assíncronas.
31. Código novo DEVE ser tipado de forma verificável por compilador ou type checker.
32. No back-end, regra de negócio NUNCA depende de framework, SDK, driver ou formato de transporte; entrada e saída ficam em adaptadores.

## Governança
- Esta constitution prevalece sobre skills, convenções de repositório e preferências pontuais.
- Alterações exigem aprovação do humano e incremento de versão (MAJOR: regra removida/redefinida; MINOR: regra nova; PATCH: redação). Ao alterar uma regra, revise as skills que a referenciam.
- Exceções são registradas no `plan.md` da feature, com motivo e alternativa descartada, e não valem para outras features.

**Versão**: 2.1.0 | **Ratificada em**: <data> | **Última alteração**: <data>
