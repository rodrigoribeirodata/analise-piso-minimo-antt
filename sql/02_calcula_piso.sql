-- 02_calcula_piso.sql
-- --------------------------------------------------------------------------
-- Associa cada carga ao coeficiente ANTT vigente na sua data e calcula o
-- piso mínimo devido.
--
-- Fórmula oficial (Res. ANTT 5.867/2020, art. 5º, com coeficientes da Tabela A):
--   piso = distancia (km) * coef_deslocamento + coef_carga_descarga
--
-- Base de comparação: FRETE SEM ICMS. O piso ANTT remunera o valor pago ao
-- contratado; o ICMS, presente apenas em parte das rotas, é fator à parte na
-- configuração das tabelas de frete da empresa e não compõe a comparação.
--
-- Regra de eixos (art. 5º, §5º): se o nº de eixos da carga não existe na
-- tabela, usa-se a quantidade imediatamente inferior; se não houver inferior,
-- a imediatamente superior. Aqui a base opera com eixos já previstos (5,6,7,9),
-- mas a junção é feita pelo eixo exato e a regra fica documentada para extensão.
-- --------------------------------------------------------------------------

DROP TABLE IF EXISTS fato_piso;

CREATE TABLE fato_piso AS
SELECT
    c.embarque,
    c.ID,
    c.dt_saida,
    c.cliente,
    c.rota,
    c.km,
    c.qtd_eixos,
    c.frete_sem_icms,
    d.resolucao,
    d.coef_deslocamento,
    d.coef_carga_descarga,
    -- piso devido pela fórmula oficial
    ROUND(c.km * d.coef_deslocamento + d.coef_carga_descarga, 2) AS piso_antt,
    -- diferença: negativa = frete abaixo do piso (exposição)
    ROUND(c.frete_sem_icms - (c.km * d.coef_deslocamento + d.coef_carga_descarga), 2) AS diferenca,
    CASE
        WHEN c.frete_sem_icms < (c.km * d.coef_deslocamento + d.coef_carga_descarga)
        THEN 'ABAIXO' ELSE 'OK'
    END AS situacao
FROM cargas c
JOIN dim_coeficiente d
  ON d.tabela = 'A'
 AND d.tipo_carga = 'Carga Geral'
 AND d.eixos = c.qtd_eixos
 -- casa a carga com a vigência que cobre a data de saída
 AND c.dt_saida >= d.dt_inicio_vigencia
 AND (d.dt_fim_vigencia IS NULL OR c.dt_saida <= d.dt_fim_vigencia);
