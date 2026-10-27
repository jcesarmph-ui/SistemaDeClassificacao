"""Imprime uma norma YAML no formato das tabelas da ABNT, para conferir com as imagens.

Uso:  python -m classificador.normas.conferir dados/normas/nbr-5915-2.yaml
"""

import sys
from decimal import Decimal

from classificador.dominio.modelos import FaixaEspessura, Limite, Norma
from classificador.dominio.propriedades import Propriedade
from classificador.normas.carregador import ErroNorma, carregar_norma

_MECANICAS = [
    Propriedade.LE,
    Propriedade.LR,
    Propriedade.AL_LO50,
    Propriedade.AL_LO80,
    Propriedade.EMBUTIMENTO,
]


def _num(valor: Decimal) -> str:
    return str(valor).replace(".", ",")


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


def _faixa(faixa: FaixaEspessura) -> str:
    partes = []
    if faixa.min is not None:
        partes.append(f"{_num(faixa.min)} {'≤' if faixa.min_inclusivo else '<'} e")
    if faixa.max is not None:
        operador = "≤" if faixa.max_inclusivo else "<"
        if partes:
            partes[0] += f" {operador} {_num(faixa.max)}"
        else:
            partes.append(f"e {operador} {_num(faixa.max)}")
    return partes[0] + " mm"


def _sinal(valor: Decimal) -> str:
    return ("+" if valor > 0 else "") + _num(valor)


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
            efeitos = []
            for prop, var in ajuste.efeito.items():
                if var.min is not None:
                    efeitos.append(f"{prop.value} mín {_sinal(var.min)}")
                if var.max is not None:
                    efeitos.append(f"{prop.value} máx {_sinal(var.max)}")
            graus = ", ".join(ajuste.graus) if ajuste.graus else "todos os graus"
            linhas.append(
                f"  [{ajuste.nota}] {_faixa(ajuste.quando)} ({graus}): {', '.join(efeitos)}"
            )
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


def main(argumentos: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # acentos corretos também no Git Bash
    argumentos = sys.argv[1:] if argumentos is None else argumentos
    if len(argumentos) != 1:
        print("Uso: python -m classificador.normas.conferir <arquivo.yaml>")
        return 2
    try:
        print(formatar_norma(carregar_norma(argumentos[0])))
    except ErroNorma as erro:
        print(f"ERRO ao carregar a norma:\n{erro}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
