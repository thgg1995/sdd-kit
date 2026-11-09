"""Valida os exemplos de código Python e C# dos arquivos .md de uma skill do kit.

Uso (na raiz do kit; no workspace, em .agents/kit/):
    python -I tests/validar_exemplos.py <pasta> [--python <executável>] [--formatar] [--manter]

<pasta>: a skill (ex.: skills/design-patterns) ou qualquer pasta com .md (busca recursiva).

Convenção dos blocos (detalhe em skills/skill-authoring/references/modelo.md):
- ```python cuja 1a linha é `# <arquivo>.py` vira esse arquivo (nome único na pasta);
  os `test_*.py` são os testes. Sem essa 1a linha, o bloco é trecho e não é validado.
- ```csharp: cada .md vira um namespace. Bloco com [Fact]/[Theory] é teste xUnit; bloco que
  começa com `// composition root` é compilado dentro de um método que recebe
  `IServiceCollection services`; bloco que começa com `// trecho` não é validado; os demais
  são código de produção.

Validação:
- Python: ruff format --check, ruff check (configuração do bloco toml da skill python-backend)
  e pytest. O interpretador (--python; padrão: o que roda este script) precisa ser da versão
  mínima declarada na python-backend ("Python 3.12+"), e o ruff analisa para essa versão.
- C#: biblioteca com Nullable, TreatWarningsAsErrors e Microsoft.AspNetCore.App, mais um
  projeto xUnit; dotnet test.
--formatar aplica o ruff format aos blocos Python no próprio .md antes de validar.
Requer ruff e pytest; para C#, o SDK do .NET e acesso ao NuGet na primeira execução.
Sai com código 0 só se tudo o que foi encontrado passou.
"""

from __future__ import annotations

import argparse
import functools
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
BLOCO = re.compile(r"```(python|csharp)\n(.*?)```", re.DOTALL)
ARQUIVO_PY = re.compile(r"# ([\w.-]+\.py)\s*$")
USINGS_COMPOSICAO = (
    "using Microsoft.Extensions.DependencyInjection;\n"
    "using Microsoft.Extensions.Options;\n"
)
# Mensagens do dotnet em inglês: legíveis em qualquer página de código do console.
AMBIENTE = {**os.environ, "DOTNET_CLI_UI_LANGUAGE": "en-US", "DOTNET_NOLOGO": "1"}


def rodar(
    comando: list[str], pasta: Path, entrada: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        comando,
        check=False,
        cwd=pasta,
        env=AMBIENTE,
        input=entrada,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def fim(saida: str, linhas: int = 40) -> str:
    return "\n".join(saida.strip().splitlines()[-linhas:])


def nome_pascal(texto: str) -> str:
    partes = re.split(r"[^0-9A-Za-z]+", texto)
    return "".join(parte[:1].upper() + parte[1:] for parte in partes if parte)


def arquivo_py(codigo: str) -> str | None:
    m = ARQUIVO_PY.match(codigo.splitlines()[0]) if codigo.strip() else None
    return m.group(1) if m else None


def skill_python_backend() -> str:
    skill = KIT / "skills" / "python-backend" / "SKILL.md"
    return skill.read_text(encoding="utf-8") if skill.exists() else ""


def config_ruff() -> str:
    m = re.search(r"```toml\n(.*?)```", skill_python_backend(), re.DOTALL)
    return m.group(1) if m else ""


def versao_minima() -> tuple[int, int] | None:
    m = re.search(r"Python (\d+)\.(\d+)\+", skill_python_backend())
    return (int(m.group(1)), int(m.group(2))) if m else None


def versao_do_interpretador(python: str, pasta: Path) -> tuple[int, int] | None:
    r = rodar([python, "-c", "import sys; print(*sys.version_info[:2])"], pasta)
    if r.returncode != 0:
        return None
    try:
        major, minor = (int(parte) for parte in r.stdout.split())
    except ValueError:
        return None
    return major, minor


def preparar_python(pasta: Path) -> Path:
    py = pasta / "py"
    py.mkdir(parents=True, exist_ok=True)
    minima = versao_minima()
    projeto = (
        '[project]\nname = "exemplos"\nversion = "0"\n'
        f'requires-python = ">={minima[0]}.{minima[1]}"\n\n'
        if minima
        else ""
    )
    (py / "pyproject.toml").write_text(projeto + config_ruff(), encoding="utf-8")
    return py


def formatar_bloco(m: re.Match[str], md: Path, py: Path) -> str:
    nome = arquivo_py(m.group(2)) if m.group(1) == "python" else None
    if nome is None:
        return m.group(0)
    r = rodar(["ruff", "format", "--stdin-filename", nome, "-"], py, m.group(2))
    if r.returncode != 0:
        sys.exit(f"ruff format falhou em {md}: {r.stderr}")
    return f"```python\n{r.stdout}```"


def formatar(mds: list[Path], py: Path) -> None:
    for md in mds:
        texto = md.read_text(encoding="utf-8")
        novo = BLOCO.sub(functools.partial(formatar_bloco, md=md, py=py), texto)
        if novo != texto:
            md.write_text(novo, encoding="utf-8", newline="\n")
            print(f"formatado: {md}")


def validar_python(mds: list[Path], py: Path, python: str) -> bool | None:
    arquivos: dict[str, Path] = {}
    for md in mds:
        for linguagem, codigo in BLOCO.findall(md.read_text(encoding="utf-8")):
            nome = arquivo_py(codigo) if linguagem == "python" else None
            if nome is None:
                continue
            if nome in arquivos:
                print(f"Python: '{nome}' declarado em {arquivos[nome]} e em {md}")
                return False
            arquivos[nome] = md
            (py / nome).write_text(codigo, encoding="utf-8")
    if not arquivos:
        return None
    atual = versao_do_interpretador(python, py)
    if atual is None:
        print(f"Python: não validado, interpretador inválido: {python}")
        return False
    minima = versao_minima()
    if minima and atual < minima:
        print(
            f"Python: não validado; {python} é {atual[0]}.{atual[1]}, e a python-backend"
            f" pede {minima[0]}.{minima[1]}+ (indique outro com --python)"
        )
        return False
    faltando = [
        ferramenta
        for ferramenta, ok in (
            ("ruff", shutil.which("ruff")),
            (
                "pytest",
                rodar([python, "-m", "pytest", "--version"], py).returncode == 0,
            ),
        )
        if not ok
    ]
    if faltando:
        print(f"Python: não validado, faltam {', '.join(faltando)}")
        return False
    passos = [
        ("ruff format --check", ["ruff", "format", "--check", "."]),
        ("ruff check", ["ruff", "check", "."]),
        ("pytest", [python, "-m", "pytest", "-q", "-p", "no:cacheprovider"]),
    ]
    for nome, comando in passos:
        r = rodar(comando, py)
        if r.returncode != 0:
            print(f"Python: {nome} falhou\n{fim(r.stdout + r.stderr)}")
            return False
    versao = f"{atual[0]}.{atual[1]}"
    print(f"Python {versao}: OK ({len(arquivos)} arquivos; {fim(r.stdout, 1)})")
    return True


def gravar_csharp(destino: Path, cabecalho: str, namespace: str, codigo: str) -> None:
    linhas = codigo.splitlines()
    usings = [linha for linha in linhas if linha.startswith("using ")]
    resto = [linha for linha in linhas if not linha.startswith("using ")]
    topo = cabecalho + "".join(f"{u}\n" for u in usings)
    destino.write_text(
        f"{topo}\nnamespace {namespace};\n\n" + "\n".join(resto) + "\n",
        encoding="utf-8",
    )


def validar_csharp(mds: list[Path], pasta: Path) -> bool | None:
    por_md: list[tuple[str, list[str]]] = []
    usados: set[str] = set()
    for md in mds:
        blocos = [
            c
            for lang, c in BLOCO.findall(md.read_text(encoding="utf-8"))
            if lang == "csharp" and not c.startswith("// trecho")
        ]
        if not blocos:
            continue
        nome = nome_pascal(md.stem)
        if nome in usados:
            nome = nome_pascal(md.parent.name) + nome
        usados.add(nome)
        por_md.append((nome, blocos))
    if not por_md:
        return None
    if not shutil.which("dotnet"):
        print("C#: não validado, falta o SDK do .NET (dotnet)")
        return False
    net = pasta / "net"
    for comando in (
        ["dotnet", "new", "classlib", "-n", "Exemplos", "-o", "Exemplos", "--force"],
        [
            "dotnet",
            "new",
            "xunit",
            "-n",
            "Exemplos.Tests",
            "-o",
            "Exemplos.Tests",
            "--force",
        ],
    ):
        net.mkdir(parents=True, exist_ok=True)
        r = rodar(comando, net)
        if r.returncode != 0:
            print(f"C#: '{' '.join(comando)}' falhou\n{fim(r.stdout + r.stderr)}")
            return False
    for modelo in (
        net / "Exemplos" / "Class1.cs",
        net / "Exemplos.Tests" / "UnitTest1.cs",
    ):
        modelo.unlink(missing_ok=True)
    csproj = net / "Exemplos" / "Exemplos.csproj"
    csproj.write_text(
        csproj.read_text(encoding="utf-8").replace(
            "</Project>",
            '  <ItemGroup>\n    <FrameworkReference Include="Microsoft.AspNetCore.App" />\n  </ItemGroup>\n</Project>',
        ),
        encoding="utf-8",
    )
    (net / "Directory.Build.props").write_text(
        "<Project>\n  <PropertyGroup>\n    <Nullable>enable</Nullable>\n"
        "    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>\n  </PropertyGroup>\n</Project>\n",
        encoding="utf-8",
    )
    r = rodar(
        ["dotnet", "add", "Exemplos.Tests", "reference", "Exemplos/Exemplos.csproj"],
        net,
    )
    if r.returncode != 0:
        print(f"C#: referência entre projetos falhou\n{fim(r.stdout + r.stderr)}")
        return False
    for nome, blocos in por_md:
        for i, codigo in enumerate(blocos, 1):
            if "[Fact]" in codigo or "[Theory]" in codigo:
                gravar_csharp(
                    net / "Exemplos.Tests" / f"{nome}Tests{i}.cs",
                    f"using Exemplos.{nome};\n",
                    f"Exemplos.Tests.{nome}",
                    codigo,
                )
            elif codigo.startswith("// composition root"):
                corpo = "\n".join("        " + linha for linha in codigo.splitlines())
                (net / "Exemplos" / f"{nome}Composicao{i}.cs").write_text(
                    f"{USINGS_COMPOSICAO}\nnamespace Exemplos.{nome};\n\n"
                    f"public static class Composicao{i}\n{{\n"
                    "    public static void Configurar(IServiceCollection services)\n    {\n"
                    f"{corpo}\n    }}\n}}\n",
                    encoding="utf-8",
                )
            else:
                gravar_csharp(
                    net / "Exemplos" / f"{nome}{i}.cs", "", f"Exemplos.{nome}", codigo
                )
    r = rodar(["dotnet", "test", "Exemplos.Tests", "-nologo", "-v", "q"], net)
    total = re.findall(r"Total:\s*(\d+)", r.stdout)
    if r.returncode != 0:
        erros = [
            linha.strip()
            for linha in r.stdout.splitlines()
            if " error " in linha or "Failed " in linha
        ]
        print(
            "C#: dotnet test falhou\n"
            + "\n".join(sorted(set(erros))[:30] or [fim(r.stdout)])
        )
        return False
    testes = f"{total[-1]} testes aprovados" if total else "testes aprovados"
    print(f"C#: OK ({len(por_md)} arquivos; {testes})")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida exemplos Python e C# de uma skill."
    )
    parser.add_argument("pasta", type=Path)
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="interpretador dos exemplos Python (padrão: o que roda este script)",
    )
    parser.add_argument(
        "--formatar", action="store_true", help="aplica ruff format aos blocos Python"
    )
    parser.add_argument(
        "--manter", action="store_true", help="mantém a pasta temporária"
    )
    args = parser.parse_args()
    mds = sorted(args.pasta.rglob("*.md"))
    if not mds:
        print(f"nenhum .md em {args.pasta}")
        return 1
    temporaria = Path(tempfile.mkdtemp(prefix="validar_exemplos_"))
    try:
        py = preparar_python(temporaria)
        if args.formatar:
            if not shutil.which("ruff"):
                print("--formatar exige o ruff")
                return 1
            formatar(mds, py)
        resultados = [
            validar_python(mds, py, args.python),
            validar_csharp(mds, temporaria),
        ]
    finally:
        if args.manter:
            print(f"pasta mantida: {temporaria}")
        else:
            shutil.rmtree(temporaria, ignore_errors=True)
    if all(r is None for r in resultados):
        print(
            "nenhum exemplo validável encontrado (veja a convenção no início deste arquivo)"
        )
        return 1
    return 0 if all(r is not False for r in resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
