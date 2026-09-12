"""Consulta, conclusão e exportação de ocorrências.

No projeto anterior os seletores desta tela existiam sem nenhuma lógica por
trás, a tabela mostrava apenas o dia corrente e não havia como concluir uma
ocorrência nem exportar nada. Aqui os filtros compõem uma consulta de verdade,
a linha selecionada pode ser concluída ou reaberta, e o recorte que estiver na
tela vira PDF.
"""

from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.datatables import MDDataTable

from deolhonacana.dados import repositorio_catalogo, repositorio_ocorrencias
from deolhonacana.dados.repositorio_ocorrencias import Filtro
from deolhonacana.servicos import formato, registros, relatorio_pdf
from deolhonacana.telas.base import TelaBase

#: Opção que representa "não filtrar por este campo".
TODOS = "Todos"

STATUS_POSSIVEIS = [TODOS, "Pendente", "Finalizado"]

#: Colunas da tabela: título, largura e chave correspondente no registro.
#:
#: A fazenda não aparece porque é determinada pela gleba, e a categoria também
#: não, porque o código do serviço já a identifica ("4.1" pertence à categoria
#: 4). Sem essas duas, a tabela inteira cabe na janela sem rolagem lateral —
#: com elas, "Status" e "Responsável" ficavam fora da área visível. Ambas
#: continuam disponíveis nos filtros e no relatório em PDF.
COLUNAS = [
    ("Id", 18, "id"),
    ("Abertura", 26, "data_abertura"),
    ("Gleba", 18, "gleba"),
    ("Quadra", 20, "quadra"),
    ("Serviço", 56, "servico"),
    ("Observação", 44, "observacao"),
    ("Dias", 16, "dias_pendentes"),
    ("Conclusão", 26, "data_conclusao"),
    ("Status", 24, "status"),
    ("Responsável", 30, "responsavel"),
    ("Fotos", 16, "qtd_anexos"),
]


class TelaConsulta(TelaBase):
    """Lista as ocorrências conforme o filtro e age sobre a selecionada."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._tabela: MDDataTable | None = None
        self._registros: list[dict] = []
        self._selecionada: int | None = None

    # ------------------------------------------------------- montagem --

    def on_pre_enter(self) -> None:
        self._garantir_tabela()
        self._carregar_opcoes()
        self.pesquisar()

    def preparar(self, status_inicial: str = TODOS) -> None:
        """Define o filtro de status antes de a tela aparecer."""
        self._garantir_tabela()
        self.ids.botao_status.text = status_inicial or TODOS

    def _garantir_tabela(self) -> None:
        """Cria a tabela uma única vez e a encaixa no espaço reservado."""
        if self._tabela is not None:
            return
        self._tabela = MDDataTable(
            use_pagination=True,
            rows_num=15,
            column_data=[(titulo, dp(largura)) for titulo, largura, _ in COLUNAS],
            row_data=[],
            elevation=1,
        )
        self._tabela.bind(on_row_press=self._linha_pressionada)
        self.ids.area_tabela.add_widget(self._tabela)

    def _carregar_opcoes(self) -> None:
        self._categorias = [TODOS] + repositorio_catalogo.listar_categorias()

    # -------------------------------------------------------- filtros --

    def escolher_categoria(self) -> None:
        self.abrir_menu(
            self.ids.botao_categoria, self._categorias, self._categoria_escolhida, largura=6
        )

    def _categoria_escolhida(self, texto: str) -> None:
        self.ids.botao_categoria.text = texto
        self.ids.botao_servico.text = TODOS
        self.pesquisar()

    def escolher_servico(self) -> None:
        categoria = self.ids.botao_categoria.text
        if categoria == TODOS:
            self.aplicativo.notificar("Escolha uma categoria para filtrar por serviço.")
            return
        rotulos = [TODOS] + [
            servico.rotulo for servico in repositorio_catalogo.listar_servicos(categoria)
        ]
        self.abrir_menu(self.ids.botao_servico, rotulos, self._servico_escolhido, largura=7)

    def _servico_escolhido(self, texto: str) -> None:
        self.ids.botao_servico.text = texto
        self.pesquisar()

    def escolher_status(self) -> None:
        self.abrir_menu(self.ids.botao_status, STATUS_POSSIVEIS, self._status_escolhido, largura=3)

    def _status_escolhido(self, texto: str) -> None:
        self.ids.botao_status.text = texto
        self.pesquisar()

    def escolher_ordenacao(self) -> None:
        self.abrir_menu(
            self.ids.botao_ordenacao,
            list(repositorio_ocorrencias.ORDENACOES),
            self._ordenacao_escolhida,
            largura=4,
        )

    def _ordenacao_escolhida(self, texto: str) -> None:
        self.ids.botao_ordenacao.text = texto
        self.pesquisar()

    def escolher_data(self, campo: str) -> None:
        self.aplicativo.escolher_data(lambda texto: self._data_escolhida(campo, texto))

    def _data_escolhida(self, campo: str, texto: str) -> None:
        self.definir_texto(campo, texto)
        self.pesquisar()

    def limpar_filtros(self) -> None:
        """Volta todos os filtros ao estado neutro."""
        self.ids.botao_categoria.text = TODOS
        self.ids.botao_servico.text = TODOS
        self.ids.botao_status.text = TODOS
        self.ids.botao_ordenacao.text = "Mais recentes"
        self.limpar_campos("campo_inicio", "campo_fim")
        self.pesquisar()

    def _montar_filtro(self) -> Filtro:
        def valor(texto: str) -> str:
            return "" if texto == TODOS else texto

        return Filtro(
            categoria=valor(self.ids.botao_categoria.text),
            servico=valor(self.ids.botao_servico.text),
            status=valor(self.ids.botao_status.text),
            data_inicio=formato.texto_para_data(self.texto("campo_inicio")),
            data_fim=formato.texto_para_data(self.texto("campo_fim")),
            ordenacao=self.ids.botao_ordenacao.text,
        )

    def descricao_do_filtro(self) -> str:
        """Frase que resume o recorte, usada no cabeçalho do PDF."""
        partes = []
        if self.ids.botao_status.text != TODOS:
            partes.append(f"status {self.ids.botao_status.text}")
        if self.ids.botao_categoria.text != TODOS:
            partes.append(f"categoria {self.ids.botao_categoria.text}")
        if self.ids.botao_servico.text != TODOS:
            partes.append(f"serviço {self.ids.botao_servico.text}")
        if self.texto("campo_inicio"):
            partes.append(f"a partir de {self.texto('campo_inicio')}")
        if self.texto("campo_fim"):
            partes.append(f"até {self.texto('campo_fim')}")
        return ", ".join(partes) if partes else "todas as ocorrências"

    # ------------------------------------------------------- pesquisa --

    def pesquisar(self) -> None:
        """Recarrega a tabela com o resultado do filtro atual."""
        if self._tabela is None:
            return
        self._registros = repositorio_ocorrencias.listar(self._montar_filtro())
        self._selecionada = None
        self._tabela.row_data = [self._para_linha(r) for r in self._registros]
        self._atualizar_rodape()

    def _para_linha(self, registro: dict) -> list[str]:
        return [
            str(registro["id"]),
            formato.data_para_texto(str(registro["data_abertura"])),
            registro["gleba"] or "",
            registro["quadra"] or "",
            formato.encurtar(registro["servico"], 34),
            formato.encurtar(registro["observacao"], 22),
            str(registro["dias_pendentes"] or 0),
            formato.data_para_texto(
                registro["data_conclusao"] and str(registro["data_conclusao"])
            ),
            registro["status"],
            formato.encurtar(registro["responsavel"], 18),
            str(registro["qtd_anexos"] or 0),
        ]

    def _atualizar_rodape(self) -> None:
        pendentes = sum(1 for r in self._registros if r["status"] == "Pendente")
        selecao = (
            f" · selecionada: ocorrência {self._selecionada}"
            if self._selecionada
            else " · clique numa linha para selecionar"
        )
        self.definir_texto(
            "resumo",
            f"{len(self._registros)} registro(s), {pendentes} pendente(s){selecao}",
        )

    def _linha_pressionada(self, _tabela, celula) -> None:
        """Guarda o id da ocorrência da linha clicada.

        A tabela avisa qual célula foi tocada; o índice da linha sai da posição
        da célula dividida pelo número de colunas.
        """
        indice_linha = int(celula.index / len(COLUNAS))
        if 0 <= indice_linha < len(self._registros):
            self._selecionada = int(self._registros[indice_linha]["id"])
            self._atualizar_rodape()

    # ---------------------------------------------------------- ações --

    def _registro_selecionado(self) -> dict | None:
        if self._selecionada is None:
            self.aplicativo.avisar(
                "Clique numa linha da tabela para escolher a ocorrência.",
                titulo="Nenhuma ocorrência selecionada",
            )
            return None
        return repositorio_ocorrencias.obter(self._selecionada)

    def concluir(self) -> None:
        """Pede o responsável e finaliza a ocorrência selecionada."""
        registro = self._registro_selecionado()
        if registro is None:
            return
        if registro["status"] == "Finalizado":
            self.aplicativo.avisar(
                f"A ocorrência {registro['id']} já foi finalizada em "
                f"{formato.data_para_texto(str(registro['data_conclusao']))}.",
                titulo="Já finalizada",
            )
            return

        self.aplicativo.perguntar_texto(
            f"Concluir ocorrência {registro['id']}",
            "Responsável pela conclusão",
            self._concluir_com,
            valor_inicial=registro["responsavel"] or self.sessao.nome,
        )

    def _concluir_com(self, responsavel: str) -> None:
        if not responsavel:
            self.aplicativo.notificar("Conclusão cancelada.")
            return
        try:
            registros.concluir_ocorrencia(self._selecionada, responsavel)
        except registros.ErroValidacao as erro:
            self.aplicativo.avisar(str(erro), titulo="Não foi possível concluir")
            return
        self.aplicativo.notificar("Ocorrência concluída.")
        self.pesquisar()

    def reabrir(self) -> None:
        """Devolve uma ocorrência finalizada para pendente."""
        registro = self._registro_selecionado()
        if registro is None:
            return

        def confirmar() -> None:
            try:
                registros.reabrir_ocorrencia(registro["id"])
            except registros.ErroValidacao as erro:
                self.aplicativo.avisar(str(erro), titulo="Não foi possível reabrir")
                return
            self.aplicativo.notificar("Ocorrência reaberta.")
            self.pesquisar()

        self.aplicativo.confirmar(
            f"Reabrir a ocorrência {registro['id']}? A data de conclusão será apagada.",
            confirmar,
        )

    def gerar_pdf(self) -> None:
        """Exporta o recorte atual para PDF e o abre no leitor do sistema."""
        if not self._registros:
            self.aplicativo.avisar(
                "O filtro atual não retornou nenhuma ocorrência.",
                titulo="Nada para exportar",
            )
            return
        try:
            arquivo = relatorio_pdf.gerar(self._registros, self.descricao_do_filtro())
        except Exception as erro:  # o reportlab pode falhar ao ler uma foto
            self.aplicativo.avisar(
                f"Não foi possível gerar o PDF: {erro}", titulo="Erro no relatório"
            )
            return

        if relatorio_pdf.abrir_no_sistema(arquivo):
            self.aplicativo.notificar("Relatório gerado.")
        else:
            self.aplicativo.avisar(
                f"Relatório salvo em:\n{arquivo}", titulo="Relatório gerado"
            )
