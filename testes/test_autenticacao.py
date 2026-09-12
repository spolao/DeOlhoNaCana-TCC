"""Testes de login, primeiro acesso e bloqueio por tentativas."""

from __future__ import annotations

import pytest

from deolhonacana.dados import migracoes, repositorio_usuarios
from deolhonacana.servicos.autenticacao import (
    ErroAutenticacao,
    GerenciadorAutenticacao,
    PrecisaTrocarSenha,
)


@pytest.fixture
def gerenciador(banco):
    return GerenciadorAutenticacao()


def test_conta_inicial_existe_e_e_admin(banco):
    admin = repositorio_usuarios.buscar_por_login(migracoes.LOGIN_INICIAL)
    assert admin is not None
    assert admin.e_admin
    assert admin.primeiro_acesso


def test_primeiro_acesso_exige_troca_de_senha(gerenciador):
    with pytest.raises(PrecisaTrocarSenha):
        gerenciador.entrar(migracoes.LOGIN_INICIAL, migracoes.SENHA_INICIAL)
    assert not gerenciador.sessao.autenticado


def test_troca_de_senha_abre_a_sessao(gerenciador):
    usuario = gerenciador.trocar_senha(migracoes.LOGIN_INICIAL, "cana2026", "cana2026")
    assert gerenciador.sessao.autenticado
    assert gerenciador.sessao.nome == usuario.nome
    assert not usuario.primeiro_acesso


def test_login_normal_apos_a_troca(gerenciador):
    gerenciador.trocar_senha(migracoes.LOGIN_INICIAL, "cana2026", "cana2026")
    gerenciador.sair()
    assert not gerenciador.sessao.autenticado
    assert gerenciador.entrar(migracoes.LOGIN_INICIAL, "cana2026").login == "admin"


def test_senha_errada_e_recusada(gerenciador, usuario):
    with pytest.raises(ErroAutenticacao, match="incorretos"):
        gerenciador.entrar("maria", "errada")
    assert not gerenciador.sessao.autenticado


def test_usuario_inexistente_da_a_mesma_mensagem(gerenciador, usuario):
    """A mensagem não pode revelar quais logins existem."""
    with pytest.raises(ErroAutenticacao) as inexistente:
        gerenciador.entrar("ninguem", "qualquer")
    with pytest.raises(ErroAutenticacao) as senha_errada:
        gerenciador.entrar("maria", "errada")
    assert str(inexistente.value) == str(senha_errada.value)


def test_campos_vazios_sao_recusados(gerenciador):
    with pytest.raises(ErroAutenticacao, match="Informe"):
        gerenciador.entrar("", "")


def test_usuario_desativado_nao_entra(gerenciador, usuario):
    repositorio_usuarios.definir_ativo("maria", False)
    with pytest.raises(ErroAutenticacao, match="desativado"):
        gerenciador.entrar("maria", "campo2026")


def test_login_ignora_maiusculas(gerenciador, usuario):
    assert gerenciador.entrar("MARIA", "campo2026").login == "maria"


def test_bloqueio_apos_tentativas_seguidas(gerenciador, usuario):
    from deolhonacana.servicos import autenticacao

    for _ in range(autenticacao.TENTATIVAS_ATE_BLOQUEIO):
        with pytest.raises(ErroAutenticacao):
            gerenciador.entrar("maria", "errada")

    assert gerenciador.segundos_de_bloqueio("maria") > 0
    # Mesmo com a senha certa, o bloqueio vale enquanto durar.
    with pytest.raises(ErroAutenticacao, match="Aguarde"):
        gerenciador.entrar("maria", "campo2026")


def test_acerto_zera_o_contador(gerenciador, usuario):
    from deolhonacana.servicos import autenticacao

    for _ in range(autenticacao.TENTATIVAS_ATE_BLOQUEIO - 1):
        with pytest.raises(ErroAutenticacao):
            gerenciador.entrar("maria", "errada")

    gerenciador.entrar("maria", "campo2026")
    gerenciador.sair()

    with pytest.raises(ErroAutenticacao):
        gerenciador.entrar("maria", "errada")
    assert gerenciador.segundos_de_bloqueio("maria") == 0


def test_senhas_divergentes_na_troca(gerenciador):
    with pytest.raises(ErroAutenticacao, match="não coincidem"):
        gerenciador.trocar_senha("admin", "cana2026", "cana2027")


def test_senha_fraca_na_troca(gerenciador):
    with pytest.raises(ErroAutenticacao):
        gerenciador.trocar_senha("admin", "123", "123")


def test_login_duplicado_e_recusado(banco, usuario):
    with pytest.raises(ValueError, match="Já existe"):
        repositorio_usuarios.criar("maria", "Outra Maria", "provisoria1")
