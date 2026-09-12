"""Painel de indicadores, gerado localmente a partir do banco.

Ocupa o lugar do antigo botão "Power-BI", que abria um navegador via Selenium
para um relatório na nuvem, digitando usuário e senha corporativos escritos no
código-fonte. Aqui os gráficos saem do próprio banco, sem rede.
"""

from __future__ import annotations

from deolhonacana.servicos import indicadores, relatorio_pdf
from deolhonacana.telas.base import TelaBase


class TelaIndicadores(TelaBase):
    """Mostra a imagem do painel e os números de resumo."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._arquivo = None

    def on_pre_enter(self) -> None:
        self.atualizar()

    def atualizar(self) -> None:
        """Redesenha os gráficos com os dados atuais."""
        try:
            self._arquivo = indicadores.gerar_painel()
        except Exception as erro:
            self.aplicativo.avisar(
                f"Não foi possível montar os gráficos: {erro}",
                titulo="Erro nos indicadores",
            )
            return

        # reload() força o Kivy a reler o arquivo, que tem sempre o mesmo nome.
        self.ids.painel.source = str(self._arquivo)
        self.ids.painel.reload()

        numeros = indicadores.resumo()
        self.definir_texto(
            "resumo",
            f"{numeros['total']} ocorrências registradas   ·   "
            f"{numeros['pendentes']} pendentes   ·   "
            f"{numeros['finalizadas']} finalizadas   ·   "
            f"média de {numeros['media_dias_pendentes']} dias em aberto   ·   "
            f"pendência mais antiga: {numeros['mais_antiga']} dias   ·   "
            f"{numeros['queimas']} queimas ({numeros['area_queimada_ha']} ha)",
        )

    def abrir_imagem(self) -> None:
        """Abre o PNG do painel no visualizador do sistema, para imprimir."""
        if self._arquivo is None:
            return
        if not relatorio_pdf.abrir_no_sistema(self._arquivo):
            self.aplicativo.avisar(
                f"Imagem salva em:\n{self._arquivo}", titulo="Painel gerado"
            )
