"""
gerar_dados_referencia.py
--------------------------
Gera um dataset sintético de jogadores/partidas para o projeto.

Este script existe para você já ter dados reais para testar o SQL, o Python
de análise e o dashboard AGORA, sem precisar instalar o .NET.

Quando você instalar o .NET, o programa C# (csharp/GameDataGenerator/Program.cs)
faz exatamente a mesma coisa, na mesma lógica, e você pode usá-lo para gerar
novos lotes de dados sempre que quiser.
"""
import csv
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

PERSONAGENS = [
    "Fantasma", "Trovão", "Sombra", "Aço", "Fênix", "Corvo",
    "Lâmina", "Guardião", "Cinzas", "Nômade"
]

RANKS_ORDEM = ["Bronze", "Prata", "Ouro", "Platina", "Diamante", "Mestre"]

NOMES = [
    "Yuri", "Kaique", "Bianca", "Rafa", "Larissa", "Diego", "Camila", "Vitor",
    "Marina", "Thiago", "Alice", "Bruno", "Sofia", "Gustavo", "Isabela",
    "Lucas", "Manuela", "Pedro", "Julia", "Enzo", "Helena", "Davi", "Laura",
    "Miguel", "Valentina", "Arthur", "Heloisa", "Gabriel", "Livia", "Matheus"
]


def gerar_jogadores(qtd=30):
    jogadores = []
    for i, nome in enumerate(NOMES[:qtd], start=1):
        # jogadores com mais "skill" tendem a ranks mais altos (não 100% linear,
        # de propósito, pra análise ter algo real pra descobrir)
        skill = random.gauss(0.5, 0.2)
        skill = min(max(skill, 0), 1)
        rank_idx = min(int(skill * len(RANKS_ORDEM)), len(RANKS_ORDEM) - 1)
        jogadores.append({
            "id": i,
            "nome": nome,
            "rank": RANKS_ORDEM[rank_idx],
            "skill": skill,  # não vai pro banco, só usamos aqui pra gerar partidas coerentes
        })
    return jogadores


def gerar_partidas(jogadores, personagens):
    partidas = []
    partida_id = 1
    hoje = datetime.now()

    for jogador in jogadores:
        n_partidas = random.randint(25, 160)
        # personagem "principal" do jogador (joga mais com ele, mas varia)
        principal = random.choice(personagens)

        for _ in range(n_partidas):
            personagem_id = principal["id"] if random.random() < 0.55 else random.choice(personagens)["id"]

            # chance de vitória correlacionada com skill do jogador (com ruído)
            chance_vitoria = 0.5 + (jogador["skill"] - 0.5) * 0.6
            chance_vitoria = min(max(chance_vitoria, 0.1), 0.9)
            vitoria = 1 if random.random() < chance_vitoria else 0

            # kills/deaths correlacionados com skill, com ruído generoso
            kills = max(0, round(random.gauss(4 + jogador["skill"] * 10, 3)))
            deaths = max(1, round(random.gauss(6 - jogador["skill"] * 3, 2)))
            assists = max(0, round(random.gauss(3, 2)))

            duracao_min = random.randint(12, 45)
            dias_atras = random.randint(0, 180)
            data = hoje - timedelta(days=dias_atras, minutes=random.randint(0, 1440))

            partidas.append({
                "id": partida_id,
                "jogador_id": jogador["id"],
                "personagem_id": personagem_id,
                "data": data.strftime("%Y-%m-%d %H:%M:%S"),
                "duracao_min": duracao_min,
                "vitoria": vitoria,
                "kills": kills,
                "deaths": deaths,
                "assists": assists,
            })
            partida_id += 1

    return partidas


def salvar_csv(caminho, linhas, campos):
    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)


def salvar_sqlite(jogadores, personagens, partidas):
    db_path = DATA_DIR / "game_data.db"
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.executescript(open(BASE_DIR / "sql" / "schema.sql", encoding="utf-8").read())

    cur.executemany(
        "INSERT INTO Jogadores (id, nome, rank) VALUES (:id, :nome, :rank)",
        jogadores,
    )
    cur.executemany(
        "INSERT INTO Personagens (id, nome) VALUES (:id, :nome)",
        personagens,
    )
    cur.executemany(
        """INSERT INTO Partidas (id, jogador_id, personagem_id, data, duracao_min, vitoria, kills, deaths, assists)
           VALUES (:id, :jogador_id, :personagem_id, :data, :duracao_min, :vitoria, :kills, :deaths, :assists)""",
        partidas,
    )

    conn.commit()
    conn.close()
    print(f"Banco SQLite gerado em: {db_path}")


def main():
    personagens = [{"id": i, "nome": nome} for i, nome in enumerate(PERSONAGENS, start=1)]
    jogadores = gerar_jogadores(30)
    partidas = gerar_partidas(jogadores, personagens)

    jogadores_csv = [{"id": j["id"], "nome": j["nome"], "rank": j["rank"]} for j in jogadores]

    salvar_csv(DATA_DIR / "jogadores.csv", jogadores_csv, ["id", "nome", "rank"])
    salvar_csv(DATA_DIR / "personagens.csv", personagens, ["id", "nome"])
    salvar_csv(
        DATA_DIR / "partidas.csv",
        partidas,
        ["id", "jogador_id", "personagem_id", "data", "duracao_min", "vitoria", "kills", "deaths", "assists"],
    )

    salvar_sqlite(jogadores_csv, personagens, partidas)

    print(f"{len(jogadores)} jogadores, {len(personagens)} personagens, {len(partidas)} partidas geradas.")
    print(f"Arquivos salvos em: {DATA_DIR}")


if __name__ == "__main__":
    main()
