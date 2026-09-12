"""Estruturas de dados do domínio.

São objetos simples de transporte entre os repositórios, os serviços e a
interface. Nenhum deles fala com o banco: quem persiste é o repositório.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Usuario:
    """Pessoa que opera o sistema."""

    id: int
    login: str
    nome: str
    perfil: str = "operador"
    primeiro_acesso: bool = True
    ativo: bool = True

    @property
    def e_admin(self) -> bool:
        return self.perfil == "admin"


@dataclass(frozen=True)
class Servico:
    """Item do catálogo, sempre pertencente a uma categoria."""

    id: int
    categoria: str
    codigo: str
    nome: str
    rotulo: str


@dataclass
class Ocorrencia:
    """Apontamento de campo: um problema observado numa quadra."""

    data_abertura: date
    servico_id: int | None = None
    gleba: str = ""
    quadra: str = ""
    fazenda: str = ""
    municipio: str = ""
    administrador: str = ""
    observacao: str = ""
    responsavel: str = ""
    status: str = "Pendente"
    data_conclusao: date | None = None
    registrado_por: int | None = None
    id: int | None = None
    anexos: list[str] = field(default_factory=list)


@dataclass
class Queima:
    """Ocorrência de incêndio e o respectivo combate."""

    data: date
    fazenda: str = ""
    gleba: str = ""
    quadra: str = ""
    viatura: str = ""
    hora_inicio: str = ""
    hora_fim: str = ""
    colaboradores: int = 0
    cana_ton: float = 0.0
    cana_ha: float = 0.0
    palha_ha: float = 0.0
    pasto_ha: float = 0.0
    mata_ha: float = 0.0
    app_ha: float = 0.0
    ja_colheu: str = "Não"
    observacao: str = ""
    registrado_por: int | None = None
    id: int | None = None

    @property
    def area_total_ha(self) -> float:
        """Área atingida somando todos os tipos de cobertura."""
        return self.cana_ha + self.palha_ha + self.pasto_ha + self.mata_ha + self.app_ha


@dataclass
class RegistroClima:
    """Leitura meteorológica anotada manualmente pelo operador."""

    data: date
    hora: str
    fonte: str = ""
    temperatura: float | None = None
    sensacao_termica: float | None = None
    umidade_relativa: float | None = None
    vento: float | None = None
    registrado_por: int | None = None
    id: int | None = None
