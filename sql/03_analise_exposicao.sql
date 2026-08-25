-- 03_analise_exposicao.sql | SQLite
-- Cria visões reutilizáveis para panorama, cliente e rota.

DROP VIEW IF EXISTS vw_resumo_geral;
CREATE VIEW vw_resumo_geral AS
SELECT
    COUNT(*) AS total_cargas,
    SUM(CASE WHEN situacao = 'ABAIXO' THEN 1 ELSE 0 END) AS cargas_abaixo,
    ROUND(
        100.0 * SUM(CASE WHEN situacao = 'ABAIXO' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    ) AS pct_abaixo,
    ROUND(SUM(exposicao), 2) AS exposicao_total
FROM fato_piso;

DROP VIEW IF EXISTS vw_exposicao_cliente;
CREATE VIEW vw_exposicao_cliente AS
WITH agregado AS (
    SELECT
        cliente,
        COUNT(*) AS cargas,
        SUM(CASE WHEN situacao = 'ABAIXO' THEN 1 ELSE 0 END) AS cargas_abaixo,
        ROUND(
            100.0 * SUM(CASE WHEN situacao = 'ABAIXO' THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0),
            1
        ) AS pct_abaixo,
        ROUND(SUM(exposicao), 2) AS exposicao
    FROM fato_piso
    GROUP BY cliente
), totais AS (
    SELECT SUM(cargas) AS total_cargas, SUM(exposicao) AS total_exposicao
    FROM agregado
)
SELECT
    a.*,
    ROUND(100.0 * a.cargas / NULLIF(t.total_cargas, 0), 1) AS pct_volume,
    ROUND(100.0 * a.exposicao / NULLIF(t.total_exposicao, 0), 1) AS pct_exposicao
FROM agregado a
CROSS JOIN totais t;

DROP VIEW IF EXISTS vw_exposicao_rota;
CREATE VIEW vw_exposicao_rota AS
SELECT
    cliente,
    rota,
    COUNT(*) AS cargas,
    SUM(CASE WHEN situacao = 'ABAIXO' THEN 1 ELSE 0 END) AS cargas_abaixo,
    ROUND(
        100.0 * SUM(CASE WHEN situacao = 'ABAIXO' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0),
        1
    ) AS pct_abaixo,
    ROUND(SUM(exposicao), 2) AS exposicao
FROM fato_piso
GROUP BY cliente, rota
HAVING SUM(exposicao) > 0;
