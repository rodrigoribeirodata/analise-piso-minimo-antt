# Análise de aderência ao piso mínimo de frete (ANTT)

Identificação de exposição a autuações regulatórias cruzando as tabelas
públicas de piso mínimo da ANTT com a base de cargas de uma transportadora,
respeitando a vigência de cada resolução na data de cada operação.

---

## O problema

Uma transportadora rodoviária de cargas vinha recebendo autuações recorrentes
da ANTT por contratação de frete abaixo do piso mínimo estabelecido pela
Política Nacional de Pisos Mínimos do Transporte Rodoviário de Cargas
(Lei 13.703/2018). As autuações eram tratadas caso a caso, sem dimensionamento
da exposição total e sem clareza sobre onde ela se concentrava.

## Contexto

Transportadora rodoviária de cargas, operação nacional, carteira B2B. Base
transacional em SQL Server integrada ao ERP. Operação de carga lotação, tipo
Carga Geral, avaliada pela **Tabela A** da ANTT (contratação da composição
veicular).

## Nota sobre os dados

- **Tabelas de coeficiente da ANTT:** públicas e reais, extraídas das
  resoluções oficiais (ver `dados/antt/` e as fontes no fim deste documento).
- **Base de cargas:** sintética, gerada por `python/gerar_base_sintetica.py`,
  reproduzindo a estrutura e a distribuição de uma base real sem conter nenhum
  dado de cliente, rota ou valor verdadeiro.

O problema, o método, as decisões e o desfecho descritos aqui são de um caso
real conduzido em produção. Apenas os dados de cargas foram substituídos, por
confidencialidade.

## Perguntas da análise

1. Qual o piso devido em cada operação, considerando a tabela vigente **na data
   em que ela ocorreu**?
2. Onde a diferença entre praticado e devido se concentra — por cliente e por rota?
3. Qual o tamanho da exposição?
4. O desvio está no frete pago ao contratado?

## Método

A dificuldade central não é comparar dois valores. É determinar **qual tabela
valia em cada data**.

A ANTT atualiza os coeficientes periodicamente por resolução. Uma carga de
agosto/2025 precisa ser avaliada pela tabela vigente em agosto, não pela atual.
Comparar toda a base contra a tabela mais recente produz piso errado — e foi
justamente o que impediu que o problema fosse detectado antes.

A solução foi montar uma **dimensão de coeficientes com intervalo de vigência**
(`sql/01`), fechando o fim de cada vigência no dia anterior ao início da
resolução seguinte, via `LEAD`. Cada carga é então associada por data ao
coeficiente correto (`sql/02`) e o piso é calculado pela fórmula oficial:

```
piso = distância (km) × coeficiente de deslocamento + coeficiente de carga e descarga
```

**Base de comparação: frete sem ICMS.** O piso ANTT remunera o valor pago ao
contratado. O ICMS, presente apenas em parte das rotas, é fator à parte na
configuração das tabelas de frete da empresa e não compõe a comparação com o
piso.

**Regra de eixos não previstos** (Res. 5.867/2020, art. 5º, §5º): quando o
número de eixos não consta na tabela, aplica-se a quantidade imediatamente
inferior, ou a superior na ausência de inferior. A regra fica documentada no
`sql/02` para extensão da base.

## Modelagem

Modelo estrela simples. Fato na granularidade da **operação individual**, pois
é sobre ela que a autuação incide. Dimensão de coeficiente com vigência,
dimensões implícitas de cliente, rota e tempo.

## Base analítica

O resultado é uma base rastreável carga a carga (`fato_piso`), com data,
cliente, rota, km, eixos, frete praticado, resolução aplicada, piso devido,
diferença e situação (`ABAIXO`/`OK`). Qualquer linha pode ser auditada até o
coeficiente e a fórmula que a geraram — a mesma leitura granular de uma
planilha, gerada por SQL.

Sobre ela rodam as agregações de exposição por cliente e por rota (`sql/03`).

## Achados

Com a base sintética de exemplo, a análise reproduz o padrão do caso real:

- As cargas abaixo do piso **não estavam distribuídas** pela carteira.
- Um único cliente concentrava a quase totalidade da exposição em reais, muito
  acima da sua participação em volume.
- A concentração descartava falha geral de processo e apontava para
  **precificação contratual** de rotas específicas.

Esse recorte — por rota **dentro** de cada cliente — foi o que tornou o
problema visível. No agregado por cliente, ele se diluía.

## Recomendação e decisão

Foram apresentadas duas alternativas aos gestores comercial e de logística:
renegociar as tabelas das rotas expostas ou descontinuar as operações
inviáveis. A decisão coube à liderança, que optou por renegociação, com parte
das rotas reajustada e parte descontinuada.

## Resultado

As autuações cessaram após a implementação das medidas.

## O que eu faria diferente hoje

- **Monitoramento em vez de diagnóstico.** O cálculo do piso pode rodar na
  entrada da operação e alertar antes da contratação, eliminando a exposição em
  vez de mensurá-la depois.
- **Versionamento das tabelas desde o início.** Capturar cada resolução assim
  que publicada, em vez de reconstruir o histórico depois. O parser em
  `python/` é o primeiro passo nessa direção.

## Como reproduzir

```bash
# 1. gerar a base sintética de cargas
python python/gerar_base_sintetica.py

# 2. carregar os CSV e executar os scripts SQL na ordem 01 → 02 → 03
#    (ver instrucoes em sql/)
```

## Stack

Python (pandas) para ingestão das tabelas da ANTT e geração da base sintética ·
SQL para vigência, cálculo do piso e análise de exposição · camada de
apresentação em Excel/Power BI.

## Fontes oficiais (tabelas de coeficiente)

- Resolução ANTT nº 6.067, de 17/07/2025
- Resolução ANTT nº 6.076, de 19/01/2026

---

> Dados de cargas sintéticos, para fins de demonstração. Metodologia e
> resultado baseados em caso real, com dados originais preservados por
> confidencialidade.
