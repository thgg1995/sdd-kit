# Estado

Aplica-se ao configurar o backend, migrar o estado, adotar recurso que já existe, ou renomear, mover ou esquecer um recurso.

> Não verificado: os blocos HCL deste arquivo — `terraform validate` numa raiz com eles; o `import` e o `removed`, com `terraform plan` numa conta de teste.

## Backend
- Um bucket de estado por conta, com versionamento, criptografia, bloqueio de acesso público e `prevent_destroy` (§33). Ele é criado fora das raízes que o usam: por uma raiz de bootstrap da conta, com estado próprio, ou pelo time de plataforma.
- Chave por componente: `<componente>/terraform.tfstate`. Um estado por componente e ambiente limita o alcance de um erro e o tempo do plan.
- Lock nativo do S3 (`use_lockfile = true`), sem tabela DynamoDB.
- Migrar do lock por DynamoDB: um ciclo com `use_lockfile = true` e `dynamodb_table` juntos, aplicado em todos os ambientes; depois, remova o `dynamodb_table`.
- Mudar bucket ou chave: `terraform init -migrate-state -backend-config=envs/<env>.backend.hcl`, um ambiente por vez; o plan seguinte não pode ter mudança.
- Estado perdido ou corrompido: volte a versão anterior do objeto no bucket (versionamento).

## Adotar recurso existente
```hcl
import {
  to = aws_sqs_queue.pedidos
  id = "https://sqs.<regiao>.amazonaws.com/000000000000/<nome-da-fila>"
}
```
- `terraform plan -generate-config-out=gerado.tf` escreve a configuração inicial: leve-a para o `.tf` do grupo, ajuste às regras da skill e apague o `gerado.tf`.
- O plan do PR de adoção mostra só o import, sem mudança no recurso; mudança desejada vem em outro PR.

## Renomear, mover, esquecer
```hcl
# Renomeado no código: o recurso não é destruído nem recriado.
moved {
  from = aws_sqs_queue.fila
  to   = aws_sqs_queue.pedidos
}

# Sai do estado e continua na AWS (ex.: passou a ser de outro repositório).
removed {
  from = aws_s3_bucket.legado

  lifecycle {
    destroy = false
  }
}
```
- Os blocos ficam no código até todos os ambientes aplicarem.
- `terraform state mv`, `terraform state rm` e `terraform import` pela linha de comando não passam por revisão: proibidos em conta AWS.
