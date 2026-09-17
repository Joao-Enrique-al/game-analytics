-- ============================================================
-- schema.sql
-- Banco de dados do projeto "Análise de Dados de Jogos"
-- Compatível com SQLite (e facilmente adaptável para SQL Server / MySQL)
-- ============================================================

DROP TABLE IF EXISTS Partidas;
DROP TABLE IF EXISTS Personagens;
DROP TABLE IF EXISTS Jogadores;

-- Tabela de jogadores
CREATE TABLE Jogadores (
    id      INTEGER PRIMARY KEY,
    nome    TEXT NOT NULL,
    rank    TEXT NOT NULL CHECK (rank IN ('Bronze','Prata','Ouro','Platina','Diamante','Mestre'))
);

-- Tabela de personagens jogáveis
CREATE TABLE Personagens (
    id      INTEGER PRIMARY KEY,
    nome    TEXT NOT NULL UNIQUE
);

-- Tabela de partidas (uma linha = uma partida jogada por um jogador com um personagem)
CREATE TABLE Partidas (
    id              INTEGER PRIMARY KEY,
    jogador_id      INTEGER NOT NULL REFERENCES Jogadores(id),
    personagem_id   INTEGER NOT NULL REFERENCES Personagens(id),
    data            TEXT NOT NULL,       -- formato ISO: YYYY-MM-DD HH:MM:SS
    duracao_min     INTEGER NOT NULL,    -- duração da partida em minutos
    vitoria         INTEGER NOT NULL CHECK (vitoria IN (0,1)),
    kills           INTEGER NOT NULL,
    deaths          INTEGER NOT NULL,
    assists         INTEGER NOT NULL
);

CREATE INDEX idx_partidas_jogador    ON Partidas(jogador_id);
CREATE INDEX idx_partidas_personagem ON Partidas(personagem_id);

-- ============================================================
-- VIEW: resumo por jogador — já no formato que você pediu:
-- Jogador | Horas jogadas | Vitórias | Derrotas | K/D | Rank
-- ============================================================
DROP VIEW IF EXISTS ResumoJogadores;
CREATE VIEW ResumoJogadores AS
SELECT
    j.nome                                                   AS Jogador,
    ROUND(SUM(p.duracao_min) / 60.0, 1)                      AS HorasJogadas,
    SUM(p.vitoria)                                           AS Vitorias,
    SUM(CASE WHEN p.vitoria = 0 THEN 1 ELSE 0 END)           AS Derrotas,
    ROUND(CAST(SUM(p.kills) AS FLOAT) / MAX(SUM(p.deaths), 1), 2) AS KD,
    j.rank                                                   AS Rank
FROM Jogadores j
JOIN Partidas p ON p.jogador_id = j.id
GROUP BY j.id, j.nome, j.rank
ORDER BY KD DESC;

-- ============================================================
-- Pergunta 1: Horas jogadas influenciam desempenho (win rate)?
-- ============================================================
DROP VIEW IF EXISTS HorasVsDesempenho;
CREATE VIEW HorasVsDesempenho AS
SELECT
    j.nome                                                       AS Jogador,
    ROUND(SUM(p.duracao_min) / 60.0, 1)                          AS HorasJogadas,
    ROUND(100.0 * SUM(p.vitoria) / COUNT(*), 1)                  AS WinRatePercentual,
    ROUND(CAST(SUM(p.kills) AS FLOAT) / MAX(SUM(p.deaths), 1), 2) AS KD
FROM Jogadores j
JOIN Partidas p ON p.jogador_id = j.id
GROUP BY j.id, j.nome
ORDER BY HorasJogadas DESC;

-- ============================================================
-- Pergunta 2: Qual personagem tem maior taxa de vitória?
-- ============================================================
DROP VIEW IF EXISTS WinRatePorPersonagem;
CREATE VIEW WinRatePorPersonagem AS
SELECT
    pe.nome                                        AS Personagem,
    COUNT(*)                                       AS TotalPartidas,
    SUM(p.vitoria)                                 AS Vitorias,
    ROUND(100.0 * SUM(p.vitoria) / COUNT(*), 1)    AS WinRatePercentual
FROM Personagens pe
JOIN Partidas p ON p.personagem_id = pe.id
GROUP BY pe.id, pe.nome
ORDER BY WinRatePercentual DESC;

-- ============================================================
-- Pergunta 3: Qual rank possui o maior K/D médio?
-- ============================================================
DROP VIEW IF EXISTS KDPorRank;
CREATE VIEW KDPorRank AS
SELECT
    j.rank                                                        AS Rank,
    COUNT(DISTINCT j.id)                                          AS TotalJogadores,
    ROUND(CAST(SUM(p.kills) AS FLOAT) / MAX(SUM(p.deaths), 1), 2) AS KDMedio
FROM Jogadores j
JOIN Partidas p ON p.jogador_id = j.id
GROUP BY j.rank
ORDER BY KDMedio DESC;
