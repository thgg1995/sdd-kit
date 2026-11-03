---
name: aws-infra
description: Padrões de infraestrutura AWS do time (IaC, segredos, IAM, criptografia). Use em tarefas que envolvem IaC, IAM, filas, buckets, deploy ou configuração de recursos AWS.
---

# AWS e infraestrutura

## IaC (constitution §20)
- Ferramenta padrão: Terraform. <!-- TIME: ou CDK/SAM -->
- Código de infra no repositório do serviço, em `infra/`. Módulos compartilhados versionados por tag.
- Toda mudança passa por `plan` revisado antes do `apply`. Nada criado manualmente no console.
- Tags obrigatórias em todo recurso: `service`, `env`, `owner`. <!-- TIME: ajustar -->

## Segredos (constitution §21)
- Secrets Manager para credenciais com rotação; Parameter Store (SecureString) para configuração sensível.
- A aplicação lê em runtime por SDK ou injeção do runtime (ECS/Lambda). Nunca em `appsettings*.json`, `.env` versionado ou Dockerfile.
- Local: segredos fora do repositório (user-secrets no .NET, `.env` no `.gitignore` no Python).

## IAM (constitution §22)
- Uma role por serviço, com política específica por ação e ARN.
- `*` em `Action` ou `Resource` só com justificativa no `plan.md`.
- Sem chaves de acesso de longa duração em aplicações; use roles.

## Criptografia (constitution §19)
- S3, RDS, DynamoDB, SQS/SNS e MSK com criptografia em repouso (KMS) e TLS em trânsito.
- Buckets com bloqueio de acesso público habilitado.

## Rede
- Bancos e brokers em subnets privadas; acesso só pelos security groups dos serviços consumidores.
