"""Cadastro de usuários, restrito ao perfil administrador.

O projeto anterior não tinha esta tela: usuários só existiam se alguém os
inserisse à mão no banco com um cliente SQLite, e a senha ficava em texto puro.
"""

from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.datatables import MDDataTable

from deolhonacana import seguranca
from deolhonacana.dados import repositorio_usuarios
from deolhonacana.telas.base import TelaBase

PERFIS = ["operador", "admin"]


class TelaUsuarios(TelaBase):
    """Lista, cadastra e desativa usuários."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tabela: MDDataTable | None = None
        self._usuarios: list = []
        self._selecionado: str | None = None

    def on_pre_enter(self) -> None:
        if not self.sessao.e_admin:
            self.aplicativo.avisar(
                "Apenas o administrador pode gerenciar usuários.",
                titulo="Acesso restrito",
            )
            self.aplicativo.ir_para("inicio")
            return
        self._garantir_tabela()
        self.atualizar()

    def _garantir_tabela(self) -> None:
        if self._tabela is not None:
            return
        self._tabela = MDDataTable(
            use_pagination=True,
            rows_num=10,
            column_data=[
                ("Login", dp(40)),
                ("Nome", dp(60)),
                ("Perfil", dp(30)),
                ("Situação", dp(34)),
                ("Primeiro acesso", dp(40)),
            ],
            row_data=[],
            elevation=1,
        )
        self._tabela.bind(on_row_press=self._linha_pressionada)
        self.ids.area_tabela.add_widget(self._tabela)

    def atualizar(self) -> None:
        """Recarrega a lista de usuários, inclusive os desativados."""
        if self._tabela is None:
            return
        self._usuarios = repositorio_usuarios.listar(incluir_inativos=True)
        self._selecionado = None
        self._tabela.row_data = [
            [
                usuario.login,
                usuario.nome,
                usuario.perfil,
                "Ativo" if usuario.ativo else "Desativado",
                "Sim" if usuario.primeiro_acesso else "Não",
            ]
            for usuario in self._usuarios
        ]
        self.definir_texto("resumo", f"{len(self._usuarios)} usuário(s) cadastrado(s)")

    def _linha_pressionada(self, _tabela, celula) -> None:
        indice = int(celula.index / 5)
        if 0 <= indice < len(self._usuarios):
            self._selecionado = self._usuarios[indice].login
            self.definir_texto(
                "resumo",
                f"{len(self._usuarios)} usuário(s) · selecionado: {self._selecionado}",
            )

    def escolher_perfil(self) -> None:
        self.abrir_menu(
            self.ids.botao_perfil,
            PERFIS,
            lambda texto: setattr(self.ids.botao_perfil, "text", texto),
            largura=3,
        )

    def cadastrar(self) -> None:
        """Cria um usuário com senha provisória, a ser trocada no primeiro login."""
        login = self.texto("campo_login")
        nome = self.texto("campo_nome")
        senha = self.ids.campo_senha.text

        if not login:
            self.aplicativo.avisar("Informe o login.", titulo="Cadastro incompleto")
            return
        if not nome:
            self.aplicativo.avisar("Informe o nome.", titulo="Cadastro incompleto")
            return

        problema = seguranca.validar_senha(senha)
        if problema:
            self.aplicativo.avisar(problema, titulo="Senha provisória inválida")
            return

        try:
            repositorio_usuarios.criar(login, nome, senha, self.ids.botao_perfil.text)
        except ValueError as erro:
            self.aplicativo.avisar(str(erro), titulo="Não foi possível cadastrar")
            return

        self.limpar_campos("campo_login", "campo_nome", "campo_senha")
        self.aplicativo.notificar(
            f"Usuário {login} cadastrado. Ele trocará a senha no primeiro acesso."
        )
        self.atualizar()

    def alternar_situacao(self) -> None:
        """Ativa ou desativa o usuário selecionado."""
        if self._selecionado is None:
            self.aplicativo.avisar(
                "Clique numa linha para escolher o usuário.",
                titulo="Nenhum usuário selecionado",
            )
            return
        if self._selecionado == self.sessao.usuario.login:
            self.aplicativo.avisar(
                "Você não pode desativar a própria conta.", titulo="Operação negada"
            )
            return

        usuario = next(u for u in self._usuarios if u.login == self._selecionado)
        acao = "desativar" if usuario.ativo else "reativar"

        def confirmar() -> None:
            repositorio_usuarios.definir_ativo(usuario.login, not usuario.ativo)
            self.aplicativo.notificar(f"Usuário {usuario.login} atualizado.")
            self.atualizar()

        self.aplicativo.confirmar(
            f"Deseja {acao} o usuário {usuario.login}?", confirmar
        )
