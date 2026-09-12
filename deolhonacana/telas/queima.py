"""Registro de combate a incêndio."""

from __future__ import annotations

from datetime import date

from deolhonacana.dados import repositorio_queimas
from deolhonacana.servicos import formato, registros
from deolhonacana.telas.base import TelaBase


class TelaQueima(TelaBase):
    """Boletim de queima: onde foi, quanto queimou e quanto durou o combate."""

    #: Campos numéricos que compõem a área atingida.
    CAMPOS_AREA = ("campo_cana_ha", "campo_palha_ha", "campo_pasto_ha",
                   "campo_mata_ha", "campo_app_ha")

    def on_pre_enter(self) -> None:
        if not self.texto("campo_data"):
            self.definir_texto("campo_data", formato.data_para_texto(date.today()))
        self.atualizar_calculados()

    def escolher_data(self) -> None:
        self.aplicativo.escolher_data(
            lambda texto: self.definir_texto("campo_data", texto)
        )

    def alternar_colheita(self) -> None:
        """Alterna o campo que diz se a área já havia sido colhida."""
        atual = self.ids.botao_colheu.text
        self.ids.botao_colheu.text = "Já colheu: Não" if atual.endswith("Sim") else "Já colheu: Sim"

    def atualizar_calculados(self) -> None:
        """Recalcula área total e tempo de combate conforme o usuário digita.

        O projeto antigo guardava o tempo de combate numa coluna, o que
        permitia divergir das horas informadas. Aqui ele é sempre derivado.
        """
        total = sum(formato.para_numero(self.texto(campo)) for campo in self.CAMPOS_AREA)
        duracao = repositorio_queimas.calcular_tempo_combate(
            self.texto("campo_hora_inicio"), self.texto("campo_hora_fim")
        )
        self.definir_texto(
            "resumo",
            f"Área total atingida: {formato.numero_para_texto(total)} ha"
            + (f"   ·   Tempo de combate: {duracao}" if duracao else ""),
        )

    def salvar(self) -> None:
        """Valida e grava o boletim."""
        usuario = self.sessao.usuario
        try:
            numero = registros.salvar_queima(
                data_texto=self.texto("campo_data"),
                fazenda=self.texto("campo_fazenda"),
                gleba=self.texto("campo_gleba"),
                quadra=self.texto("campo_quadra"),
                viatura=self.texto("campo_viatura"),
                hora_inicio=self.texto("campo_hora_inicio"),
                hora_fim=self.texto("campo_hora_fim"),
                colaboradores=self.texto("campo_colaboradores"),
                cana_ton=self.texto("campo_cana_ton"),
                cana_ha=self.texto("campo_cana_ha"),
                palha_ha=self.texto("campo_palha_ha"),
                pasto_ha=self.texto("campo_pasto_ha"),
                mata_ha=self.texto("campo_mata_ha"),
                app_ha=self.texto("campo_app_ha"),
                ja_colheu="Sim" if self.ids.botao_colheu.text.endswith("Sim") else "Não",
                observacao=self.texto("campo_observacao"),
                usuario_id=usuario.id if usuario else None,
            )
        except registros.ErroValidacao as erro:
            self.aplicativo.avisar(str(erro), titulo="Não foi possível salvar")
            return

        self.aplicativo.notificar(f"Queima {numero} registrada.")
        self.limpar()

    def limpar(self) -> None:
        """Esvazia o formulário para o próximo boletim."""
        self.limpar_campos(
            "campo_fazenda", "campo_gleba", "campo_quadra", "campo_viatura",
            "campo_hora_inicio", "campo_hora_fim", "campo_colaboradores",
            "campo_cana_ton", "campo_cana_ha", "campo_palha_ha",
            "campo_pasto_ha", "campo_mata_ha", "campo_app_ha", "campo_observacao",
        )
        self.definir_texto("campo_data", formato.data_para_texto(date.today()))
        self.ids.botao_colheu.text = "Já colheu: Não"
        self.atualizar_calculados()
