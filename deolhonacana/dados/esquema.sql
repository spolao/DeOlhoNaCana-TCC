-- Esquema do De Olho na Cana.
--
-- Substitui a tabela única BANCO_DE_OLHO_NA_CANA, que misturava identificação,
-- classificação e acompanhamento em 16 colunas de texto. Aqui o catálogo é
-- normalizado, as datas são gravadas em ISO-8601 (AAAA-MM-DD) para permitir
-- comparação e aritmética em SQL, e a integridade é garantida por chaves
-- estrangeiras e restrições CHECK.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- usuários --

CREATE TABLE IF NOT EXISTS usuarios (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    login            TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    nome             TEXT    NOT NULL,
    senha_hash       TEXT    NOT NULL,
    sal              TEXT    NOT NULL,
    perfil           TEXT    NOT NULL DEFAULT 'operador'
                             CHECK (perfil IN ('admin', 'operador')),
    primeiro_acesso  INTEGER NOT NULL DEFAULT 1 CHECK (primeiro_acesso IN (0, 1)),
    ativo            INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
    criado_em        TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- ---------------------------------------------------------------- catálogo --

CREATE TABLE IF NOT EXISTS categorias (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo  TEXT    NOT NULL UNIQUE,   -- "4"
    nome    TEXT    NOT NULL,          -- "ESTRADA"
    rotulo  TEXT    NOT NULL UNIQUE,   -- "4-ESTRADA", como aparece na tela
    ordem   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS servicos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id  INTEGER NOT NULL REFERENCES categorias(id) ON DELETE CASCADE,
    codigo        TEXT    NOT NULL,    -- "4.2"
    nome          TEXT    NOT NULL,    -- descrição do serviço
    rotulo        TEXT    NOT NULL,    -- como aparece na tela
    ordem         INTEGER NOT NULL,
    UNIQUE (categoria_id, codigo)
);

CREATE INDEX IF NOT EXISTS idx_servicos_categoria ON servicos (categoria_id);

-- ------------------------------------------------------- glebas e fazendas --
-- Substitui o arquivo Espelho_banco_Glebas.xlsx: o mesmo dado, agora dentro do
-- banco, sem depender de planilha externa nem da biblioteca pandas.

CREATE TABLE IF NOT EXISTS glebas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo         TEXT    NOT NULL UNIQUE,
    fazenda        TEXT    NOT NULL,
    municipio      TEXT,
    administrador  TEXT
);

-- ------------------------------------------------------------- ocorrências --

CREATE TABLE IF NOT EXISTS ocorrencias (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    data_abertura   TEXT    NOT NULL,          -- AAAA-MM-DD
    data_conclusao  TEXT,                      -- AAAA-MM-DD, nulo enquanto pendente
    gleba           TEXT,
    quadra          TEXT,
    fazenda         TEXT,
    municipio       TEXT,
    administrador   TEXT,
    servico_id      INTEGER REFERENCES servicos(id) ON DELETE SET NULL,
    observacao      TEXT    NOT NULL DEFAULT '',
    status          TEXT    NOT NULL DEFAULT 'Pendente'
                            CHECK (status IN ('Pendente', 'Finalizado')),
    responsavel     TEXT    NOT NULL DEFAULT '',
    registrado_por  INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    atualizado_em   TEXT,

    -- Coerência entre status e data de conclusão: um registro finalizado tem
    -- data de conclusão, um pendente não tem.
    CHECK (
        (status = 'Finalizado' AND data_conclusao IS NOT NULL)
        OR (status = 'Pendente' AND data_conclusao IS NULL)
    ),
    CHECK (data_conclusao IS NULL OR data_conclusao >= data_abertura)
);

CREATE INDEX IF NOT EXISTS idx_ocorrencias_status  ON ocorrencias (status);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_data    ON ocorrencias (data_abertura);
CREATE INDEX IF NOT EXISTS idx_ocorrencias_servico ON ocorrencias (servico_id);

CREATE TABLE IF NOT EXISTS anexos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ocorrencia_id  INTEGER NOT NULL REFERENCES ocorrencias(id) ON DELETE CASCADE,
    arquivo        TEXT    NOT NULL,   -- nome do arquivo dentro de dados/anexos
    criado_em      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_anexos_ocorrencia ON anexos (ocorrencia_id);

-- --------------------------------------------------------- combate a fogo --

CREATE TABLE IF NOT EXISTS queimas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    data            TEXT    NOT NULL,          -- AAAA-MM-DD
    fazenda         TEXT    NOT NULL DEFAULT '',
    gleba           TEXT,
    quadra          TEXT,
    viatura         TEXT,
    hora_inicio     TEXT,                      -- HH:MM
    hora_fim        TEXT,                      -- HH:MM
    colaboradores   INTEGER NOT NULL DEFAULT 0 CHECK (colaboradores >= 0),
    cana_ton        REAL    NOT NULL DEFAULT 0 CHECK (cana_ton  >= 0),
    cana_ha         REAL    NOT NULL DEFAULT 0 CHECK (cana_ha   >= 0),
    palha_ha        REAL    NOT NULL DEFAULT 0 CHECK (palha_ha  >= 0),
    pasto_ha        REAL    NOT NULL DEFAULT 0 CHECK (pasto_ha  >= 0),
    mata_ha         REAL    NOT NULL DEFAULT 0 CHECK (mata_ha   >= 0),
    app_ha          REAL    NOT NULL DEFAULT 0 CHECK (app_ha    >= 0),
    ja_colheu       TEXT    NOT NULL DEFAULT 'Não' CHECK (ja_colheu IN ('Sim', 'Não')),
    observacao      TEXT    NOT NULL DEFAULT '',
    registrado_por  INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em       TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_queimas_data ON queimas (data);

-- ------------------------------------------------------------------ clima --

CREATE TABLE IF NOT EXISTS clima (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    data              TEXT NOT NULL,           -- AAAA-MM-DD
    hora              TEXT NOT NULL,           -- HH:MM
    fonte             TEXT NOT NULL DEFAULT '',
    temperatura       REAL,
    sensacao_termica  REAL,
    umidade_relativa  REAL CHECK (umidade_relativa IS NULL
                                  OR umidade_relativa BETWEEN 0 AND 100),
    vento             REAL CHECK (vento IS NULL OR vento >= 0),
    registrado_por    INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    criado_em         TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (data, hora, fonte)
);

CREATE INDEX IF NOT EXISTS idx_clima_data ON clima (data);

-- ------------------------------------------------------------------ visão --
-- Centraliza a junção com o catálogo e o cálculo de dias pendentes. O código
-- antigo tentava subtrair uma data formatada por strftime de uma coluna de
-- texto, o que em SQLite é subtração entre strings e devolvia valor sem
-- sentido. Com datas em ISO, julianday() faz a conta corretamente.

CREATE VIEW IF NOT EXISTS vw_ocorrencias AS
SELECT
    o.id,
    o.data_abertura,
    o.data_conclusao,
    o.gleba,
    o.quadra,
    o.fazenda,
    o.municipio,
    o.administrador,
    o.observacao,
    o.status,
    o.responsavel,
    o.criado_em,
    c.rotulo AS categoria,
    c.codigo AS categoria_codigo,
    s.rotulo AS servico,
    s.codigo AS servico_codigo,
    u.nome   AS registrado_por_nome,
    CAST(
        julianday(COALESCE(o.data_conclusao, date('now', 'localtime')))
        - julianday(o.data_abertura)
        AS INTEGER
    ) AS dias_pendentes,
    (SELECT COUNT(*) FROM anexos a WHERE a.ocorrencia_id = o.id) AS qtd_anexos
FROM ocorrencias AS o
LEFT JOIN servicos   AS s ON s.id = o.servico_id
LEFT JOIN categorias AS c ON c.id = s.categoria_id
LEFT JOIN usuarios   AS u ON u.id = o.registrado_por;
