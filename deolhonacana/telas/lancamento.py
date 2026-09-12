"""Lançamento de uma ocorrência de campo.

Esta é a tela que, no projeto anterior, tinha um botão SALVAR ligado a um
método inexistente: nenhum apontamento chegava ao banco. Aqui ela valida,
copia as fotos para a pasta de dados e grava.
"""

from __future__ import annotations

from datetime import date

from deolhonacana import config
from deolhonacana.dados import repositorio_catalogo
from deolhonacana.servicos import formato, registros
from deolhonacana.telas.base import TelaBase

#: Quantidade de fotos que podem acompanhar uma ocorrência.
QUANTIDADE_FOTOS = 3


class TelaLancamento(TelaBase):
    """Formulário de abertura de ocorrência."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Caminho da imagem escolhida em cada um dos três espaços de foto.
        self._fotos: list[str] = [""] * QUANTIDADE_FOTOS

    def on_pre_enter(self) -> None:
        if not self.texto("campo_data"):
            self.definir_texto("campo_data", formato.data_para_texto(date.today()))
        self._carregar_glebas()

    # ------------------------------------------------------- seletores --

    def _carregar_glebas(self) -> None:
        self._glebas = repositorio_catalogo.listar_glebas()

    def escolher_gleba(self) -> None:
        """Menu com as glebas cadastradas."""
        rotulos = [f"{g['codigo']} — {g['fazenda']}" for g in self._glebas]
        self.abrir_menu(self.ids.botao_gleba, rotulos, self._gleba_escolhida, largura=5)

    def _gleba_escolhida(self, rotulo: str) -> None:
        codigo = rotulo.split(" — ")[0]
        self.ids.botao_gleba.text = rotulo
        dados = repositorio_catalogo.buscar_gleba(codigo) or {}
        self.definir_texto(
            "resumo_gleba",
            f"{dados.get('fazenda', '')} · {dados.get('municipio', '')} · "
            f"{dados.get('administrador', '')}",
        )

    def escolher_categoria(self) -> None:
        """Menu com as 27 categorias do catálogo."""
        self.abrir_menu(
            self.ids.botao_categoria,
            repositorio_catalogo.listar_categorias(),
            self._categoria_escolhida,
            largura=6,
        )

    def _categoria_escolhida(self, rotulo: str) -> None:
        self.ids.botao_categoria.text = rotulo
        # Trocar de categoria invalida o serviço escolhido antes.
        self.ids.botao_servico.text = registros.PLACEHOLDER_SERVICO

    def escolher_servico(self) -> None:
        """Menu com os serviços da categoria escolhida."""
        categoria = self.ids.botao_categoria.text
        if categoria == registros.PLACEHOLDER_CATEGORIA:
            self.aplicativo.notificar("Escolha primeiro a categoria.")
            return
        servicos = repositorio_catalogo.listar_servicos(categoria)
        self.abrir_menu(
            self.ids.botao_servico,
            [servico.rotulo for servico in servicos],
            lambda texto: setattr(self.ids.botao_servico, "text", texto),
            largura=7,
        )

    def escolher_data(self) -> None:
        """Abre o calendário para a data de abertura."""
        self.aplicativo.escolher_data(
            lambda texto: self.definir_texto("campo_data", texto)
        )

    # ----------------------------------------------------------- fotos --

    def escolher_foto(self, indice: int) -> None:
        """Abre o seletor de arquivos para um dos três espaços de foto."""
        self.aplicativo.escolher_arquivo(lambda caminho: self._foto_escolhida(indice, caminho))

    def _foto_escolhida(self, indice: int, caminho: str) -> None:
        self._fotos[indice] = caminho
        self.ids[f"foto_{indice}"].source = caminho
        self.aplicativo.notificar("Imagem anexada.")

    def remover_fotos(self) -> None:
        """Desfaz a seleção das três fotos."""
        vazio = config.caminho_imagem("sem-foto.png")
        for indice in range(QUANTIDADE_FOTOS):
            self._fotos[indice] = ""
            self.ids[f"foto_{indice}"].source = vazio

    # ---------------------------------------------------------- gravar --

    def salvar(self) -> None:
        """Valida o formulário e grava a ocorrência."""
        usuario = self.sessao.usuario
        try:
            numero = registros.salvar_ocorrencia(
                data_texto=self.texto("campo_data"),
                categoria=self.ids.botao_categoria.text,
                servico=self.ids.botao_servico.text,
                gleba=self.ids.botao_gleba.text.split(" — ")[0]
                if " — " in self.ids.botao_gleba.text
                else "",
                quadra=self.texto("campo_quadra"),
                observacao=self.texto("campo_observacao"),
                responsavel=self.texto("campo_responsavel"),
                imagens=[caminho for caminho in self._fotos if caminho],
                usuario_id=usuario.id if usuario else None,
            )
        except registros.ErroValidacao as erro:
            self.aplicativo.avisar(str(erro), titulo="Não foi possível salvar")
            return

        self.aplicativo.notificar(f"Ocorrência {numero} registrada.")
        self.limpar()

    def limpar(self) -> None:
        """Devolve o formulário ao estado inicial para o próximo lançamento."""
        self.limpar_campos("campo_quadra", "campo_observacao", "campo_responsavel")
        self.definir_texto("campo_data", formato.data_para_texto(date.today()))
        self.definir_texto("resumo_gleba", "")
        self.ids.botao_categoria.text = registros.PLACEHOLDER_CATEGORIA
        self.ids.botao_servico.text = registros.PLACEHOLDER_SERVICO
        self.ids.botao_gleba.text = "Selecione a gleba"
        self.remover_fotos()
