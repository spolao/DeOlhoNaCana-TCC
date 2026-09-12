"""Consultas e gravações da tabela ``usuarios``."""

from __future__ import annotations

import sqlite3

from deolhonacana import seguranca
from deolhonacana.dados.conexao import conectar
from deolhonacana.dominio.modelos import Usuario


def _para_usuario(linha: sqlite3.Row) -> Usuario:
    return Usuario(
        id=linha["id"],
        login=linha["login"],
        nome=linha["nome"],
        perfil=linha["perfil"],
        primeiro_acesso=bool(linha["primeiro_acesso"]),
        ativo=bool(linha["ativo"]),
    )


def buscar_por_login(login: str) -> Usuario | None:
    """Usuário com este login, ou ``None``. A comparação ignora maiúsculas."""
    with conectar() as conexao:
        linha = conexao.execute(
            "SELECT * FROM usuarios WHERE login = ?", (login.strip(),)
        ).fetchone()
    return _para_usuario(linha) if linha else None


def obter_credencial(login: str) -> tuple[str, str] | None:
    """Par ``(hash, sal)`` do usuário, ou ``None`` se ele não existir."""
    with conectar() as conexao:
        linha = conexao.execute(
            "SELECT senha_hash, sal FROM usuarios WHERE login = ?", (login.strip(),)
        ).fetchone()
    return (linha["senha_hash"], linha["sal"]) if linha else None


def listar(incluir_inativos: bool = False) -> list[Usuario]:
    """Todos os usuários, em ordem alfabética de nome."""
    sql = "SELECT * FROM usuarios"
    if not incluir_inativos:
        sql += " WHERE ativo = 1"
    sql += " ORDER BY nome COLLATE NOCASE"
    with conectar() as conexao:
        linhas = conexao.execute(sql).fetchall()
    return [_para_usuario(linha) for linha in linhas]


def criar(login: str, nome: str, senha: str, perfil: str = "operador") -> Usuario:
    """Cadastra um usuário novo, que precisará trocar a senha no primeiro login.

    Levanta :class:`ValueError` se o login já existir.
    """
    login = login.strip()
    senha_hash, sal = seguranca.criar_credencial(senha)
    try:
        with conectar() as conexao:
            cursor = conexao.execute(
                """
                INSERT INTO usuarios (login, nome, senha_hash, sal, perfil,
                                      primeiro_acesso)
                VALUES (?, ?, ?, ?, ?, 1)
                """,
                (login, nome.strip(), senha_hash, sal, perfil),
            )
            novo_id = cursor.lastrowid
    except sqlite3.IntegrityError as erro:
        raise ValueError(f"Já existe um usuário com o login '{login}'.") from erro
    return Usuario(
        id=novo_id, login=login, nome=nome.strip(), perfil=perfil, primeiro_acesso=True
    )


def alterar_senha(login: str, nova_senha: str) -> bool:
    """Grava a nova senha e encerra a condição de primeiro acesso."""
    senha_hash, sal = seguranca.criar_credencial(nova_senha)
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            UPDATE usuarios
               SET senha_hash = ?, sal = ?, primeiro_acesso = 0
             WHERE login = ?
            """,
            (senha_hash, sal, login.strip()),
        )
    return cursor.rowcount > 0


def definir_ativo(login: str, ativo: bool) -> bool:
    """Ativa ou desativa o acesso de um usuário, sem apagar o histórico dele."""
    with conectar() as conexao:
        cursor = conexao.execute(
            "UPDATE usuarios SET ativo = ? WHERE login = ?",
            (1 if ativo else 0, login.strip()),
        )
    return cursor.rowcount > 0
