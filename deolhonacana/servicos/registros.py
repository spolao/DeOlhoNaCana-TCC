"""Regras de negócio dos três formulários do sistema.

Cada função recebe o que o usuário digitou — sempre texto, como vem da
interface —, valida, converte e delega ao repositório. As telas não conhecem
SQL nem tipos de banco; elas chamam daqui e mostram a mensagem que voltar.

Este módulo é o que o projeto anterior não tinha: os botões SALVAR chamavam
métodos inexistentes, de modo que nenhum apontamento chegava a ser gravado.
"""

from __future__ import annotations

from datetime import date

from deolhonacana.dados import (
    repositorio_catalogo,
    repositorio_clima,
    repositorio_ocorrencias,
    repositorio_queimas,
)
from deolhonacana.dominio.modelos import Ocorrencia, Queima, RegistroClima
from deolhonacana.servicos import anexos as servico_anexos
from deolhonacana.servicos import formato

#: Texto exibido nos seletores enquanto nada foi escolhido.
PLACEHOLDER_CATEGORIA = "Selecione a categoria"
PLACEHOLDER_SERVICO = "Selecione o serviço"


class ErroValidacao(Exception):
    """Dado do formulário inválido, com mensagem pronta para o usuário."""


def _obrigatorio(valor: str | None, rotulo: str) -> str:
    texto = (valor or "").strip()
    if not texto:
        raise ErroValidacao(f"Informe {rotulo}.")
    return texto


def _escolhido(valor: str | None, placeholder: str, rotulo: str) -> str:
    texto = (valor or "").strip()
    if not texto or texto == placeholder:
        raise ErroValidacao(f"Escolha {rotulo}.")
    return texto


def _data_obrigatoria(texto: str | None, rotulo: str = "a data") -> date:
    valor = formato.texto_para_data(texto)
    if valor is None:
        raise ErroValidacao(f"Informe {rotulo} no formato dd/mm/aaaa.")
    if valor > date.today():
        raise ErroValidacao("A data não pode estar no futuro.")
    return valor


# --------------------------------------------------------------- ocorrências --


def salvar_ocorrencia(
    *,
    data_texto: str,
    categoria: str,
    servico: str,
    gleba: str,
    quadra: str,
    observacao: str = "",
    responsavel: str = "",
    imagens: list[str] | None = None,
    usuario_id: int | None = None,
) -> int:
    """Valida e grava um apontamento de campo. Devolve o id criado.

    A fazenda, o município e o administrador não são digitados: vêm da gleba
    cadastrada, o que evita a mesma gleba aparecer com três grafias de fazenda.
    """
    data_abertura = _data_obrigatoria(data_texto)
    _escolhido(categoria, PLACEHOLDER_CATEGORIA, "a categoria")
    rotulo_servico = _escolhido(servico, PLACEHOLDER_SERVICO, "o serviço")
    codigo_gleba = _obrigatorio(gleba, "a gleba")
    numero_quadra = _obrigatorio(quadra, "a quadra")

    servico_id = repositorio_catalogo.id_do_servico(rotulo_servico)
    if servico_id is None:
        raise ErroValidacao("Serviço não encontrado no catálogo.")

    dados_gleba = repositorio_catalogo.buscar_gleba(codigo_gleba) or {}

    guardados: list[str] = []
    for caminho in imagens or []:
        if not caminho:
            continue
        try:
            guardados.append(servico_anexos.guardar(caminho))
        except servico_anexos.ErroAnexo as erro:
            raise ErroValidacao(str(erro)) from erro

    ocorrencia = Ocorrencia(
        data_abertura=data_abertura,
        servico_id=servico_id,
        gleba=codigo_gleba,
        quadra=numero_quadra,
        fazenda=dados_gleba.get("fazenda", ""),
        municipio=dados_gleba.get("municipio", ""),
        administrador=dados_gleba.get("administrador", ""),
        observacao=observacao or "",
        responsavel=responsavel or "",
        registrado_por=usuario_id,
        anexos=guardados,
    )
    return repositorio_ocorrencias.inserir(ocorrencia)


def alterar_ocorrencia(
    *,
    ocorrencia_id: int,
    data_texto: str,
    categoria: str,
    servico: str,
    gleba: str,
    quadra: str,
    observacao: str = "",
    responsavel: str = "",
) -> None:
    """Aplica as edições feitas na tela de alteração."""
    if repositorio_ocorrencias.obter(ocorrencia_id) is None:
        raise ErroValidacao(f"Não existe ocorrência com o id {ocorrencia_id}.")

    data_abertura = _data_obrigatoria(data_texto)
    _escolhido(categoria, PLACEHOLDER_CATEGORIA, "a categoria")
    rotulo_servico = _escolhido(servico, PLACEHOLDER_SERVICO, "o serviço")
    codigo_gleba = _obrigatorio(gleba, "a gleba")
    numero_quadra = _obrigatorio(quadra, "a quadra")

    servico_id = repositorio_catalogo.id_do_servico(rotulo_servico)
    if servico_id is None:
        raise ErroValidacao("Serviço não encontrado no catálogo.")

    dados_gleba = repositorio_catalogo.buscar_gleba(codigo_gleba) or {}

    repositorio_ocorrencias.atualizar(
        ocorrencia_id,
        {
            "data_abertura": data_abertura.isoformat(),
            "servico_id": servico_id,
            "gleba": codigo_gleba,
            "quadra": numero_quadra,
            "fazenda": dados_gleba.get("fazenda", ""),
            "municipio": dados_gleba.get("municipio", ""),
            "administrador": dados_gleba.get("administrador", ""),
            "observacao": observacao or "",
            "responsavel": responsavel or "",
        },
    )


def concluir_ocorrencia(
    ocorrencia_id: int, responsavel: str, data_texto: str | None = None
) -> None:
    """Finaliza uma ocorrência pendente.

    A data de conclusão não pode ser anterior à de abertura — a restrição
    existe também no banco, mas checar aqui permite dar uma mensagem melhor.
    """
    registro = repositorio_ocorrencias.obter(ocorrencia_id)
    if registro is None:
        raise ErroValidacao(f"Não existe ocorrência com o id {ocorrencia_id}.")
    if registro["status"] == "Finalizado":
        raise ErroValidacao("Esta ocorrência já está finalizada.")

    quem = _obrigatorio(responsavel, "o responsável pela conclusão")
    quando = formato.texto_para_data(data_texto) or date.today()

    abertura = formato.texto_para_data(str(registro["data_abertura"]))
    if abertura and quando < abertura:
        raise ErroValidacao(
            "A conclusão não pode ser anterior à abertura "
            f"({formato.data_para_texto(abertura)})."
        )
    if quando > date.today():
        raise ErroValidacao("A data de conclusão não pode estar no futuro.")

    repositorio_ocorrencias.concluir(ocorrencia_id, quem, quando)


def reabrir_ocorrencia(ocorrencia_id: int) -> None:
    """Devolve uma ocorrência finalizada para pendente."""
    registro = repositorio_ocorrencias.obter(ocorrencia_id)
    if registro is None:
        raise ErroValidacao(f"Não existe ocorrência com o id {ocorrencia_id}.")
    if registro["status"] == "Pendente":
        raise ErroValidacao("Esta ocorrência já está pendente.")
    repositorio_ocorrencias.reabrir(ocorrencia_id)


# ------------------------------------------------------------------ queimas --


def salvar_queima(
    *,
    data_texto: str,
    fazenda: str,
    gleba: str = "",
    quadra: str = "",
    viatura: str = "",
    hora_inicio: str = "",
    hora_fim: str = "",
    colaboradores: str = "",
    cana_ton: str = "",
    cana_ha: str = "",
    palha_ha: str = "",
    pasto_ha: str = "",
    mata_ha: str = "",
    app_ha: str = "",
    ja_colheu: str = "Não",
    observacao: str = "",
    usuario_id: int | None = None,
) -> int:
    """Valida e grava um boletim de combate a incêndio."""
    data = _data_obrigatoria(data_texto)
    nome_fazenda = _obrigatorio(fazenda, "a fazenda")

    for rotulo, valor in (("início", hora_inicio), ("término", hora_fim)):
        if valor.strip() and not formato.hora_valida(valor):
            raise ErroValidacao(f"A hora de {rotulo} deve estar no formato HH:MM.")

    queima = Queima(
        data=data,
        fazenda=nome_fazenda,
        gleba=gleba,
        quadra=quadra,
        viatura=viatura,
        hora_inicio=hora_inicio,
        hora_fim=hora_fim,
        colaboradores=formato.para_inteiro(colaboradores),
        cana_ton=formato.para_numero(cana_ton),
        cana_ha=formato.para_numero(cana_ha),
        palha_ha=formato.para_numero(palha_ha),
        pasto_ha=formato.para_numero(pasto_ha),
        mata_ha=formato.para_numero(mata_ha),
        app_ha=formato.para_numero(app_ha),
        ja_colheu="Sim" if str(ja_colheu).strip().lower().startswith("s") else "Não",
        observacao=observacao,
        registrado_por=usuario_id,
    )
    if queima.area_total_ha <= 0 and queima.cana_ton <= 0:
        raise ErroValidacao("Informe ao menos uma área atingida ou o volume de cana.")

    return repositorio_queimas.inserir(queima)


# -------------------------------------------------------------------- clima --


def salvar_clima(
    *,
    data_texto: str,
    hora: str,
    fonte: str = "",
    temperatura: str = "",
    sensacao_termica: str = "",
    umidade: str = "",
    vento: str = "",
    usuario_id: int | None = None,
) -> int:
    """Valida e grava uma leitura meteorológica digitada pelo operador."""
    data = _data_obrigatoria(data_texto)
    if not formato.hora_valida(hora):
        raise ErroValidacao("Informe a hora no formato HH:MM.")

    umidade_valor = formato.para_numero(umidade, padrao=-1)
    if umidade.strip() and not 0 <= umidade_valor <= 100:
        raise ErroValidacao("A umidade relativa deve estar entre 0 e 100%.")

    vento_valor = formato.para_numero(vento, padrao=-1)
    if vento.strip() and vento_valor < 0:
        raise ErroValidacao("A velocidade do vento não pode ser negativa.")

    registro = RegistroClima(
        data=data,
        hora=hora.strip(),
        fonte=fonte or "",
        temperatura=formato.para_numero(temperatura) if temperatura.strip() else None,
        sensacao_termica=(
            formato.para_numero(sensacao_termica) if sensacao_termica.strip() else None
        ),
        umidade_relativa=umidade_valor if umidade.strip() else None,
        vento=vento_valor if vento.strip() else None,
        registrado_por=usuario_id,
    )
    try:
        return repositorio_clima.inserir(registro)
    except ValueError as erro:
        raise ErroValidacao(str(erro)) from erro
