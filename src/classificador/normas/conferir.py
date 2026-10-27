"""Imprime uma norma YAML no formato das tabelas da ABNT, para conferir com as imagens.

Uso:  python -m classificador.normas.conferir dados/normas/nbr-5915-2.yaml
"""

import sys
from pathlib import Path

from classificador.dominio.formatacao import descrever_ajuste, descrever_faixa
from classificador.dominio.formatacao import num as _num
from classificador.dominio.modelos import Limite, Norma, NormaTolerancia
from classificador.dominio.propriedades import Propriedade
from classificador.normas.carregador import ErroNorma, carregar_norma, carregar_tolerancia

_MECANICAS = [
    Propriedade.LE,
    Propriedade.LR,
    Propriedade.AL_LO50,
    Propriedade.AL_LO80,
    Propriedade.EMBUTIMENTO,
]


def _celula(limite: Limite | None, tipo_coluna: str) -> str:
    """Texto de uma célula. Se a coluna inteira é só 'máx' ou só 'mín', mostra só o número."""
    if limite is None:
        return "–"
    if limite.min is not None and limite.max is not None:
        return f"{_num(limite.min)} – {_num(limite.max)}"
    if limite.max is not None:
        return _num(limite.max) if tipo_coluna == "máx" else f"{_num(limite.max)} máx"
    return _num(limite.min) if tipo_coluna == "mín" else f"{_num(limite.min)} mín"


def _tipo_coluna(limites: list[Limite]) -> str:
    """'máx' se todos os limites da coluna só têm máximo, 'mín' se só mínimo, senão ''."""
    if all(lim.min is None for lim in limites):
        return "máx"
    if all(lim.max is None for lim in limites):
        return "mín"
    return ""


def _desenhar(cabecalho: list[str], linhas: list[list[str]]) -> str:
    larguras = [max(len(c) for c in coluna) for coluna in zip(cabecalho, *linhas, strict=True)]

    def linha(celulas: list[str]) -> str:
        return "| " + " | ".join(c.center(w) for c, w in zip(celulas, larguras, strict=True)) + " |"

    separador = "+" + "+".join("-" * (w + 2) for w in larguras) + "+"
    return "\n".join([separador, linha(cabecalho), separador, *map(linha, linhas), separador])


def _tabela_propriedades(norma: Norma, titulo: str, propriedades: list[Propriedade]) -> str:
    usadas = [p for p in propriedades if any(p in g.limites for g in norma.graus)]
    if not usadas:
        return ""
    cabecalho = ["Grau"]
    tipos = {}
    for p in usadas:
        tipos[p] = _tipo_coluna([g.limites[p] for g in norma.graus if p in g.limites])
        cabecalho.append(f"{p.value} {tipos[p]} ({p.unidade})".replace("  ", " "))
    linhas = [
        [g.nome_na_norma] + [_celula(g.limites.get(p), tipos[p]) for p in usadas]
        for g in norma.graus
    ]
    return f"{titulo}\n{_desenhar(cabecalho, linhas)}"


def formatar_norma(norma: Norma) -> str:
    blocos = [
        f"{norma.codigo} — {norma.titulo}",
        "Graus do menos para o mais nobre (ordem da tabela).",
    ]

    quimicas = _tabela_propriedades(norma, "COMPOSIÇÃO QUÍMICA", Propriedade.quimicas())
    mecanicas = _tabela_propriedades(norma, "PROPRIEDADES MECÂNICAS", _MECANICAS)
    blocos += [b for b in (quimicas, mecanicas) if b]

    somas = [
        f"  {g.nome_na_norma}: {' + '.join(e.value for e in s.elementos)} ≤ {_num(s.max)} %"
        for g in norma.graus
        for s in g.somas
    ]
    if somas:
        blocos.append("SOMAS\n" + "\n".join(somas))

    if norma.ajustes:
        linhas = []
        for ajuste in norma.ajustes:
            graus = ", ".join(ajuste.graus) if ajuste.graus else "todos os graus"
            linhas.append(f"  [{ajuste.nota}] ({graus}) {descrever_ajuste(ajuste)}")
        blocos.append("NOTAS DE RODAPÉ (AJUSTES)\n" + "\n".join(linhas))

    avisos = [f"  {g.nome_na_norma}: {aviso}" for g in norma.graus for aviso in g.avisos]
    if avisos:
        blocos.append("AVISOS\n" + "\n".join(avisos))

    if norma.tabela_embutimento is not None:
        linhas_tab = norma.tabela_embutimento.linhas
        siglas = [g.sigla for g in norma.graus if any(g.sigla in ln.minimos for ln in linhas_tab)]
        nomes = [norma.grau(s).nome_na_norma for s in siglas]
        linhas = [
            [_num(ln.espessura)]
            + [_num(ln.minimos[s]) if s in ln.minimos else "–" for s in siglas]
            for ln in linhas_tab
        ]
        blocos.append(
            "EMBUTIMENTO — mínimos (mm)\n" + _desenhar(["Espessura (mm)", *nomes], linhas)
        )

    return "\n\n".join(blocos)


def formatar_tolerancia(norma: NormaTolerancia) -> str:
    larguras = [_num(x) for x in norma.larguras]
    colunas = [f"L ≤ {larguras[0]}"]
    colunas += [f"{a} < L ≤ {b}" for a, b in zip(larguras, larguras[1:], strict=False)]
    colunas.append(f"L > {larguras[-1]}")

    blocos = [f"{norma.codigo} — {norma.titulo}", "Tolerâncias normais (± mm)."]
    for tabela in norma.tabelas:
        faixa_le = (
            f" — LE mínimo do grau: {descrever_faixa(tabela.le_min, 'LE', 'MPa')}"
            if tabela.le_min
            else ""
        )
        linhas = [
            [descrever_faixa(ln.espessura)]
            + [f"± {_num(t)}" if t is not None else "–" for t in ln.tolerancias]
            for ln in tabela.linhas
        ]
        grade = _desenhar(["Espessura", *colunas], linhas)
        blocos.append(f"{tabela.nome.upper()}{faixa_le}\n{grade}")
    for acrescimo in norma.acrescimos:
        blocos.append(
            f"ACRÉSCIMO: +{_num(acrescimo.valor)} mm para {', '.join(acrescimo.acabamentos)} "
            f"com camada ≥ {_num(acrescimo.camada_min)} g/m²"
        )
    return "\n\n".join(blocos)


def _e_tolerancia(caminho: Path) -> bool:
    """Arquivo de norma de tolerância (tem o campo `larguras:` no topo)?"""
    if not caminho.is_file():
        return False
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    return any(ln.startswith("larguras:") for ln in linhas)


def main(argumentos: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # acentos corretos também no Git Bash
    argumentos = sys.argv[1:] if argumentos is None else argumentos
    if len(argumentos) != 1:
        print("Uso: python -m classificador.normas.conferir <arquivo.yaml>")
        return 2
    caminho = Path(argumentos[0])
    try:
        if _e_tolerancia(caminho):
            print(formatar_tolerancia(carregar_tolerancia(caminho)))
        else:
            print(formatar_norma(carregar_norma(caminho)))
    except ErroNorma as erro:
        print(f"ERRO ao carregar a norma:\n{erro}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
