"""Criação e semeadura do banco na primeira execução.

O usuário não roda script nenhum: ao abrir o programa pela primeira vez em
qualquer computador, o banco é criado, o catálogo é semeado a partir de
:mod:`deolhonacana.dominio.catalogo` e uma conta administrativa inicial é
cadastrada. Rodar de novo não duplica nada.
"""

from __future__ import annotations

import sqlite3

from deolhonacana import config, seguranca
from deolhonacana.dados.conexao import conectar
from deolhonacana.dominio import catalogo

#: Conta criada na primeira execução. A senha precisa ser trocada no primeiro
#: login: o campo ``primeiro_acesso`` fica em 1 e a tela de login desvia para a
#: troca de senha antes de liberar o sistema.
LOGIN_INICIAL = "admin"
SENHA_INICIAL = "admin"
NOME_INICIAL = "Administrador"

#: Glebas de demonstração, para o sistema já abrir utilizável. Substituem o
#: arquivo Espelho_banco_Glebas.xlsx do projeto antigo.
GLEBAS_EXEMPLO = [
    ("001", "Fazenda Santa Rita", "Pradópolis - SP", "ADM Norte"),
    ("002", "Fazenda Boa Esperança", "Pradópolis - SP", "ADM Norte"),
    ("003", "Fazenda Córrego Fundo", "Guariba - SP", "ADM Leste"),
    ("004", "Fazenda Três Barras", "Guariba - SP", "ADM Leste"),
    ("005", "Fazenda Água Limpa", "Jaboticabal - SP", "ADM Sul"),
    ("006", "Fazenda Monte Alegre", "Jaboticabal - SP", "ADM Sul"),
]


def _criar_estrutura(conexao: sqlite3.Connection) -> None:
    """Executa o DDL. Todos os comandos usam IF NOT EXISTS."""
    ddl = config.caminho_esquema_sql().read_text(encoding="utf-8")
    conexao.executescript(ddl)


def _semear_catalogo(conexao: sqlite3.Connection) -> int:
    """Insere categorias e serviços que ainda não estejam no banco.

    Devolve quantos serviços foram inseridos nesta chamada.
    """
    inseridos = 0
    for ordem_categoria, rotulo_categoria in enumerate(catalogo.categorias()):
        codigo, nome = catalogo.separar_codigo(rotulo_categoria)
        conexao.execute(
            """
            INSERT INTO categorias (codigo, nome, rotulo, ordem)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (rotulo) DO UPDATE SET nome = excluded.nome,
                                               ordem = excluded.ordem
            """,
            (codigo, nome, rotulo_categoria, ordem_categoria),
        )
        categoria_id = conexao.execute(
            "SELECT id FROM categorias WHERE rotulo = ?", (rotulo_categoria,)
        ).fetchone()["id"]

        for ordem_servico, rotulo_servico in enumerate(
            catalogo.servicos_de(rotulo_categoria)
        ):
            codigo_servico, nome_servico = catalogo.separar_codigo(rotulo_servico)
            cursor = conexao.execute(
                """
                INSERT INTO servicos (categoria_id, codigo, nome, rotulo, ordem)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (categoria_id, codigo) DO UPDATE
                    SET nome = excluded.nome,
                        rotulo = excluded.rotulo,
                        ordem = excluded.ordem
                """,
                (
                    categoria_id,
                    codigo_servico,
                    nome_servico,
                    rotulo_servico,
                    ordem_servico,
                ),
            )
            inseridos += cursor.rowcount if cursor.rowcount > 0 else 0
    return inseridos


def _semear_glebas(conexao: sqlite3.Connection) -> None:
    """Cadastra as glebas de exemplo apenas se a tabela estiver vazia."""
    vazia = conexao.execute("SELECT COUNT(*) AS n FROM glebas").fetchone()["n"] == 0
    if vazia:
        conexao.executemany(
            """
            INSERT INTO glebas (codigo, fazenda, municipio, administrador)
            VALUES (?, ?, ?, ?)
            """,
            GLEBAS_EXEMPLO,
        )


def _semear_administrador(conexao: sqlite3.Connection) -> None:
    """Cria a conta inicial se ainda não houver nenhum usuário."""
    vazia = conexao.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()["n"] == 0
    if not vazia:
        return
    senha_hash, sal = seguranca.criar_credencial(SENHA_INICIAL)
    conexao.execute(
        """
        INSERT INTO usuarios (login, nome, senha_hash, sal, perfil, primeiro_acesso)
        VALUES (?, ?, ?, ?, 'admin', 1)
        """,
        (LOGIN_INICIAL, NOME_INICIAL, senha_hash, sal),
    )


def inicializar() -> None:
    """Garante que o banco exista, esteja atualizado e tenha o catálogo.

    Chamada em toda inicialização do aplicativo; é idempotente.
    """
    with conectar() as conexao:
        _criar_estrutura(conexao)
        _semear_catalogo(conexao)
        _semear_glebas(conexao)
        _semear_administrador(conexao)
