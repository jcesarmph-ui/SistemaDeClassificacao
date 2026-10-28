"""Teste de fumaça: confirma que o pacote está instalado e pode ser importado."""

import re
from importlib.metadata import version

import classificador


def test_pacote_importa_e_tem_versao_semantica():
    assert re.fullmatch(r"\d+\.\d+\.\d+", classificador.__version__)  # MAIOR.MENOR.CORREÇÃO
    assert version("classificador") == classificador.__version__  # um lugar só
