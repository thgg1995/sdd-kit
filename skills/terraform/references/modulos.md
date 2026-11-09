# Módulos

Aplica-se ao criar, consumir ou versionar um módulo.

> Não verificado: o bloco HCL deste arquivo — `terraform init` e `terraform validate` numa raiz com ele, com acesso ao repositório do módulo.

## Quando criar
- Duas ou mais raízes usam o mesmo conjunto de recursos com a mesma regra (ex.: fila com DLQ, alarme e política). Antes disso, os recursos ficam na raiz.
- Módulo que envolve um recurso só e repassa os argumentos é proibido: use o recurso direto.

## Forma
- `modules/<nome>/` com `main.tf`, `variables.tf`, `outputs.tf` e `versions.tf` (`required_version = ">= 1.11"`; provider com `>=` na menor versão que o módulo exige).
- Sem bloco `provider` nem `backend`: quem configura é a raiz.
- Variáveis: só o que muda entre os consumidores, nas regras de variável do `SKILL.md`; o resto é decisão do módulo.
- Outputs: só o que os consumidores usam.
- Renomear recurso interno: bloco `moved` no próprio módulo, para os consumidores não destruírem e recriarem o recurso.

## Versão e consumo
- Tag semântica no repositório do módulo: quebra (variável ou output removido ou com outro tipo, recurso recriado) → major; variável opcional ou output novo → minor; correção → patch.
- A raiz consome por tag, nunca por branch:
```hcl
module "fila_pedidos" {
  source = "git::https://github.com/<org>/<repo-de-modulos>.git//modules/fila?ref=v1.2.0"

  nome            = "${local.prefixo}-pedidos"
  maximo_leituras = 5
}
```
- Módulo público do registry: versão exata (`version = "<x.y.z>"`), registrada em `Padrões` do Desenho técnico.
