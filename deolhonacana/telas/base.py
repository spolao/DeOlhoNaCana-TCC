"""Peças comuns a todas as telas.

Concentra o que o projeto antigo repetia: quatro gerenciadores de arquivo
idênticos, quatro tratadores de tecla iguais e o mesmo código de diálogo
copiado em cada método. Aqui existe um de cada, parametrizado.
"""

from __future__ import annotations

from collections.abc import Callable

from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen


class TelaBase(MDScreen):
    """Tela com atalhos para o aplicativo e para menus suspensos."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._menu: MDDropdownMenu | None = None

    @property
    def aplicativo(self):
        """Instância do aplicativo em execução."""
        from kivymd.app import MDApp

        return MDApp.get_running_app()

    @property
    def sessao(self):
        """Sessão do usuário autenticado."""
        return self.aplicativo.autenticacao.sessao

    # ------------------------------------------------------------- menus --

    def abrir_menu(
        self,
        chamador,
        itens: list[str],
        ao_escolher: Callable[[str], None],
        largura: int = 4,
    ) -> None:
        """Abre um menu suspenso ancorado no widget ``chamador``.

        ``ao_escolher`` recebe o texto escolhido. O menu se fecha sozinho.
        Lista vazia não abre menu nenhum.
        """
        self.fechar_menu()
        if not itens:
            return

        def selecionar(texto: str) -> None:
            self.fechar_menu()
            ao_escolher(texto)

        self._menu = MDDropdownMenu(
            caller=chamador,
            items=[
                {
                    "text": item,
                    "viewclass": "OneLineListItem",
                    "height": 44,
                    "on_release": lambda x=item: selecionar(x),
                }
                for item in itens
            ],
            width_mult=largura,
            max_height=340,
        )
        self._menu.open()

    def fechar_menu(self) -> None:
        """Fecha o menu suspenso aberto, se houver."""
        if self._menu is not None:
            self._menu.dismiss()
            self._menu = None

    # ------------------------------------------------------- comodidades --

    def texto(self, id_widget: str) -> str:
        """Texto de um campo da tela, já sem espaços nas pontas."""
        widget = self.ids.get(id_widget)
        return widget.text.strip() if widget is not None else ""

    def definir_texto(self, id_widget: str, valor: str) -> None:
        """Escreve num campo da tela, ignorando ids que não existem."""
        widget = self.ids.get(id_widget)
        if widget is not None:
            widget.text = valor

    def limpar_campos(self, *ids_widgets: str) -> None:
        """Esvazia os campos indicados."""
        for id_widget in ids_widgets:
            self.definir_texto(id_widget, "")

    def voltar(self) -> None:
        """Volta ao menu principal."""
        self.fechar_menu()
        self.aplicativo.ir_para("inicio")
