-- 03_analise_exposicao.sql
-- --------------------------------------------------------------------------
-- Responde as perguntas de negócio da análise a partir de fato_piso.
-- --------------------------------------------------------------------------

-- (1) Panorama geral: quantas cargas abaixo do piso e qual a exposição total.
SELECT
    COUNT(*)                                             AS total_cargas,
    SUM(CASE WHEN situacao = 'ABAIXO' THEN 1 ELSE 0 END) AS cargas_abaixo,
    ROUND(100.0 * SUM(CASE WHEN situacao = 'ABAIXO' THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                         AS pct_abaixo,
    ROUND(SUM(CASE WHEN situacao = 'ABAIXO' THEN diferenca ELSE 0 END), 2)
                                                         AS exposicao_total
FROM fato_piso;

-- (2) Concentração por cliente: onde está o problema.
SELECT
    cliente,
    COUNT(*)                                             AS cargas,
    SUM(CASE WHEN situacao = 'ABAIXO' THEN 1 ELSE 0 END) AS cargas_abaixo,
    ROUND(100.0 * SUM(CASE WHEN situacao = 'ABAIXO' THEN 1 ELSE 0 END) / COUNT(*), 1)
                                                         AS pct_abaixo,
    ROUND(SUM(CASE WHEN situacao = 'ABAIXO' THEN diferenca ELSE 0 END), 2)
                                                         AS exposicao
FROM fato_piso
GROUP BY cliente
ORDER BY exposicao;

-- (3) Concentração por rota dentro do cliente mais exposto.
SELECT
    cliente,
    rota,
    COUNT(*)                                             AS cargas,
    SUM(CASE WHEN situacao = 'ABAIXO' THEN 1 ELSE 0 END) AS cargas_abaixo,
    ROUND(SUM(CASE WHEN situacao = 'ABAIXO' THEN diferenca ELSE 0 END), 2)
                                                         AS exposicao
FROM fato_piso
GROUP BY cliente, rota
HAVING cargas_abaixo > 0
ORDER BY exposicao
LIMIT 10;
