"""Teste de fumaça: confirma que o pacote está instalado e pode ser importado."""

import classificador


def test_pacote_importa_e_tem_versao():
    assert classificador.__version__ == "0.1.0"
