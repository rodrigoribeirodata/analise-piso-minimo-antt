"""Executa o case ponta a ponta em SQLite usando apenas a biblioteca padrão."""

from __future__ import annotations

import csv
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "resultados" / "analise_antt.sqlite"
CARGAS_CSV = ROOT / "dados" / "sintetico" / "cargas.csv"
COEF_CSV = ROOT / "dados" / "antt" / "coeficientes_antt.csv"
SQL_DIR = ROOT / "sql"
RESULTADOS_DIR = ROOT / "resultados"
IMAGENS_DIR = ROOT / "imagens"


def gerar_base_sintetica() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "python" / "gerar_base_sintetica.py")],
        check=True,
    )


def ler_csv(caminho: Path) -> list[dict[str, str]]:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    with caminho.open("r", encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo, delimiter=";"))


def carregar_tabelas(conn: sqlite3.Connection) -> None:
    coeficientes = ler_csv(COEF_CSV)
    cargas = ler_csv(CARGAS_CSV)

    conn.executescript(
        """
        DROP TABLE IF EXISTS stg_coeficientes_antt;
        CREATE TABLE stg_coeficientes_antt (
            resolucao TEXT NOT NULL,
            tabela TEXT NOT NULL,
            tipo_carga TEXT NOT NULL,
            eixos INTEGER NOT NULL,
            coef_deslocamento REAL NOT NULL,
            coef_carga_descarga REAL NOT NULL,
            dt_inicio_vigencia TEXT NOT NULL
        );

        DROP TABLE IF EXISTS cargas;
        CREATE TABLE cargas (
            embarque TEXT NOT NULL,
            ID TEXT NOT NULL,
            dt_saida TEXT NOT NULL,
            uf_remet TEXT NOT NULL,
            uf_dest TEXT NOT NULL,
            cliente TEXT NOT NULL,
            rota TEXT NOT NULL,
            km INTEGER NOT NULL,
            qtd_eixos INTEGER NOT NULL,
            frete_sem_icms REAL NOT NULL,
            icms REAL NOT NULL,
            frete_com_icms REAL NOT NULL
        );
        """
    )

    conn.executemany(
        """
        INSERT INTO stg_coeficientes_antt VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["resolucao"],
                row["tabela"],
                row["tipo_carga"],
                int(row["eixos"]),
                float(row["coef_deslocamento"]),
                float(row["coef_carga_descarga"]),
                row["dt_inicio_vigencia"],
            )
            for row in coeficientes
        ],
    )

    conn.executemany(
        """
        INSERT INTO cargas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row["embarque"],
                row["ID"],
                row["dt_saida"],
                row["uf_remet"],
                row["uf_dest"],
                row["cliente"],
                row["rota"],
                int(row["km"]),
                int(row["qtd_eixos"]),
                float(row["frete_sem_icms"]),
                float(row["icms"]),
                float(row["frete_com_icms"]),
            )
            for row in cargas
        ],
    )
    conn.commit()


def executar_sql(conn: sqlite3.Connection) -> None:
    for nome in (
        "01_dim_coeficiente_vigencia.sql",
        "02_calcula_piso.sql",
        "03_analise_exposicao.sql",
    ):
        caminho = SQL_DIR / nome
        conn.executescript(caminho.read_text(encoding="utf-8"))
    conn.commit()


def consultar(conn: sqlite3.Connection, sql: str) -> tuple[list[str], list[tuple]]:
    cursor = conn.execute(sql)
    colunas = [descricao[0] for descricao in cursor.description]
    return colunas, cursor.fetchall()


def exportar_csv(caminho: Path, colunas: Sequence[str], linhas: Iterable[Sequence]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8", newline="") as arquivo:
        writer = csv.writer(arquivo, delimiter=";")
        writer.writerow(colunas)
        writer.writerows(linhas)


def moeda_br(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def gerar_svg_clientes(linhas: list[tuple]) -> None:
    # Espera: cliente, cargas, cargas_abaixo, pct_abaixo, exposicao, pct_volume, pct_exposicao
    dados = [(str(row[0]), float(row[4])) for row in linhas]
    maior = max((valor for _, valor in dados), default=1.0)

    largura = 960
    margem_esq = 150
    margem_dir = 180
    topo = 70
    altura_linha = 64
    altura = topo + len(dados) * altura_linha + 70
    area_barra = largura - margem_esq - margem_dir

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#202124}.titulo{font-size:24px;font-weight:700}.rotulo{font-size:16px}.valor{font-size:15px;font-weight:700}.nota{font-size:13px;fill:#5f6368}</style>',
        '<text x="32" y="38" class="titulo">Exposição estimada por cliente</text>',
        '<text x="32" y="60" class="nota">Base sintética — valores em reais</text>',
    ]

    for indice, (cliente, valor) in enumerate(dados):
        y = topo + indice * altura_linha
        comprimento = 0 if maior == 0 else area_barra * valor / maior
        partes.extend(
            [
                f'<text x="32" y="{y + 27}" class="rotulo">{cliente}</text>',
                f'<rect x="{margem_esq}" y="{y + 8}" width="{comprimento:.1f}" height="28" rx="4" fill="#4f6d7a"/>',
                f'<text x="{margem_esq + comprimento + 12:.1f}" y="{y + 28}" class="valor">{moeda_br(valor)}</text>',
            ]
        )

    partes.append('</svg>')
    IMAGENS_DIR.mkdir(parents=True, exist_ok=True)
    (IMAGENS_DIR / "exposicao_por_cliente.svg").write_text("\n".join(partes), encoding="utf-8")


def validar(conn: sqlite3.Connection) -> None:
    total_cargas = conn.execute("SELECT COUNT(*) FROM cargas").fetchone()[0]
    total_fato = conn.execute("SELECT COUNT(*) FROM fato_piso").fetchone()[0]
    sem_coeficiente = conn.execute(
        """
        SELECT COUNT(*)
        FROM cargas c
        LEFT JOIN fato_piso f ON f.ID = c.ID
        WHERE f.ID IS NULL
        """
    ).fetchone()[0]

    if total_cargas != 900:
        raise RuntimeError(f"Esperadas 900 cargas, encontradas {total_cargas}.")
    if total_fato != total_cargas or sem_coeficiente:
        raise RuntimeError(
            "Falha de cobertura temporal: há cargas sem coeficiente vigente associado."
        )


def main() -> None:
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    gerar_base_sintetica()

    if DB_PATH.exists():
        DB_PATH.unlink()

    with sqlite3.connect(DB_PATH) as conn:
        carregar_tabelas(conn)
        executar_sql(conn)
        validar(conn)

        consultas = {
            "resumo_geral.csv": "SELECT * FROM vw_resumo_geral",
            "resultado_por_cliente.csv": (
                "SELECT * FROM vw_exposicao_cliente ORDER BY exposicao DESC"
            ),
            "resultado_por_rota.csv": (
                "SELECT * FROM vw_exposicao_rota ORDER BY exposicao DESC LIMIT 10"
            ),
            "amostra_fato_piso.csv": (
                "SELECT * FROM fato_piso ORDER BY dt_saida, ID LIMIT 25"
            ),
        }

        linhas_cliente: list[tuple] = []
        for arquivo, consulta_sql in consultas.items():
            colunas, linhas = consultar(conn, consulta_sql)
            exportar_csv(RESULTADOS_DIR / arquivo, colunas, linhas)
            if arquivo == "resultado_por_cliente.csv":
                linhas_cliente = linhas

        gerar_svg_clientes(linhas_cliente)

        _, resumo = consultar(conn, "SELECT * FROM vw_resumo_geral")
        total, abaixo, pct, exposicao = resumo[0]
        print("Pipeline concluído com sucesso.")
        print(f"Cargas analisadas: {total}")
        print(f"Cargas abaixo do piso: {abaixo} ({pct:.1f}%)")
        print(f"Exposição estimada: {moeda_br(float(exposicao))}")
        print(f"Resultados: {RESULTADOS_DIR}")


if __name__ == "__main__":
    main()
