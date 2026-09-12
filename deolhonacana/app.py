"""Aplicativo Kivy/KivyMD do De Olho na Cana.

A classe aqui é deliberadamente magra: monta as telas, guarda a sessão e
oferece os serviços de interface que todas as telas usam — diálogos, avisos,
seletor de data e seletor de arquivo. A regra de negócio mora em
:mod:`deolhonacana.servicos`, e o acesso ao banco em
:mod:`deolhonacana.dados`.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import date

from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import FadeTransition, ScreenManager
from kivymd.app import MDApp
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.pickers import MDDatePicker

from deolhonacana import config
from deolhonacana.dados import migracoes
from deolhonacana.servicos import formato
from deolhonacana.servicos.autenticacao import GerenciadorAutenticacao
from deolhonacana.telas.alterar_senha import TelaAlterarSenha
from deolhonacana.telas.clima import TelaClima
from deolhonacana.telas.consulta import TelaConsulta
from deolhonacana.telas.indicadores import TelaIndicadores
from deolhonacana.telas.inicio import TelaInicio
from deolhonacana.telas.lancamento import TelaLancamento
from deolhonacana.telas.login import TelaLogin
from deolhonacana.telas.queima import TelaQueima
from deolhonacana.telas.usuarios import TelaUsuarios

#: Telas do sistema: arquivo .kv, classe e nome usado na navegação.
TELAS = [
    ("login.kv", TelaLogin, "login"),
    ("alterar_senha.kv", TelaAlterarSenha, "alterar_senha"),
    ("inicio.kv", TelaInicio, "inicio"),
    ("lancamento.kv", TelaLancamento, "lancamento"),
    ("consulta.kv", TelaConsulta, "consulta"),
    ("queima.kv", TelaQueima, "queima"),
    ("clima.kv", TelaClima, "clima"),
    ("indicadores.kv", TelaIndicadores, "indicadores"),
    ("usuarios.kv", TelaUsuarios, "usuarios"),
]


def _garantir_recursos() -> None:
    """Desenha as imagens do aplicativo se ainda não existirem.

    Elas não são versionadas — são geradas por ``ferramentas/gerar_recursos.py``.
    Fazer isso também aqui permite que ``python executar.py`` funcione logo
    depois do ``pip install``, sem passo intermediário. No executável
    empacotado as imagens já vêm embutidas, e nada acontece.
    """
    if (config.diretorio_imagens() / "marca.png").is_file():
        return
    try:
        from ferramentas.gerar_recursos import gerar_todos

        gerar_todos()
    except Exception as erro:
        # Sem as imagens a interface continua utilizável: os widgets apenas
        # ficam sem ilustração. Não vale derrubar o programa por isso.
        print(f"Aviso: não foi possível gerar as imagens ({erro}).")


class DeOlhoNaCanaApp(MDApp):
    """Ponto de entrada da interface."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.autenticacao = GerenciadorAutenticacao()
        self._dialogo: MDDialog | None = None
        self._gerenciador_arquivos: MDFileManager | None = None
        self._ao_escolher_arquivo: Callable[[str], None] | None = None

    # ------------------------------------------------------ inicialização --

    def build(self) -> ScreenManager:
        self.title = f"{config.APP_NOME} — {config.ORGANIZACAO}"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.accent_palette = "Amber"

        _garantir_recursos()

        # Cria o banco e semeia o catálogo na primeira execução, em qualquer
        # computador, sem o usuário rodar script nenhum.
        migracoes.inicializar()

        Window.minimum_width, Window.minimum_height = 1024, 680
        Window.size = (1180, 760)
        Window.bind(on_keyboard=self._ao_pressionar_tecla)

        gerenciador = ScreenManager(transition=FadeTransition(duration=0.15))
        for arquivo_kv, classe, nome in TELAS:
            Builder.load_file(config.caminho_tela(arquivo_kv))
            gerenciador.add_widget(classe(name=nome))
        return gerenciador

    # ---------------------------------------------------------- navegação --

    def ir_para(self, nome: str) -> None:
        """Troca a tela corrente, avisando a tela de destino."""
        if self.root is None or not self.root.has_screen(nome):
            return
        self.root.current = nome

    def entrar_no_sistema(self) -> None:
        """Chamada após o login: abre o menu já com o nome do usuário."""
        Window.maximize()
        inicio = self.root.get_screen("inicio")
        inicio.atualizar_saudacao()
        self.ir_para("inicio")

    def sair_da_conta(self) -> None:
        """Encerra a sessão e volta ao login."""
        self.autenticacao.sair()
        Window.restore()
        login = self.root.get_screen("login")
        login.limpar_campos("campo_usuario", "campo_senha")
        self.ir_para("login")

    def encerrar(self) -> None:
        """Fecha o aplicativo, pedindo confirmação."""
        self.confirmar("Deseja realmente fechar o De Olho na Cana?", self.stop)

    # ------------------------------------------------------------ avisos --

    def notificar(self, mensagem: str) -> None:
        """Mensagem curta e passageira no rodapé."""
        toast(mensagem)

    def avisar(self, mensagem: str, titulo: str = "Atenção") -> None:
        """Diálogo de uma mensagem só, com botão de fechar."""
        self._fechar_dialogo()
        self._dialogo = MDDialog(
            title=titulo,
            text=mensagem,
            buttons=[MDFlatButton(text="ENTENDI", on_release=lambda *_: self._fechar_dialogo())],
        )
        self._dialogo.open()

    def confirmar(
        self, mensagem: str, ao_confirmar: Callable[[], None], titulo: str = "Confirmar"
    ) -> None:
        """Diálogo de sim ou não; ``ao_confirmar`` roda só no sim."""
        self._fechar_dialogo()

        def confirmado(*_) -> None:
            self._fechar_dialogo()
            ao_confirmar()

        self._dialogo = MDDialog(
            title=titulo,
            text=mensagem,
            buttons=[
                MDFlatButton(text="CANCELAR", on_release=lambda *_: self._fechar_dialogo()),
                MDFlatButton(text="CONFIRMAR", on_release=confirmado),
            ],
        )
        self._dialogo.open()

    def perguntar_texto(
        self,
        titulo: str,
        rotulo: str,
        ao_responder: Callable[[str], None],
        valor_inicial: str = "",
    ) -> None:
        """Diálogo com um campo de texto — usado para pedir o responsável."""
        from kivymd.uix.textfield import MDTextField

        self._fechar_dialogo()
        campo = MDTextField(hint_text=rotulo, text=valor_inicial, size_hint_x=1)

        def responder(*_) -> None:
            valor = campo.text.strip()
            self._fechar_dialogo()
            ao_responder(valor)

        self._dialogo = MDDialog(
            title=titulo,
            type="custom",
            content_cls=campo,
            buttons=[
                MDFlatButton(text="CANCELAR", on_release=lambda *_: self._fechar_dialogo()),
                MDFlatButton(text="CONFIRMAR", on_release=responder),
            ],
        )
        self._dialogo.open()

    def _fechar_dialogo(self, *_) -> None:
        if self._dialogo is not None:
            self._dialogo.dismiss()
            self._dialogo = None

    # ------------------------------------------------- seletor de datas --

    def escolher_data(self, ao_escolher: Callable[[str], None]) -> None:
        """Abre o calendário e devolve a data escolhida como dd/mm/aaaa."""
        seletor = MDDatePicker(max_date=date.today())
        seletor.bind(
            on_save=lambda _instancia, valor, _intervalo: ao_escolher(
                formato.data_para_texto(valor)
            )
        )
        seletor.open()

    # ----------------------------------------------- seletor de arquivos --

    def escolher_arquivo(self, ao_escolher: Callable[[str], None]) -> None:
        """Abre o navegador de arquivos do KivyMD para escolher uma imagem.

        Um único gerenciador atende todas as telas: quem chama informa o que
        fazer com o caminho escolhido.
        """
        self._ao_escolher_arquivo = ao_escolher
        if self._gerenciador_arquivos is None:
            self._gerenciador_arquivos = MDFileManager(
                exit_manager=self._fechar_arquivos,
                select_path=self._arquivo_escolhido,
                preview=True,
                ext=[".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"],
            )
        inicio = os.path.expanduser("~")
        imagens = os.path.join(inicio, "Pictures")
        self._gerenciador_arquivos.show(imagens if os.path.isdir(imagens) else inicio)

    def _arquivo_escolhido(self, caminho: str) -> None:
        retorno = self._ao_escolher_arquivo
        self._fechar_arquivos()
        if retorno is not None:
            retorno(caminho)

    def _fechar_arquivos(self, *_) -> None:
        if self._gerenciador_arquivos is not None:
            self._gerenciador_arquivos.close()
        self._ao_escolher_arquivo = None

    # ------------------------------------------------------------ teclado --

    def _ao_pressionar_tecla(self, _janela, tecla, *_args) -> bool:
        """Esc fecha o navegador de arquivos em vez de sair da tela."""
        if tecla in (1001, 27) and self._gerenciador_arquivos is not None:
            self._fechar_arquivos()
            return True
        return False


def executar() -> None:
    """Sobe a interface. Chamado por ``executar.py``."""
    DeOlhoNaCanaApp().run()
