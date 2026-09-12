"""Registro manual de leituras meteorológicas."""

from __future__ import annotations

from datetime import date, datetime

from deolhonacana.dados import repositorio_clima
from deolhonacana.servicos import formato, registros
from deolhonacana.telas.base import TelaBase

#: Origens habituais da leitura, oferecidas num menu para padronizar o texto.
FONTES = [
    "Estação da fazenda",
    "Termômetro do escritório",
    "Boletim meteorológico",
    "Aplicativo de previsão",
    "Outra",
]


class TelaClima(TelaBase):
    """Anota temperatura, umidade e vento observados no momento."""

    def on_pre_enter(self) -> None:
        agora = datetime.now()
        if not self.texto("campo_data"):
            self.definir_texto("campo_data", formato.data_para_texto(date.today()))
        if not self.texto("campo_hora"):
            self.definir_texto("campo_hora", agora.strftime("%H:%M"))
        self.mostrar_ultima()

    def mostrar_ultima(self) -> None:
        """Exibe a leitura mais recente já gravada, como referência."""
        ultima = repositorio_clima.ultima_leitura()
        if not ultima:
            self.definir_texto("ultima_leitura", "Nenhuma leitura registrada ainda.")
            return
        self.definir_texto(
            "ultima_leitura",
            "Última leitura: "
            f"{formato.data_para_texto(str(ultima['data']))} às {ultima['hora']} · "
            f"{formato.numero_para_texto(ultima['temperatura'], 1)} °C · "
            f"umidade {formato.numero_para_texto(ultima['umidade_relativa'], 0)}% · "
            f"vento {formato.numero_para_texto(ultima['vento'], 1)} km/h "
            f"({ultima['fonte'] or 'fonte não informada'})",
        )

    def escolher_data(self) -> None:
        self.aplicativo.escolher_data(
            lambda texto: self.definir_texto("campo_data", texto)
        )

    def escolher_fonte(self) -> None:
        self.abrir_menu(
            self.ids.botao_fonte,
            FONTES,
            lambda texto: setattr(self.ids.botao_fonte, "text", texto),
            largura=5,
        )

    def salvar(self) -> None:
        """Valida e grava a leitura."""
        usuario = self.sessao.usuario
        fonte = self.ids.botao_fonte.text
        try:
            registros.salvar_clima(
                data_texto=self.texto("campo_data"),
                hora=self.texto("campo_hora"),
                fonte="" if fonte == "Selecione a fonte" else fonte,
                temperatura=self.texto("campo_temperatura"),
                sensacao_termica=self.texto("campo_sensacao"),
                umidade=self.texto("campo_umidade"),
                vento=self.texto("campo_vento"),
                usuario_id=usuario.id if usuario else None,
            )
        except registros.ErroValidacao as erro:
            self.aplicativo.avisar(str(erro), titulo="Não foi possível salvar")
            return

        self.aplicativo.notificar("Leitura registrada.")
        self.limpar()
        self.mostrar_ultima()

    def limpar(self) -> None:
        """Esvazia os campos, mantendo data e hora atuais."""
        self.limpar_campos(
            "campo_temperatura", "campo_sensacao", "campo_umidade", "campo_vento"
        )
        self.definir_texto("campo_data", formato.data_para_texto(date.today()))
        self.definir_texto("campo_hora", datetime.now().strftime("%H:%M"))
