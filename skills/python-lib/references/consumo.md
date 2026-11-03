# Como os consumidores dependem da lib

A forma de consumo é decisão do tech lead (registrada em `research.md` e nas notas `.agents/repos/<repo>.md`), uma vez por workspace, e vale para todos os consumidores.

## Desenvolvimento local e na feature
- O consumidor aponta para a lib **no kit**, pelo caminho relativo à pasta do consumidor: `path` da lib no `workspace.yaml` com um `../` a mais (ex.: `../../sdd-kit/python_lib`). Lib alterada na mesma feature: a branch `feature/<f>` da lib, no kit.
  - uv: `uv add --editable ../../sdd-kit/python_lib` (grava `[tool.uv.sources] <dist> = { path = "../../sdd-kit/python_lib", editable = true }` no `pyproject.toml` do consumidor).
  - pip: `pip install -e ../../sdd-kit/python_lib`, sem gravar no manifesto.
- O caminho relativo pressupõe o kit uma pasta acima do workspace (`KIT_LOCAL: ../sdd-kit`). `> Não verificado: comportamento do uv.lock do consumidor com fonte path quando a lib muda de versão — conferir com uv lock --check após alterar a lib.`
- Antes de entregar para produção, a dependência por caminho local volta para a forma publicada (abaixo): é uma tarefa da feature, não uma limpeza opcional.

## Forma publicada (CI e produção)
Escolha uma e registre:
| Forma | Exemplo no `pyproject.toml` do consumidor | Quando |
|---|---|---|
| registro de pacotes (CodeArtifact, Artifactory...) | `"<dist> >=0.3,<0.4"` | time com registro privado; melhor para várias aplicações |
| tag no Git do repositório da lib | `"<dist> @ git+ssh://git@github.com/<org>/python_lib.git@v0.3.0"` | sem registro; exige acesso ao repositório no CI |
| tag no Git do kit, se a lib for publicada dentro dele | `"<dist> @ git+ssh://git@github.com/<org>/sdd-kit.git@v0.3.0#subdirectory=python_lib"` | lib versionada junto com o kit |
- Faixa compatível com o major em uso (`>=0.3,<0.4` antes do 1.0; `>=1.2,<2` depois). Nunca a branch `main` da lib como dependência.
- Publicar a versão (tag, upload) não é tarefa de subagente: é do humano ou do pipeline da lib.

## Lambda
- A lib vai dentro do pacote da função (zip com as dependências) ou numa Lambda Layer.
  - zip: mais simples; cada função leva a versão que declarou.
  - layer: uma cópia para várias funções; a versão da layer precisa casar com a faixa declarada por cada função.
- `boto3`: o runtime Python da Lambda já traz uma versão; se a lib exigir uma faixa que o runtime não atende, o pacote da função precisa incluir o `boto3`. `> Não verificado: versão de boto3 embarcada no runtime python3.14 — conferir na documentação da AWS ("Lambda runtimes") antes de decidir.`
