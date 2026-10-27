"""Testes do formato das normas de tolerância de espessura."""

from decimal import Decimal
from pathlib import Path

import pytest

from classificador.normas.carregador import ErroNorma, carregar_tolerancias

DADOS = Path(__file__).parent / "dados"
D = Decimal


@pytest.fixture(scope="module")
def norma(tmp_path_factory):
    pasta = tmp_path_factory.mktemp("tol")
    texto = (DADOS / "tolerancia-ficticia.yaml").read_text(encoding="utf-8")
    (pasta / "t.yaml").write_text(texto, encoding="utf-8")
    return carregar_tolerancias(pasta)["NBR 0000-T"]


def test_carrega_tabelas_e_acrescimo(norma):
    assert [t.nome for t in norma.tabelas] == ["Tabela 1", "Tabela 2"]
    assert norma.tabelas[0].linhas[0].tolerancias == [D("0.04"), D("0.05"), None]
    assert norma.acrescimos[0].valor == D("0.01")


@pytest.mark.parametrize(
    ("largura", "coluna"),
    [("1000", 0), ("1200", 0), ("1200.1", 1), ("1500", 1), ("1501", 2)],
)
def test_coluna_pela_largura(norma, largura, coluna):
    assert norma.coluna(D(largura)) == coluna


def test_linha_com_numero_errado_de_colunas(tmp_path):
    (tmp_path / "t.yaml").write_text(
        "codigo: X\ntitulo: X\nlarguras: [1200, 1500]\n"
        "tabelas:\n  - nome: Tabela 9\n    linhas:\n"
        "      - {espessura: {max: 1}, tolerancias: [0.1, 0.2]}\n",
        encoding="utf-8",
    )
    with pytest.raises(ErroNorma, match="Tabela 9.*esperadas 3"):
        carregar_tolerancias(tmp_path)
