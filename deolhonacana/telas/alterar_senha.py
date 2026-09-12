"""Troca de senha, obrigatória no primeiro acesso."""

from __future__ import annotations

from deolhonacana import seguranca
from deolhonacana.servicos.autenticacao import ErroAutenticacao
from deolhonacana.telas.base import TelaBase


class TelaAlterarSenha(TelaBase):
    """Define a senha definitiva de um usuário.

    Chega aqui quem acabou de ser cadastrado — nesse caso o retorno ao login é
    bloqueado até a troca — ou quem escolheu trocar a própria senha pelo menu.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._login = ""
        self._obrigatorio = False

    def preparar(self, login: str, obrigatorio: bool = False) -> None:
        """Configura a tela antes de exibi-la."""
        self._login = login
        self._obrigatorio = obrigatorio
        self.definir_texto("campo_usuario", login)
        self.limpar_campos("campo_nova", "campo_confirmacao")
        self.ids.aviso.text = (
            "Este é o seu primeiro acesso. Escolha uma senha para continuar."
            if obrigatorio
            else "Escolha a sua nova senha."
        )
        self.ids.botao_voltar.text = "CANCELAR" if not obrigatorio else "VOLTAR AO LOGIN"
        self.ids.regra.text = (
            f"Mínimo de {seguranca.TAMANHO_MINIMO_SENHA} caracteres e não pode ser "
            "só números."
        )

    def confirmar(self) -> None:
        """Valida e grava a nova senha."""
        nova = self.ids.campo_nova.text
        confirmacao = self.ids.campo_confirmacao.text

        try:
            self.aplicativo.autenticacao.trocar_senha(self._login, nova, confirmacao)
        except ErroAutenticacao as erro:
            self.aplicativo.avisar(str(erro), titulo="Senha não alterada")
            return

        self.limpar_campos("campo_nova", "campo_confirmacao")
        self.aplicativo.notificar("Senha alterada com sucesso.")
        self.aplicativo.entrar_no_sistema()

    def cancelar(self) -> None:
        """Sai da tela sem trocar a senha.

        No primeiro acesso o usuário volta ao login, porque a sessão ainda não
        foi aberta; nos demais casos volta ao menu.
        """
        self.limpar_campos("campo_nova", "campo_confirmacao")
        if self._obrigatorio or not self.sessao.autenticado:
            self.aplicativo.ir_para("login")
        else:
            self.aplicativo.ir_para("inicio")
