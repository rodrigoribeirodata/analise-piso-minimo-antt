-- 02_calcula_piso.sql | SQLite
-- Associa cada carga ao coeficiente vigente na data e calcula o piso devido.
-- Escopo demonstrado: Tabela A, Carga Geral, eixos 5, 6, 7 e 9.

DROP TABLE IF EXISTS fato_piso;

CREATE TABLE fato_piso AS
WITH calculo AS (
    SELECT
        c.embarque,
        c.ID,
        c.dt_saida,
        c.uf_remet,
        c.uf_dest,
        c.cliente,
        c.rota,
        c.km,
        c.qtd_eixos,
        c.frete_sem_icms,
        c.icms,
        c.frete_com_icms,
        d.resolucao,
        d.dt_inicio_vigencia,
        d.dt_fim_vigencia,
        d.coef_deslocamento,
        d.coef_carga_descarga,
        ROUND(c.km * d.coef_deslocamento + d.coef_carga_descarga, 2) AS piso_antt
    FROM cargas c
    JOIN dim_coeficiente d
      ON d.tabela = 'A'
     AND d.tipo_carga = 'Carga Geral'
     AND d.eixos = c.qtd_eixos
     AND c.dt_saida >= d.dt_inicio_vigencia
     AND (d.dt_fim_vigencia IS NULL OR c.dt_saida <= d.dt_fim_vigencia)
)
SELECT
    *,
    ROUND(frete_sem_icms - piso_antt, 2) AS diferenca,
    CASE
        WHEN frete_sem_icms < piso_antt
        THEN ROUND(piso_antt - frete_sem_icms, 2)
        ELSE 0
    END AS exposicao,
    CASE WHEN frete_sem_icms < piso_antt THEN 'ABAIXO' ELSE 'OK' END AS situacao
FROM calculo;

CREATE INDEX idx_fato_piso_cliente_rota
    ON fato_piso(cliente, rota, situacao);
