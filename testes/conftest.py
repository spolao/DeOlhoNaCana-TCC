"""Configuração comum dos testes.

Todo teste roda contra um banco recém-criado numa pasta temporária. Como
:func:`deolhonacana.config.diretorio_dados` consulta a variável de ambiente
``DONC_DIR`` a cada chamada, apontá-la para o ``tmp_path`` isola banco, anexos
e relatórios de uma vez — sem tocar nos dados reais de quem estiver rodando.
"""

from __future__ import annotations

import pytest

from deolhonacana import config
from deolhonacana.dados import migracoes


@pytest.fixture
def banco(tmp_path, monkeypatch):
    """Banco limpo, já com o esquema criado e o catálogo semeado."""
    monkeypatch.setenv(config.VAR_AMBIENTE_DADOS, str(tmp_path / "dados"))
    migracoes.inicializar()
    return tmp_path / "dados"


@pytest.fixture
def usuario(banco):
    """Usuário comum já com a senha definida, pronto para autenticar."""
    from deolhonacana.dados import repositorio_usuarios

    criado = repositorio_usuarios.criar("maria", "Maria Souza", "provisoria1")
    repositorio_usuarios.alterar_senha("maria", "campo2026")
    return repositorio_usuarios.buscar_por_login(criado.login)


@pytest.fixture
def servico_id(banco):
    """Um serviço qualquer do catálogo, para vincular às ocorrências."""
    from deolhonacana.dados import repositorio_catalogo

    return repositorio_catalogo.listar_servicos("4-ESTRADA")[0].id
