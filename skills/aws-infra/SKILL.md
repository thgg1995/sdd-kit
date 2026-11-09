---
name: aws-infra
description: O que o time exige de todo recurso AWS — tags, segredos, IAM com menor privilégio, criptografia, rede e filas SQS. Use quando a tarefa cria ou altera recurso AWS (IAM, segredos, filas, buckets, bancos, rede).
---

# Recursos AWS

Vale para qualquer recurso AWS. Como escrever a IaC está na `terraform`; Lambda, Step Functions e agendamento, na `aws-serverless`. Em conflito, vale a constitution.

## Tags
- Todo recurso com as tags `service`, `env` e `owner`. <!-- TIME: ajustar -->

## Segredos (constitution §21)
- Secrets Manager para credenciais com rotação; Parameter Store (SecureString) para configuração sensível.
- A aplicação lê em runtime por SDK ou injeção do runtime (ECS/Lambda). Nunca em `appsettings*.json`, `.env` versionado ou Dockerfile.
- Local: segredos fora do repositório (user-secrets no .NET, `.env` no `.gitignore` no Python).

## IAM (constitution §22)
- Uma role por serviço, com política específica por ação e ARN.
- `*` em `Action` ou `Resource` só com justificativa no `plan.md`. Exceção conhecida: ações que a AWS não deixa restringir a um recurso (`cloudwatch:PutMetricData`, `logs:*LogDelivery*`, `xray:Put*`) e o sufixo `:log-stream:*` exigem `*`, com a exceção registrada no plano.
- Sem chave de acesso de longa duração em aplicação nem em pipeline: use roles (na pipeline, por OIDC).

## Criptografia (constitution §19)
- S3, RDS, DynamoDB, SQS/SNS e MSK com criptografia em repouso (KMS) e TLS em trânsito.
- Buckets com bloqueio de acesso público habilitado.

## Rede
- Bancos e brokers em subnets privadas; acesso só pelos security groups dos serviços consumidores.

## SQS (constitution §11, §25)
- Redrive (`maxReceiveCount`) é o mecanismo de tentativas; `redrive_allow_policy` na DLQ.
- Visibilidade maior que a duração máxima do processamento de uma leitura.
- Retenção: na fila standard, a expiração na DLQ conta do envio original.
- Alarme da DLQ em `ApproximateNumberOfMessagesVisible` (não `NumberOfMessagesSent`, que ignora a redrive).

## Limites (tech lead)
- Limites de SQS e DynamoDB (lote, visibilidade, retenção, tamanho de item, precisão): o tech lead confere o pior caso de cada contrato com `references/limites.md` **antes** de congelá-lo.

## Referências
- `references/limites.md` — ler quando o tech lead, na triagem ou no desenho, confere contratos ou fluxos que passam por fila SQS ou tabela DynamoDB antes de congelá-los.
