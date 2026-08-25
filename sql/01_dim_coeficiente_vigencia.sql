-- 01_dim_coeficiente_vigencia.sql | SQLite
-- Constrói a dimensão histórica de coeficientes da ANTT.

DROP TABLE IF EXISTS dim_coeficiente;

CREATE TABLE dim_coeficiente AS
SELECT
    resolucao,
    tabela,
    tipo_carga,
    eixos,
    coef_deslocamento,
    coef_carga_descarga,
    dt_inicio_vigencia,
    DATE(
        LEAD(dt_inicio_vigencia) OVER (
            PARTITION BY tabela, tipo_carga, eixos
            ORDER BY dt_inicio_vigencia
        ),
        '-1 day'
    ) AS dt_fim_vigencia
FROM stg_coeficientes_antt;

CREATE INDEX idx_dim_coeficiente_vigencia
    ON dim_coeficiente(tabela, tipo_carga, eixos, dt_inicio_vigencia, dt_fim_vigencia);
