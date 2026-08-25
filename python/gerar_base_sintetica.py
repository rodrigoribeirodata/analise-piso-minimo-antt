"""
Gera uma base fictícia de cargas para demonstrar a ferramenta.

A base contém um padrão de concentração de exposição em um dos clientes,
incluído apenas para ilustrar a análise por dimensão. Nomes, rotas, datas e
valores são sintéticos. O script usa apenas a biblioteca padrão.

Saída: dados/sintetico/cargas.csv
"""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEMENTE = 42
SAIDA = Path(__file__).resolve().parent.parent / "dados" / "sintetico" / "cargas.csv"

CLIENTES = (
    ["Cliente A"] * 55
    + ["Cliente B"] * 15
    + ["Cliente C"] * 12
    + ["Cliente D"] * 10
    + ["Cliente E"] * 8
)

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
DT_INICIO = date(2025, 8, 1)
DT_FIM = date(2026, 3, 31)


def data_aleatoria(rng: random.Random) -> date:
    dias = (DT_FIM - DT_INICIO).days
    return DT_INICIO + timedelta(days=rng.randint(0, dias))


def gerar(n: int = 900, semente: int = SEMENTE) -> list[dict[str, object]]:
    rng = random.Random(semente)
    linhas: list[dict[str, object]] = []

    for i in range(1, n + 1):
        cliente = rng.choice(CLIENTES)
        uf_orig, uf_dest, km_base = rng.choice(ROTAS)
        km = km_base + rng.randint(-30, 30)
        eixos = rng.choice(EIXOS_POSSIVEIS)
        dt = data_aleatoria(rng)

<<<<<<< HEAD
        # Valores aproximados usados somente para gerar a base de demonstração.
        # O Cliente A concentra a maior parte dos desvios (frequentes e mais
        # profundos); os demais clientes têm desvios ocasionais e mais rasos.
        # Isso produz uma concentração realista, em torno de 70% da exposição no
        # Cliente A, sem torná-la binária. O cálculo oficial do piso é feito
        # depois, com os coeficientes históricos reais.
        coef_aprox = {5: 6.10, 6: 6.75, 7: 7.40, 9: 8.50}[eixos]
        if cliente == "Cliente A":
            if rng.random() < 0.42:
                base_km = coef_aprox * rng.uniform(0.80, 0.95)   # abaixo, mais forte
            else:
                base_km = coef_aprox * rng.uniform(1.06, 1.30)
        else:
            if rng.random() < 0.08:
                base_km = coef_aprox * rng.uniform(0.94, 0.99)   # abaixo, ocasional e raso
            else:
                base_km = coef_aprox * rng.uniform(1.07, 1.32)
=======
        # Valores aproximados usados somente para gerar uma distribuição com
        # maioria de operações aderentes e concentração de desvios no Cliente A.
        # O cálculo oficial é feito depois, com os coeficientes históricos reais.
        coef_aprox = {5: 6.10, 6: 6.75, 7: 7.40, 9: 8.50}[eixos]
        if cliente == "Cliente A" and rng.random() < 0.40:
            base_km = coef_aprox * rng.uniform(0.82, 0.97)
        else:
            base_km = coef_aprox * rng.uniform(1.05, 1.30)
>>>>>>> 3c4b397e17f169ae1dd6653b507f51c9ca6d1744

        frete_sem_icms = round(km * base_km, 2)
        tem_icms = rng.random() < 0.5
        aliquota = rng.choice([0.07, 0.12]) if tem_icms else 0.0
        icms = round(frete_sem_icms * aliquota, 2)
        frete_com_icms = round(frete_sem_icms + icms, 2)

        letra_cliente = cliente.split()[-1]
        id_carga = f"{letra_cliente}{uf_orig}{6000 + i}"

        linhas.append(
            {
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
            }
        )

    return linhas


def main() -> None:
    linhas = gerar()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=linhas[0].keys(), delimiter=";")
        writer.writeheader()
        writer.writerows(linhas)
    print(f"{len(linhas)} cargas fictícias geradas em {SAIDA}")


if __name__ == "__main__":
<<<<<<< HEAD
    main()
=======
    main()
>>>>>>> 3c4b397e17f169ae1dd6653b507f51c9ca6d1744
