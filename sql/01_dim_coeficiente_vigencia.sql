-- 01_dim_coeficiente_vigencia.sql
-- --------------------------------------------------------------------------
-- Constrói a dimensão de coeficientes da ANTT com INTERVALO DE VIGÊNCIA.
--
-- Problema que este passo resolve:
-- A ANTT publica resoluções que atualizam os coeficientes periodicamente.
-- Cada carga precisa ser avaliada pelo coeficiente vigente NA DATA em que
-- ocorreu, não pelo coeficiente atual. Comparar toda a base contra a tabela
-- mais recente produz piso errado e foi o que mascarou o problema no início.
--
-- A data de início da vigência vem em cada linha (dt_inicio_vigencia). A data
-- de fim é derivada: é o dia anterior ao início da PRÓXIMA resolução, para a
-- mesma combinação de tabela/tipo de carga/eixos. A vigência mais recente
-- fica em aberto (dt_fim = NULL).
-- --------------------------------------------------------------------------

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
    -- fim da vigência = dia anterior ao início da próxima resolução
    DATE(
        LEAD(dt_inicio_vigencia) OVER (
            PARTITION BY tabela, tipo_carga, eixos
            ORDER BY dt_inicio_vigencia
        ),
        '-1 day'
    ) AS dt_fim_vigencia
FROM stg_coeficientes_antt;

-- Observação para SQL Server (T-SQL):
--   dt_fim_vigencia = DATEADD(DAY, -1,
--       LEAD(dt_inicio_vigencia) OVER (
--           PARTITION BY tabela, tipo_carga, eixos
--           ORDER BY dt_inicio_vigencia))
