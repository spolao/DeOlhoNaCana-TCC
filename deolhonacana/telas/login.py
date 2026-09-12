"""Tela de entrada no sistema."""

from __future__ import annotations

from deolhonacana import config
from deolhonacana.servicos.autenticacao import ErroAutenticacao, PrecisaTrocarSenha
from deolhonacana.telas.base import TelaBase


class TelaLogin(TelaBase):
    """Pede usuário e senha e decide para onde levar quem entrou."""

    def on_pre_enter(self) -> None:
        self.definir_texto("campo_senha", "")
        self.ids.rodape.text = f"{config.APP_NOME} versão {config.VERSAO}"

    def entrar(self) -> None:
        """Autentica e navega, ou mostra o motivo da recusa."""
        usuario = self.texto("campo_usuario")
        senha = self.ids.campo_senha.text  # senha não sofre strip

        try:
            self.aplicativo.autenticacao.entrar(usuario, senha)
        except PrecisaTrocarSenha as aviso:
            self.definir_texto("campo_senha", "")
            tela = self.aplicativo.root.get_screen("alterar_senha")
            tela.preparar(aviso.login, obrigatorio=True)
            self.aplicativo.ir_para("alterar_senha")
            return
        except ErroAutenticacao as erro:
            self.definir_texto("campo_senha", "")
            self.aplicativo.avisar(str(erro), titulo="Não foi possível entrar")
            return

        self.aplicativo.entrar_no_sistema()
