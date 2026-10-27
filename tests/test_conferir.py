"""Testes do comando de conferência (imprime a norma no formato das tabelas da ABNT)."""

from pathlib import Path

from classificador.normas.carregador import carregar_norma
from classificador.normas.conferir import formatar_norma, main

NORMA_FICTICIA = Path(__file__).parent / "dados" / "norma-ficticia.yaml"


def test_tabelas_no_formato_da_norma():
    texto = formatar_norma(carregar_norma(NORMA_FICTICIA))
    # vírgula decimal, como nas imagens das normas
    assert "0,007" in texto
    assert "0,12" in texto
    # nome do grau como está na norma, e faixa de LE
    assert "BBB grau 1" in texto
    assert "120 – 160" in texto
    # coluna sem exigência para o grau mostra traço
    assert "–" in texto
    # somas, notas e avisos
    assert "Ti + Nb ≤ 0,20" in texto
    assert "(todos os graus) e < 0,50 mm" in texto
    assert "LE máx +40" in texto
    assert "alongamento Lo50 mín -4" in texto
    assert "não substitui AAA" in texto
    # embutimento
    assert "9,5" in texto


def test_main_imprime_e_retorna_zero(capsys):
    assert main([str(NORMA_FICTICIA)]) == 0
    assert "NBR 0000-1:2026" in capsys.readouterr().out


def test_main_com_arquivo_invalido_retorna_um(tmp_path, capsys):
    assert main([str(tmp_path / "nao-existe.yaml")]) == 1
    assert "não encontrado" in capsys.readouterr().out
