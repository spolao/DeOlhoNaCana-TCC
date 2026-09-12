"""Menu principal, com o resumo da situação atual."""

from __future__ import annotations

from deolhonacana import config
from deolhonacana.dados import repositorio_ocorrencias
from deolhonacana.telas.base import TelaBase


class TelaInicio(TelaBase):
    """Painel de entrada: saudação, números do dia e acesso às funções."""

    def on_pre_enter(self) -> None:
        self.atualizar_saudacao()
        self.atualizar_resumo()

    def atualizar_saudacao(self) -> None:
        """Escreve o nome de quem está usando o sistema."""
        nome = self.sessao.nome or "visitante"
        self.definir_texto("saudacao", f"Bem-vindo, {nome}")
        self.definir_texto(
            "rodape_dados", f"Dados gravados localmente em {config.diretorio_dados()}"
        )
        # Só o administrador cadastra novos usuários.
        self.ids.botao_usuarios.disabled = not self.sessao.e_admin

    def atualizar_resumo(self) -> None:
        """Atualiza os três cartões do topo a partir do banco."""
        por_status = repositorio_ocorrencias.contar_por_status()

        abertas = [
            registro
            for registro in repositorio_ocorrencias.listar()
            if registro["status"] == "Pendente"
        ]
        mais_antiga = max((r["dias_pendentes"] or 0 for r in abertas), default=0)

        self.ids.cartao_pendentes.valor = str(por_status.get("Pendente", 0))
        self.ids.cartao_finalizadas.valor = str(por_status.get("Finalizado", 0))
        self.ids.cartao_mais_antiga.valor = f"{mais_antiga} dias"

    # --------------------------------------------------------- navegação --

    def abrir_pendentes(self) -> None:
        """Abre a consulta já filtrada pelas ocorrências em aberto."""
        consulta = self.aplicativo.root.get_screen("consulta")
        consulta.preparar(status_inicial="Pendente")
        self.aplicativo.ir_para("consulta")

    def abrir_consulta(self) -> None:
        """Abre a consulta sem filtro de status."""
        consulta = self.aplicativo.root.get_screen("consulta")
        consulta.preparar()
        self.aplicativo.ir_para("consulta")

    def trocar_senha(self) -> None:
        """Permite ao próprio usuário trocar a senha fora do primeiro acesso."""
        if not self.sessao.autenticado:
            return
        tela = self.aplicativo.root.get_screen("alterar_senha")
        tela.preparar(self.sessao.usuario.login, obrigatorio=False)
        self.aplicativo.ir_para("alterar_senha")
