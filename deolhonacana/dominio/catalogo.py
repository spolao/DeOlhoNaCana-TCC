"""Catálogo de categorias e serviços de ocorrência.

Estas listas são o vocabulário controlado usado pelos apontamentos de campo:
28 categorias e os serviços de cada uma. São a única fonte da verdade — o
banco é semeado a partir daqui na primeira execução, e a interface monta os
seus seletores a partir do banco.

Cada chave tem o formato ``"<número>-<NOME>"`` e cada item o formato
``"<número>.<subnúmero> - <descrição>"``.
"""

from __future__ import annotations

#: categoria -> lista de serviços, na ordem em que aparecem para o usuário.
CATALOGO: dict[str, list[str]] = {
    '1-ACESSOS': [
        '1.1 - Entrada do acesso irregular',
        '1.2 - Saída do acesso irregular',
    ],
    '2-CAMINHOS INTERNOS': [
        '2.1 - Erosão',
        '2.2 - Estrias',
        '2.3 - Buracos',
        '2.4 - Entulho',
    ],
    '3-ACEIRO': [
        '3.1 - Largura de aceiro inadequada',
        '3.2 - Presença de ervas daninhas',
        '3.3 - Erosão',
        '3.4 - Árvore caída',
        '3.5 - Saída do acesso irregular',
    ],
    '4-ESTRADA': [
        '4.1 - Buracos',
        "4.2 - Poças d'água",
        '4.3 - Falta de material',
        '4.4 - Material perfurocortante',
        '4.5 - Estrias',
        '4.6 - Estrada com trepidação',
        '4.7 - Bigodes assoreados',
        '4.8 - Passagem de tubos (Irrigação)',
        '4.9 - Poeira',
    ],
    '5-PONTE': [
        '5.1 - Passagem estreita',
        '5.2 - Perda de material',
        '5.3 - Ponte quebrada',
        '5.4 - Pregos expostos',
    ],
    '6-PONTO DE TRANSFERÊNCIA': [
        '6.1 - Declive',
        '6.2 - Dimensão de ponto fora do padrão',
        '6.3 - Ponto com acúmulo de água',
        '6.4 - Presença de materiais (entulho, terra, gesso, torta, calcário, etc.)',
        '6.5 - Declivioso',
        '6.6 - Estreito',
        '6.7 - Inexistente',
        '6.8 - Obstruído (calcário)',
        '6.9 - Obstruído (pedra)',
        '6.10 - Obstruído (torta)',
        '6.11 - Linha de Força próxima',
    ],
    '7-ALEIRAMENTO': [
        '7.1 - Aleiramento',
    ],
    '8-CERCA': [
        '8.1 - Aceiro de Cerca',
        '8.2 - Cerca Danificada',
        '8.3 - Cerca Entupida',
        '8.4 - Construção de Cerca',
        '8.5 - Desmanche de Cerca',
        '8.6 - Fazer Perímetro de Cerca',
        '8.7 - Manutenção de Cerca',
    ],
    '9-DANOS': [
        '9.1 - Sem enchimento de terra no pé do poste',
        '9.2 - Capivara',
        '9.3 - Equinos Bovinos',
        '9.4 - Queima de Cana',
        '9.5 - Queima de Palha',
        '9.6 - Vento',
    ],
    '10-DOENÇAS': [
        '10.1 - Carvão',
        '10.2 - Doenças Outras',
        '10.3 - Ferrugem',
    ],
    '11-FORMIGA': [
        '11.1 - Formiga APP',
        '11.2 - Formiga Cana Planta',
        '11.3 - Formiga Cana Soca',
        '11.4 - Formiga Divisa',
        '11.5 - Formiga Usina',
    ],
    '12-GEADA': [
        '12.1 - Geada Cana Planta',
        '12.2 - Geada Cana Soca',
    ],
    '13-GRANIZO': [
        '13.1 - Granizo Cana Planta',
        '13.2 - Granizo Cana Soca',
    ],
    '14-LIMPEZA': [
        '14.1 - Aceiro',
        '14.2 - Animais',
        '14.3 - Entulho',
        '14.4 - Obstrução',
        '14.5 - Pedra',
        '14.6 - Resíduo',
    ],
    '15-MANUTENÇÃO': [
        '15.1 - Ponte',
        '15.2 - Portão',
        '15.3 - Poste (Serv. Agric.)',
    ],
    '16-MEIO AMBIENTE (ANIMAIS SILVESTRES)': [
        '16.1 - Cobra',
        '16.2 - Lagarto - Teiú',
        '16.3 - Lobo-Guará',
        '16.4 - Macaco',
        '16.5 - Onça',
        '16.6 - Tamanduá',
        '16.7 - Tatu',
        '16.8 - Veado-Mateiro',
        '16.9 - Outro Animal',
    ],
    '17-QUEBRA LOMBO': [
        '17.1 - Quebra Lombo - Altura',
        '17.2 - Quebra Lombo - Auditoria',
    ],
    '18-PISOTEIO': [
        '18.1 - Pisoteio Cana Planta',
        '18.2 - Pisoteio Cana Soca',
    ],
    '19-PLANTAS DANINHAS': [
        '19.1 - Arbusto',
        '19.2 - Capim-Camalote',
        '19.3 - Capim-Marmelada',
        '19.4 - Capim-Braquiara',
        '19.5 - Capim-Massambara',
        '19.6 - Capim-Colchão',
        '19.7 - Capim-Colonião',
        '19.8 - Corda de Viola',
        '19.9 - Fitotoxicidade',
        '19.10 - Grama-Seda',
        '19.11 - Mamona',
        '19.12 - Mucuna',
        '19.13 - Tiririca',
        '19.14 - Vassoura',
        '19.15 - Outro (folha estreita)',
        '19.16 - Outro (folha larga)',
    ],
    '20-PODA': [
        '20.1 - APP',
        '20.2 - Carreira de Árvores',
        '20.3 - Cerca Viva',
    ],
    '22-SINALIZAÇÃO': [
        '22.1 - Outros',
        '22.2 - Pontes',
        '22.3 - Rodovias',
        '22.4 - Cacimba',
        '22.5 - Estradão',
        '22.6 - Gasoduto',
    ],
    '23-REBOLEIRA': [
        '23.1 - Reboleira',
    ],
    '24-REFORMA': [
        '24.1 - Mal desenvolvida/Baixa Produção',
        '24.2 - Faixa sem plantio',
        '24.3 - Declividade',
        '24.4 - Rua de Cana na Faixa de Linha de força',
    ],
    '25-REPLANTIO': [
        '25.1 - APP',
        '25.2 - Cana',
        '25.3 - Cerca Viva',
    ],
    '26-ROUBO': [
        '26.1 - Cana',
        '26.2 - Patrimônio',
    ],
    '27-CONSERVAÇÃO': [
        '27.1 - Cacimba danificada',
        '27.2 - Curva de nivel - Cheia de Água',
        '27.3 - Curva de nivel - Alta',
        '27.4 - Laje de pedra',
        '27.5 - Limpeza de Cacimba',
        '27.6 - Poça',
    ],
    '28-OUTRO': [
        '28.1 - Cobrição Ruim',
        '28.2 - Plantio em área total sem estaquiar',
        '28.3 - Sobra de cana',
        '28.4 - Falha na Cobrição',
        '28.5 - Falha aplicação de torta',
        '28.6 - Excesso de herbicida',
        '28.7 - Construção de Valeta',
        '28.8 - Espaçamento Irregular',
        '28.9 - Canal Entupido',
        '28.10 - Outros',
    ],
}


def categorias() -> list[str]:
    """Categorias na ordem de exibição."""
    return list(CATALOGO)


def servicos_de(categoria: str) -> list[str]:
    """Serviços de uma categoria; lista vazia se a categoria não existir."""
    return list(CATALOGO.get(categoria, []))


def separar_codigo(rotulo: str) -> tuple[str, str]:
    """Quebra ``"4-ESTRADA"`` em ``("4", "ESTRADA")``.

    Também atende serviços: ``"4.2 - Poças d'água"`` vira
    ``("4.2", "Poças d'água")``. Rótulo sem separador devolve nome cheio e
    código vazio.
    """
    for separador in (" - ", "-"):
        codigo, achou, nome = rotulo.partition(separador)
        if achou and codigo.replace(".", "").isdigit():
            return codigo.strip(), nome.strip()
    return "", rotulo.strip()


def total_servicos() -> int:
    """Quantidade de serviços em todas as categorias."""
    return sum(len(itens) for itens in CATALOGO.values())
