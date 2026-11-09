# Regras boas e ruins

## Lado a lado
| Ruim | Bom | Por quê |
|---|---|---|
| "Siga boas práticas de segurança." | "Políticas IAM com ações e recursos específicos; `*` só nas ações que a AWS não permite restringir, com exceção registrada no plano (§22)." | o reviewer consegue conferir no diff |
| "Use uma arquitetura limpa." | "`handler.py` só converte o evento e chama `service.run_cycle`; regras em `service.py`, sem boto3; boto3 só em `aws.py`." | diz onde cada coisa fica |
| "Teste bem o código." | "Cada FR tem um teste `test_FR<nnn>_<caso>`; boto3 com `botocore.stub.Stubber`, sem rede." | nome e ferramenta verificáveis |
| "Use a versão mais recente do Python." | (nada: versão é da stack declarada, não da skill) | skill não escolhe stack |
| "Crie a fila `sqs-batch-process`." | (nada: nome de recurso é da feature, não da skill) | skill vale para qualquer feature |
| "Prefira X; às vezes Y." | "Use X. Use Y só quando <condição verificável>." | sem ambiguidade para quem segue à risca |

## Erros já vistos em propostas
- **Exemplo inválido**: referência de Step Functions com `Catch` num estado `Pass` — a ASL não permite `Catch` em `Pass`. O dev teve de trocar por `Parallel`. Verifique cada exemplo com o comando de validação da ferramenta ou contra a documentação oficial.
- **Regra que não funciona na prática**: "testes Terraform sempre com `mock_provider`" — o mock simula também o JSON do `aws_iam_policy_document`, e o teste por `jsondecode` que a própria skill exigia deixou de funcionar. Os dois devs desviaram. Quando duas regras da skill dependem uma da outra, confira que funcionam juntas. (A `terraform` resolveu montando as políticas com `jsonencode`: `references/testes.md`.)
- **Regra que só vale para a feature**: limites, nomes e números da spec copiados para a skill. Vão para o `Desenho técnico`.
- **Sobreposição**: skill nova repetindo regras de IAM que já estão em `aws-infra`. Aponte para a skill vizinha em vez de copiar.

## Atualizar a partir das lições da feature
Desvio aceito pelo reviewer, falha do QA por padrão errado ou bloqueio do dev por regra inviável são evidências para atualizar a skill:
1. Corrija a regra no arquivo onde ela vive (`SKILL.md` ou `references/`).
2. Registre em `Decisões` do relatório: regra antes → depois e o relatório que comprova.
3. Mantenha o resto da skill igual: a atualização não é ocasião para reescrevê-la.
