"""Armazenamento seguro de senhas.

Substitui o esquema anterior, em que a senha do usuário era gravada em texto
puro na coluna ``Usuarios.Senha``. Aqui a senha nunca é persistida: guarda-se
apenas o resultado de PBKDF2-HMAC-SHA256 sobre a senha mais um sal aleatório
por usuário. Usa somente a biblioteca padrão, sem dependência externa.
"""

from __future__ import annotations

import hashlib
import hmac
import os

#: Iterações do PBKDF2. Valor alto o bastante para encarecer ataque de força
#: bruta e baixo o bastante para o login continuar instantâneo no desktop.
ITERACOES = 240_000

TAMANHO_SAL = 16
ALGORITMO = "sha256"

#: Regras mínimas exigidas na troca de senha.
TAMANHO_MINIMO_SENHA = 6


def gerar_sal() -> str:
    """Sal aleatório novo, em hexadecimal."""
    return os.urandom(TAMANHO_SAL).hex()


def calcular_hash(senha: str, sal: str) -> str:
    """Deriva o hash da senha com o sal informado."""
    derivado = hashlib.pbkdf2_hmac(
        ALGORITMO,
        senha.encode("utf-8"),
        bytes.fromhex(sal),
        ITERACOES,
    )
    return derivado.hex()


def criar_credencial(senha: str) -> tuple[str, str]:
    """Devolve ``(hash, sal)`` para uma senha nova."""
    sal = gerar_sal()
    return calcular_hash(senha, sal), sal


def verificar_senha(senha: str, hash_esperado: str, sal: str) -> bool:
    """Confere a senha em tempo constante, tolerando registro corrompido."""
    try:
        calculado = calcular_hash(senha, sal)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calculado, hash_esperado)


def validar_senha(senha: str) -> str | None:
    """Valida uma senha nova.

    Devolve a mensagem de erro a exibir ao usuário, ou ``None`` se estiver boa.
    """
    if not senha:
        return "Informe a nova senha."
    if len(senha) < TAMANHO_MINIMO_SENHA:
        return f"A senha deve ter ao menos {TAMANHO_MINIMO_SENHA} caracteres."
    if senha.isdigit():
        return "A senha não pode ser apenas números."
    if senha.lower() in {"senha", "123456", "admin", "password"}:
        return "Escolha uma senha menos óbvia."
    return None
