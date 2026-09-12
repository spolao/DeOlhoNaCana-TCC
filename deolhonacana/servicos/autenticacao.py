"""Regras de login, sessão e troca de senha.

Concentra o que antes estava espalhado pelo método ``login`` da classe do
aplicativo: comparação de senha, controle de primeiro acesso, contagem de
tentativas e bloqueio temporário.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from deolhonacana import seguranca
from deolhonacana.dados import repositorio_usuarios
from deolhonacana.dominio.modelos import Usuario

#: Tentativas erradas seguidas antes de bloquear o login daquele usuário.
TENTATIVAS_ATE_BLOQUEIO = 5

#: Duração do bloqueio, em segundos.
SEGUNDOS_BLOQUEIO = 60


class ErroAutenticacao(Exception):
    """Falha de login com mensagem já pronta para mostrar ao usuário."""


class PrecisaTrocarSenha(Exception):
    """Login correto, mas a senha precisa ser trocada antes de prosseguir."""

    def __init__(self, login: str) -> None:
        super().__init__("É o primeiro acesso: escolha uma nova senha.")
        self.login = login


@dataclass
class Sessao:
    """Quem está usando o sistema agora.

    Uma instância só é criada pelo :class:`GerenciadorAutenticacao`; a
    interface a consulta para saber o nome a exibir e o perfil.
    """

    usuario: Usuario | None = None

    @property
    def autenticado(self) -> bool:
        return self.usuario is not None

    @property
    def nome(self) -> str:
        return self.usuario.nome if self.usuario else ""

    @property
    def e_admin(self) -> bool:
        return bool(self.usuario and self.usuario.e_admin)

    def encerrar(self) -> None:
        self.usuario = None


@dataclass
class GerenciadorAutenticacao:
    """Autentica usuários e mantém a sessão corrente."""

    sessao: Sessao = field(default_factory=Sessao)
    _tentativas: dict[str, int] = field(default_factory=dict, repr=False)
    _bloqueados_ate: dict[str, float] = field(default_factory=dict, repr=False)

    def segundos_de_bloqueio(self, login: str) -> int:
        """Quanto falta do bloqueio deste login; zero se estiver liberado."""
        restante = self._bloqueados_ate.get(login.strip().lower(), 0) - time.monotonic()
        return max(0, int(restante))

    def entrar(self, login: str, senha: str) -> Usuario:
        """Valida as credenciais e abre a sessão.

        Levanta :class:`PrecisaTrocarSenha` no primeiro acesso e
        :class:`ErroAutenticacao` em qualquer falha.
        """
        login = login.strip()
        chave = login.lower()

        if not login or not senha:
            raise ErroAutenticacao("Informe usuário e senha.")

        restante = self.segundos_de_bloqueio(login)
        if restante:
            raise ErroAutenticacao(
                f"Muitas tentativas. Aguarde {restante} segundos e tente de novo."
            )

        usuario = repositorio_usuarios.buscar_por_login(login)
        credencial = repositorio_usuarios.obter_credencial(login)

        # Mensagem única para usuário inexistente e senha errada, para não
        # revelar quais logins existem.
        if usuario is None or credencial is None:
            self._registrar_falha(chave)
            raise ErroAutenticacao("Usuário ou senha incorretos.")

        if not usuario.ativo:
            raise ErroAutenticacao("Este usuário está desativado.")

        senha_hash, sal = credencial
        if not seguranca.verificar_senha(senha, senha_hash, sal):
            self._registrar_falha(chave)
            raise ErroAutenticacao("Usuário ou senha incorretos.")

        self._tentativas.pop(chave, None)
        self._bloqueados_ate.pop(chave, None)

        if usuario.primeiro_acesso:
            raise PrecisaTrocarSenha(usuario.login)

        self.sessao.usuario = usuario
        return usuario

    def trocar_senha(self, login: str, nova_senha: str, confirmacao: str) -> Usuario:
        """Troca a senha e já deixa o usuário autenticado.

        Levanta :class:`ErroAutenticacao` se as senhas não coincidirem ou se a
        nova senha não passar nas regras de :func:`seguranca.validar_senha`.
        """
        if nova_senha != confirmacao:
            raise ErroAutenticacao("As senhas não coincidem.")

        problema = seguranca.validar_senha(nova_senha)
        if problema:
            raise ErroAutenticacao(problema)

        if not repositorio_usuarios.alterar_senha(login, nova_senha):
            raise ErroAutenticacao("Usuário não encontrado.")

        usuario = repositorio_usuarios.buscar_por_login(login)
        self.sessao.usuario = usuario
        return usuario

    def sair(self) -> None:
        """Encerra a sessão corrente."""
        self.sessao.encerrar()

    def _registrar_falha(self, chave: str) -> None:
        self._tentativas[chave] = self._tentativas.get(chave, 0) + 1
        if self._tentativas[chave] >= TENTATIVAS_ATE_BLOQUEIO:
            self._bloqueados_ate[chave] = time.monotonic() + SEGUNDOS_BLOQUEIO
            self._tentativas[chave] = 0
