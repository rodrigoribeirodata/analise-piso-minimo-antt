# Scripts SQL

Ordem de execução:

1. **01_dim_coeficiente_vigencia.sql** — monta a dimensão de coeficientes da
   ANTT com intervalo de vigência, a partir da staging `stg_coeficientes_antt`
   (carregada do CSV em `dados/antt/`). Usa `LEAD` para fechar cada vigência no
   dia anterior ao início da norma seguinte.
2. **02_calcula_piso.sql** — associa cada carga ao coeficiente vigente na sua
   data de saída e calcula o piso, a diferença e a situação (`fato_piso`).
3. **03_analise_exposicao.sql** — consultas de exposição: panorama geral,
   concentração por cliente e por rota.

Os scripts são executados automaticamente por `python/executar_pipeline.py`,
que cria o banco SQLite, carrega os dados e roda os três na ordem acima.

Tabelas de entrada esperadas:

### `stg_coeficientes_antt`

| Coluna | Tipo sugerido |
|---|---|
| resolucao | texto |
| tabela | texto |
| tipo_carga | texto |
| eixos | inteiro |
| coef_deslocamento | decimal(12,4) |
| coef_carga_descarga | decimal(12,2) |
| dt_inicio_vigencia | data |

### `cargas`

| Coluna | Tipo sugerido |
|---|---|
| embarque | texto |
| ID | texto |
| dt_saida | data |
| uf_remet / uf_dest | texto |
| cliente / rota | texto |
| km | inteiro |
| qtd_eixos | inteiro |
| frete_sem_icms / icms / frete_com_icms | decimal(14,2) |

O pipeline cria e carrega essas tabelas automaticamente a partir dos CSV.
