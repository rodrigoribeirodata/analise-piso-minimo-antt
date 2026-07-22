"""
gerar_base_sintetica.py

Gera uma base FICTÍCIA de cargas para o repositório, reproduzindo a
ESTRUTURA e a DISTRIBUIÇÃO de uma base real de transportadora, sem conter
nenhum dado real de cliente, rota ou valor.

Motivo: a análise original foi conduzida sobre dados confidenciais de uma
operação real. Para publicar o método de forma reproduzível e versionável,
os dados de cargas são sintetizados. As tabelas de coeficiente da ANTT, ao
contrário, são públicas e reais (ver dados/antt/).

Saída: dados/sintetico/cargas.csv
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)  # reprodutibilidade

SAIDA = Path(__file__).resolve().parent.parent / "dados" / "sintetico" / "cargas.csv"

# Clientes fictícios. Um deles concentra volume, como no caso real, para que a
# análise de concentração tenha o que encontrar.
CLIENTES = (
    ["Cliente A"] * 55 +          # concentrador
    ["Cliente B"] * 15 +
    ["Cliente C"] * 12 +
    ["Cliente D"] * 10 +
    ["Cliente E"] * 8
)

# Rotas fictícias: (origem, destino, km aproximado).
ROTAS = [
    ("MS", "MG", 1029),
    ("SP", "BA", 1440),
    ("PR", "PE", 2650),
    ("GO", "SP", 926),
    ("MG", "RS", 1712),
    ("SP", "CE", 2810),
    ("RJ", "MG", 434),
    ("SC", "SP", 705),
]

EIXOS_POSSIVEIS = [5, 6, 7, 9]

# Vigências reais (para posicionar as datas; o cálculo do piso é feito no SQL).
DT_INICIO = date(2025, 8, 1)
DT_FIM = date(2026, 3, 31)


def data_aleatoria():
    dias = (DT_FIM - DT_INICIO).days
    return DT_INICIO + timedelta(days=random.randint(0, dias))


def gerar(n=900):
    linhas = []
    for i in range(1, n + 1):
        cliente = random.choice(CLIENTES)
        uf_orig, uf_dest, km_base = random.choice(ROTAS)
        km = km_base + random.randint(-30, 30)
        eixos = random.choice(EIXOS_POSSIVEIS)
        dt = data_aleatoria()

        # Frete praticado. O piso ANTT de Carga Geral fica, na faixa de eixos
        # usada, aproximadamente entre R$ 6,5 e R$ 8,7 por km (deslocamento) mais
        # a parcela fixa de carga/descarga. A maioria das cargas é precificada
        # ACIMA do piso; a exposição é concentrada no Cliente A, reproduzindo o
        # padrão real em que o problema não era geral, e sim de um cliente.
        # coef_deslocamento aproximado por eixo, só para calibrar o gerador
        coef_aprox = {5: 6.10, 6: 6.75, 7: 7.40, 9: 8.50}[eixos]
        if cliente == "Cliente A" and random.random() < 0.40:
            # subprecificado: abaixo do coeficiente de deslocamento
            base_km = coef_aprox * random.uniform(0.82, 0.97)
        else:
            # precificado acima do piso, com margem
            base_km = coef_aprox * random.uniform(1.05, 1.30)

        frete_sem_icms = round(km * base_km, 2)

        # ICMS: presente só em parte das rotas, como no caso real.
        tem_icms = random.random() < 0.5
        aliquota = random.choice([0.07, 0.12]) if tem_icms else 0.0
        icms = round(frete_sem_icms * aliquota, 2)
        frete_com_icms = round(frete_sem_icms + icms, 2)

        letra_cliente = cliente.split()[-1]  # "Cliente A" -> "A"
        id_carga = f"{letra_cliente}{uf_orig}{6000 + i}"

        linhas.append({
            "embarque": f"{6000 + i:06d}",
            "ID": id_carga,
            "dt_saida": dt.isoformat(),
            "uf_remet": uf_orig,
            "uf_dest": uf_dest,
            "cliente": cliente,
            "rota": f"{uf_orig} x {uf_dest}",
            "km": km,
            "qtd_eixos": eixos,
            "frete_sem_icms": frete_sem_icms,
            "icms": icms,
            "frete_com_icms": frete_com_icms,
        })
    return linhas


def main():
    linhas = gerar()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SAIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=linhas[0].keys(), delimiter=";")
        w.writeheader()
        w.writerows(linhas)
    print(f"{len(linhas)} cargas fictícias geradas em {SAIDA}")


if __name__ == "__main__":
    main()
