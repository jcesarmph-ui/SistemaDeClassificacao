"""Histórico: salvar, pesquisar, lixeira, divergências, backup e banco ocupado (dados fictícios)."""

import datetime
import sqlite3

import pytest

from classificador.historico.backup import fazer_backup_diario
from classificador.historico.esquema import conectar
from classificador.historico.repositorio import (
    MENSAGEM_CONSULTA,
    MENSAGEM_OCUPADO,
    ErroDeValidacao,
    NovaClassificacao,
    RepositorioHistorico,
)


class Relogio:
    """Hora controlada pelo teste: cada leitura anda 1 minuto."""

    def __init__(self):
        self.hora = datetime.datetime(2026, 11, 3, 8, 0)

    def __call__(self):
        self.hora += datetime.timedelta(minutes=1)
        return self.hora


@pytest.fixture
def repo(tmp_path):
    r = RepositorioHistorico.abrir(tmp_path, agora=Relogio(), quem=("ana", "PC-01"))
    yield r
    r.fechar()


def nova(volume="V-001", resultado="GRAU X - Z100", **outros):
    return NovaClassificacao(
        volume=volume,
        acabamento=outros.pop("acabamento", "GI ZN"),
        valores=outros.pop("valores", {"LE": "200", "Mn": "0,15"}),
        resultado=resultado,
        norma="De acordo com a norma NBR 0000",
        correlatas=["EN 0000 DX0"],
        avisos=outros.pop("avisos", ["Seria GRAU Y, mas o LE rebaixou"]),
        tolerancia="Dentro da tolerância: 0,73 a 0,87 mm",
        tolerancia_dentro=True,
    )


def test_salva_e_le_o_retrato_completo(repo):
    id_ = repo.salvar(nova(volume="  V-001  "))
    r = repo.obter(id_)
    assert r.volume == "V-001"  # espaços das pontas tirados
    assert r.resultado == "GRAU X - Z100"
    assert r.valores == {"LE": "200", "Mn": "0,15"}
    assert r.avisos == ["Seria GRAU Y, mas o LE rebaixou"]
    assert r.tolerancia_dentro is True
    assert (r.usuario, r.computador) == ("ana", "PC-01")
    assert r.criado_em.date() == datetime.date(2026, 11, 3)
    assert r.versao_programa and r.excluido_em is None


def test_volume_obrigatoria_e_precisa_de_resultado(repo):
    with pytest.raises(ErroDeValidacao) as erro:
        repo.salvar(nova(volume="  ", resultado=None))
    assert len(erro.value.mensagens) == 2
    assert repo.listar() == []


def test_lista_mais_recente_primeiro(repo):
    primeiro = repo.salvar(nova(volume="V-1"))
    segundo = repo.salvar(nova(volume="V-2"))
    assert [r.id for r in repo.listar()] == [segundo, primeiro]


def test_pesquisa_texto_livre_sem_maiusculas_nem_acentos(repo):
    repo.salvar(nova(volume="V-777", acabamento="FF", resultado="EEP G2"))
    repo.salvar(nova(volume="V-888", avisos=["Valores não informados: Lo80"]))
    assert [r.volume for r in repo.listar("v-777")] == ["V-777"]
    assert [r.volume for r in repo.listar("eep g2")] == ["V-777"]  # palavras em qualquer ordem
    assert [r.volume for r in repo.listar("NAO informados")] == ["V-888"]  # sem acento
    assert [r.volume for r in repo.listar("ana 03/11/2026 V-888")] == ["V-888"]
    assert repo.listar("inexistente") == []


def test_lixeira_excluir_restaurar_e_excluir_de_vez(repo):
    id_ = repo.salvar(nova())
    repo.excluir(id_)
    assert repo.listar() == []
    na_lixeira = repo.listar(lixeira=True)
    assert [r.id for r in na_lixeira] == [id_] and na_lixeira[0].excluido_por == "ana"

    repo.restaurar(id_)
    assert [r.id for r in repo.listar()] == [id_] and repo.listar(lixeira=True) == []

    with pytest.raises(ErroDeValidacao):  # fora da Lixeira não apaga de vez
        repo.excluir_permanentemente(id_)
    repo.excluir(id_)
    repo.excluir_permanentemente(id_)
    assert repo.obter(id_) is None


def test_divergencia_exige_correta_e_motivo(repo):
    id_ = repo.salvar(nova())
    with pytest.raises(ErroDeValidacao) as erro:
        repo.registrar_divergencia(id_, " ", "")
    assert len(erro.value.mensagens) == 2


def test_divergencias_pendentes_resolvidas_e_lixeira(repo):
    id_ = repo.salvar(nova())
    d = repo.registrar_divergencia(id_, "GRAU Y - Z100", "Certificado lido errado")
    [pendente] = repo.listar_divergencias()
    assert (pendente.id, pendente.correta, pendente.classificacao.id) == (d, "GRAU Y - Z100", id_)

    repo.excluir(id_)  # classificação na Lixeira → divergência some da lista
    assert repo.listar_divergencias() == []
    with pytest.raises(ErroDeValidacao):  # e não aceita divergência nova
        repo.registrar_divergencia(id_, "GRAU Y", "motivo")
    repo.restaurar(id_)

    repo.resolver_divergencia(d)
    assert repo.listar_divergencias() == []
    [resolvida] = repo.listar_divergencias(resolvidas=True)
    assert resolvida.resolvida_por == "ana"

    repo.excluir(id_)
    repo.excluir_permanentemente(id_)  # apaga junto as divergências
    assert repo._conexao.execute("SELECT COUNT(*) FROM divergencia").fetchone()[0] == 0


def test_modo_consulta_recusa_toda_gravacao(repo):
    id_ = repo.salvar(nova())
    repo.modo_consulta = True
    for gravar in (
        lambda: repo.salvar(nova()),
        lambda: repo.excluir(id_),
        lambda: repo.restaurar(id_),
        lambda: repo.registrar_divergencia(id_, "X", "Y"),
    ):
        with pytest.raises(ErroDeValidacao) as erro:
            gravar()
        assert erro.value.mensagens == [MENSAGEM_CONSULTA]
    assert len(repo.listar()) == 1  # consultar continua valendo


def test_banco_ocupado_vira_aviso(tmp_path):
    banco = tmp_path / "historico.db"
    outro_pc = sqlite3.connect(banco)
    conexao = conectar(banco)
    conexao.execute("PRAGMA busy_timeout = 50")  # não esperar 5 s no teste
    repo = RepositorioHistorico(conexao, quem=("ana", "PC-01"))
    outro_pc.execute("BEGIN EXCLUSIVE")  # outro computador gravando
    try:
        with pytest.raises(ErroDeValidacao) as erro:
            repo.salvar(nova())
        assert erro.value.mensagens == [MENSAGEM_OCUPADO]
    finally:
        outro_pc.rollback()
        outro_pc.close()
        repo.fechar()


def test_banco_em_modo_journal_tradicional_nunca_wal(repo):
    assert repo._conexao.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    assert repo._conexao.execute("PRAGMA user_version").fetchone()[0] >= 1


def test_backup_diario_uma_copia_por_dia_e_guarda_as_ultimas(tmp_path):
    banco = tmp_path / "historico.db"
    conectar(banco).close()
    dia = datetime.date(2026, 11, 1)
    assert fazer_backup_diario(banco, dia, manter=2) is not None
    assert fazer_backup_diario(banco, dia, manter=2) is None  # mesmo dia: não repete
    for n in (1, 2):
        fazer_backup_diario(banco, dia + datetime.timedelta(days=n), manter=2)
    copias = sorted(p.name for p in (tmp_path / "backup").iterdir())
    assert copias == ["historico_2026-11-02.db", "historico_2026-11-03.db"]


def test_abrir_faz_o_backup_do_dia(tmp_path):
    RepositorioHistorico.abrir(tmp_path, agora=Relogio(), quem=("a", "b")).fechar()
    assert (tmp_path / "backup" / "historico_2026-11-03.db").is_file()
