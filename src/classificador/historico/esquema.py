"""Tabelas do banco `historico.db` e a forma de abrir a conexão.

O banco fica na pasta comum da rede, por isso:
- modo journal tradicional (DELETE) — **nunca WAL**, que não funciona em pasta de rede;
- `busy_timeout`: se outro computador estiver gravando, espera alguns segundos antes de desistir;
- cada gravação é uma transação curta (feita pelo repositório).

A versão do esquema fica em `PRAGMA user_version`; versões novas acrescentam tabelas/colunas sem
apagar dados.
"""

import sqlite3
from pathlib import Path

VERSAO_ESQUEMA = 1
ESPERA_BANCO_OCUPADO_MS = 5000

_TABELAS = """
-- Uma linha por classificação salva. Guarda o "retrato" do que a tela mostrou na hora: se a norma
-- for corrigida depois, o histórico continua mostrando o que foi entregue.
CREATE TABLE IF NOT EXISTS classificacao (
    id               INTEGER PRIMARY KEY,
    criado_em        TEXT NOT NULL,      -- data e hora (ISO, horário local)
    usuario          TEXT NOT NULL,      -- usuário do Windows
    computador       TEXT NOT NULL,
    versao_programa  TEXT NOT NULL,
    bobina           TEXT NOT NULL,      -- nº da bobina / lote (obrigatório)
    acabamento       TEXT NOT NULL,
    valores          TEXT NOT NULL,      -- JSON: campo da tela → texto digitado
    resultado        TEXT,               -- ex.: "ZEE G2 - Z275"
    norma            TEXT,               -- ex.: "De acordo com a norma NBR 7008-2:2021"
    correlatas       TEXT NOT NULL,      -- JSON: lista
    avisos           TEXT NOT NULL,      -- JSON: lista
    tolerancia       TEXT,               -- texto da tolerância de espessura
    tolerancia_dentro INTEGER,           -- 1 dentro, 0 fora, NULL não avaliada / sem norma
    excluido_em      TEXT,               -- preenchido = está na Lixeira (exclusão lógica)
    excluido_por     TEXT
);

-- "A classificação correta era outra": lista para revisão (melhoria contínua).
CREATE TABLE IF NOT EXISTS divergencia (
    id               INTEGER PRIMARY KEY,
    classificacao_id INTEGER NOT NULL REFERENCES classificacao(id) ON DELETE CASCADE,
    correta          TEXT NOT NULL,
    motivo           TEXT NOT NULL,
    criado_em        TEXT NOT NULL,
    usuario          TEXT NOT NULL,
    computador       TEXT NOT NULL,
    resolvida_em     TEXT,               -- preenchido = já virou correção no YAML/regra
    resolvida_por    TEXT
);
"""


def conectar(banco: Path) -> sqlite3.Connection:
    """Abre o banco do jeito certo para pasta de rede e cria as tabelas que faltarem."""
    conexao = sqlite3.connect(banco, timeout=ESPERA_BANCO_OCUPADO_MS / 1000)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA journal_mode = DELETE")
    conexao.execute(f"PRAGMA busy_timeout = {ESPERA_BANCO_OCUPADO_MS}")
    conexao.execute("PRAGMA foreign_keys = ON")
    criar_tabelas(conexao)
    return conexao


def criar_tabelas(conexao: sqlite3.Connection) -> None:
    with conexao:
        conexao.executescript(_TABELAS)
        if conexao.execute("PRAGMA user_version").fetchone()[0] < VERSAO_ESQUEMA:
            conexao.execute(f"PRAGMA user_version = {VERSAO_ESQUEMA}")
