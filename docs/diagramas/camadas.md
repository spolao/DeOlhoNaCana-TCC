# Camadas e dependências

## Visão geral

A dependência aponta sempre para baixo. Nenhum módulo de uma camada inferior importa algo
de uma camada superior — é o que permite testar toda a regra de negócio sem instanciar o
Kivy.

```mermaid
flowchart TD
    subgraph apresentacao["telas/ — apresentação"]
        login[login]
        senha[alterar_senha]
        inicio[inicio]
        lanc[lancamento]
        cons[consulta]
        queima[queima]
        clima[clima]
        indic[indicadores]
        usu[usuarios]
        base[base.TelaBase]
    end

    app["app.py<br/>ScreenManager, diálogos,<br/>seletor de data e de arquivo"]

    subgraph servicos["servicos/ — regras de negócio"]
        autent[autenticacao]
        reg[registros]
        anex[anexos]
        ind[indicadores]
        pdf[relatorio_pdf]
        fmt[formato]
    end

    subgraph dados["dados/ — persistência"]
        conex[conexao]
        migr[migracoes]
        repoOc[repositorio_ocorrencias]
        repoUs[repositorio_usuarios]
        repoCa[repositorio_catalogo]
        repoQu[repositorio_queimas]
        repoCl[repositorio_clima]
    end

    subgraph dominio["dominio/ — vocabulário"]
        cat[catalogo]
        mod[modelos]
    end

    cfg["config.py<br/>caminhos portáveis"]
    seg["seguranca.py<br/>PBKDF2"]
    db[("SQLite<br/>deolhonacana.db")]

    apresentacao --> app
    apresentacao --> servicos
    app --> servicos
    servicos --> dados
    servicos --> dominio
    dados --> dominio
    dados --> conex
    conex --> db
    migr --> cat
    autent --> seg
    repoUs --> seg
    conex --> cfg
    anex --> cfg
    pdf --> cfg
    ind --> cfg
    app --> cfg
```

## Regra de dependência

| Camada | Pode importar | Não pode importar |
|---|---|---|
| `telas/` | `servicos/`, `config`, o próprio `app` | `dados/` diretamente |
| `servicos/` | `dados/`, `dominio/`, `config`, `seguranca` | `telas/`, `kivy` |
| `dados/` | `dominio/`, `config`, `seguranca` | `servicos/`, `telas/`, `kivy` |
| `dominio/` | nada do projeto | qualquer outra camada |

A única exceção deliberada é `telas/consulta.py`, que importa
`repositorio_ocorrencias` para ler a lista de ordenações disponíveis e para recarregar a
tabela — uma leitura sem regra de negócio associada.

## Dependências externas

```mermaid
flowchart LR
    proj["De Olho na Cana"]

    kivy["kivy 2.3.1<br/>laço gráfico e widgets"]
    kivymd["kivymd 1.2.0<br/>componentes Material"]
    mpl["matplotlib 3.9.2<br/>gráficos do painel"]
    rl["reportlab 4.2.5<br/>relatório em PDF"]
    pil["pillow 10.4.0<br/>geração das imagens"]
    std["biblioteca padrão<br/>sqlite3, hashlib, pathlib"]

    proj --> kivy
    proj --> kivymd
    proj --> mpl
    proj --> rl
    proj --> pil
    proj --> std

    kivymd --> kivy
    mpl --> pil
```

Cinco dependências, todas instaláveis offline a partir de um cache do pip. Não há cliente
HTTP, driver de navegador nem biblioteca de nuvem — coerente com o requisito de operação
sem rede.

O projeto anterior dependia ainda de `selenium`, `pandas` e `openpyxl`, além de um
`chromedriver.exe` de 19 MB. As três saíram: o Selenium com o dashboard remoto, o pandas e
o openpyxl quando as duas planilhas de apoio viraram tabelas do banco.
