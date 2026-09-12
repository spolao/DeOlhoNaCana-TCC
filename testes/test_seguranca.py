"""Testes do armazenamento de senhas."""

from __future__ import annotations

import pytest

from deolhonacana import seguranca


def test_senha_nao_aparece_no_hash():
    """O hash não pode conter a senha em lugar nenhum."""
    senha = "cana2026"
    hash_gerado, sal = seguranca.criar_credencial(senha)
    assert senha not in hash_gerado
    assert senha not in sal


def test_senha_correta_e_aceita():
    hash_gerado, sal = seguranca.criar_credencial("cana2026")
    assert seguranca.verificar_senha("cana2026", hash_gerado, sal)


def test_senha_errada_e_recusada():
    hash_gerado, sal = seguranca.criar_credencial("cana2026")
    assert not seguranca.verificar_senha("cana2025", hash_gerado, sal)
    assert not seguranca.verificar_senha("", hash_gerado, sal)


def test_mesma_senha_gera_hashes_diferentes():
    """O sal por usuário impede identificar senhas iguais comparando hashes."""
    primeiro, _ = seguranca.criar_credencial("cana2026")
    segundo, _ = seguranca.criar_credencial("cana2026")
    assert primeiro != segundo


def test_registro_corrompido_nao_derruba_o_login():
    """Sal inválido devolve falso em vez de estourar exceção."""
    assert not seguranca.verificar_senha("cana2026", "abc", "nao-e-hexadecimal")


@pytest.mark.parametrize(
    "senha",
    ["", "abc", "12345678", "senha", "admin"],
)
def test_senhas_fracas_sao_recusadas(senha):
    assert seguranca.validar_senha(senha) is not None


@pytest.mark.parametrize("senha", ["cana2026", "Talhao#14", "boa esperanca 7"])
def test_senhas_aceitaveis_passam(senha):
    assert seguranca.validar_senha(senha) is None
