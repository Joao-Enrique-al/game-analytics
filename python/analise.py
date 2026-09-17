"""
analise.py
----------
Lê o banco SQLite gerado (data/game_data.db), faz limpeza básica e
responde às 3 perguntas do projeto usando pandas:

1) Quantas horas de jogo influenciam o desempenho?
2) Qual personagem tem maior taxa de vitória?
3) Qual rank possui maior K/D?

Gera gráficos em charts/ e imprime um resumo no terminal.

Como rodar:
    pip install pandas matplotlib
    python analise.py
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # gera imagens sem precisar de tela
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "game_data.db"
CHARTS_DIR = BASE_DIR / "charts"
CHARTS_DIR.mkdir(exist_ok=True)

# Paleta "pixel art" pra manter consistência com o dashboard
COR_PRIMARIA = "#7c3aed"
COR_SECUNDARIA = "#22d3ee"
COR_FUNDO = "#1a1a2e"
COR_TEXTO = "#e8e8f0"

plt.rcParams.update({
    "figure.facecolor": COR_FUNDO,
    "axes.facecolor": COR_FUNDO,
    "axes.edgecolor": COR_TEXTO,
    "axes.labelcolor": COR_TEXTO,
    "text.color": COR_TEXTO,
    "xtick.color": COR_TEXTO,
    "ytick.color": COR_TEXTO,
    "figure.figsize": (9, 5.5),
})


def carregar_dados():
    conn = sqlite3.connect(DB_PATH)
    jogadores = pd.read_sql("SELECT * FROM Jogadores", conn)
    personagens = pd.read_sql("SELECT * FROM Personagens", conn)
    partidas = pd.read_sql("SELECT * FROM Partidas", conn, parse_dates=["data"])
    conn.close()
    return jogadores, personagens, partidas


def limpar_dados(partidas: pd.DataFrame) -> pd.DataFrame:
    antes = len(partidas)
    partidas = partidas.dropna()
    partidas = partidas[(partidas["duracao_min"] > 0) & (partidas["deaths"] >= 0)]
    partidas = partidas.drop_duplicates(subset="id")
    depois = len(partidas)
    if antes != depois:
        print(f"Limpeza: removidas {antes - depois} linhas inválidas/duplicadas.")
    return partidas


def resumo_por_jogador(jogadores, partidas):
    g = partidas.groupby("jogador_id").agg(
        horas_jogadas=("duracao_min", lambda x: round(x.sum() / 60, 1)),
        vitorias=("vitoria", "sum"),
        partidas=("vitoria", "count"),
        kills=("kills", "sum"),
        deaths=("deaths", "sum"),
    ).reset_index()
    g["derrotas"] = g["partidas"] - g["vitorias"]
    g["win_rate"] = round(100 * g["vitorias"] / g["partidas"], 1)
    g["kd"] = round(g["kills"] / g["deaths"].clip(lower=1), 2)
    g = g.merge(jogadores[["id", "nome", "rank"]], left_on="jogador_id", right_on="id")
    return g[["nome", "horas_jogadas", "vitorias", "derrotas", "kd", "win_rate", "rank"]] \
        .rename(columns={"nome": "Jogador", "horas_jogadas": "HorasJogadas", "vitorias": "Vitorias",
                          "derrotas": "Derrotas", "kd": "KD", "win_rate": "WinRate", "rank": "Rank"})


def pergunta_1_horas_vs_desempenho(resumo: pd.DataFrame):
    correlacao_winrate = resumo["HorasJogadas"].corr(resumo["WinRate"])
    correlacao_kd = resumo["HorasJogadas"].corr(resumo["KD"])

    print("\n=== Pergunta 1: Horas jogadas influenciam o desempenho? ===")
    print(f"Correlação Horas x Win Rate: {correlacao_winrate:.2f}")
    print(f"Correlação Horas x K/D:      {correlacao_kd:.2f}")
    if abs(correlacao_winrate) < 0.2 and abs(correlacao_kd) < 0.2:
        print("Interpretação: correlação fraca — nesse dataset, jogar mais horas")
        print("não é, sozinho, um bom previsor de desempenho.")
    else:
        sinal = "positiva" if correlacao_winrate > 0 else "negativa"
        print(f"Interpretação: correlação {sinal} — vale investigar mais a fundo.")

    fig, ax = plt.subplots()
    ax.scatter(resumo["HorasJogadas"], resumo["WinRate"], color=COR_SECUNDARIA, edgecolor=COR_PRIMARIA, s=70)
    ax.set_xlabel("Horas jogadas")
    ax.set_ylabel("Win Rate (%)")
    ax.set_title("Horas jogadas x Taxa de vitória")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "01_horas_vs_winrate.png", dpi=130)
    plt.close(fig)

    return correlacao_winrate, correlacao_kd


def pergunta_2_personagem_maior_winrate(partidas: pd.DataFrame, personagens: pd.DataFrame):
    g = partidas.groupby("personagem_id").agg(
        partidas=("vitoria", "count"),
        vitorias=("vitoria", "sum"),
    ).reset_index()
    g["win_rate"] = round(100 * g["vitorias"] / g["partidas"], 1)
    g = g.merge(personagens, left_on="personagem_id", right_on="id").rename(columns={"nome": "Personagem"})
    g = g.sort_values("win_rate", ascending=False)

    print("\n=== Pergunta 2: Qual personagem tem maior taxa de vitória? ===")
    print(g[["Personagem", "partidas", "win_rate"]].to_string(index=False))

    fig, ax = plt.subplots()
    ax.bar(g["Personagem"], g["win_rate"], color=COR_PRIMARIA, edgecolor=COR_SECUNDARIA)
    ax.set_ylabel("Win Rate (%)")
    ax.set_title("Taxa de vitória por personagem")
    plt.xticks(rotation=35, ha="right")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "02_winrate_por_personagem.png", dpi=130)
    plt.close(fig)

    return g


def pergunta_3_rank_maior_kd(resumo: pd.DataFrame):
    g = resumo.groupby("Rank").agg(
        jogadores=("Jogador", "count"),
        kd_medio=("KD", "mean"),
    ).reset_index()
    g["kd_medio"] = round(g["kd_medio"], 2)
    ordem_ranks = ["Bronze", "Prata", "Ouro", "Platina", "Diamante", "Mestre"]
    g["Rank"] = pd.Categorical(g["Rank"], categories=ordem_ranks, ordered=True)
    g = g.sort_values("kd_medio", ascending=False)

    print("\n=== Pergunta 3: Qual rank possui maior K/D? ===")
    print(g.to_string(index=False))

    fig, ax = plt.subplots()
    g_ordenado_por_rank = g.sort_values("Rank")
    ax.bar(g_ordenado_por_rank["Rank"].astype(str), g_ordenado_por_rank["kd_medio"],
           color=COR_SECUNDARIA, edgecolor=COR_PRIMARIA)
    ax.set_ylabel("K/D médio")
    ax.set_title("K/D médio por rank")
    fig.tight_layout()
    fig.savefig(CHARTS_DIR / "03_kd_por_rank.png", dpi=130)
    plt.close(fig)

    return g


def exportar_resumo(resumo: pd.DataFrame):
    caminho = BASE_DIR / "data" / "resumo_jogadores.csv"
    resumo.sort_values("KD", ascending=False).to_csv(caminho, index=False)
    print(f"\nTabela-resumo (Jogador | Horas | Vitórias | Derrotas | K/D | Rank) salva em:\n{caminho}")


def main():
    jogadores, personagens, partidas = carregar_dados()
    partidas = limpar_dados(partidas)

    resumo = resumo_por_jogador(jogadores, partidas)
    print("=== Amostra da tabela-resumo ===")
    print(resumo.head(10).to_string(index=False))

    pergunta_1_horas_vs_desempenho(resumo)
    pergunta_2_personagem_maior_winrate(partidas, personagens)
    pergunta_3_rank_maior_kd(resumo)
    exportar_resumo(resumo)

    print(f"\nGráficos salvos em: {CHARTS_DIR}")


if __name__ == "__main__":
    main()
