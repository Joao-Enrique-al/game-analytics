// ============================================================
// GameDataGenerator
// Gera dados sintéticos de jogadores, personagens e partidas,
// exporta para CSV e grava num banco SQLite (data/game_data.db).
//
// Como rodar:
//   cd csharp/GameDataGenerator
//   dotnet run
//
// O programa cria (ou recria) os arquivos em ../../data/
// ============================================================

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Microsoft.Data.Sqlite;

namespace GameDataGenerator;

public record Jogador(int Id, string Nome, string Rank, double Skill);
public record Personagem(int Id, string Nome);
public record Partida(
    int Id, int JogadorId, int PersonagemId, DateTime Data,
    int DuracaoMin, int Vitoria, int Kills, int Deaths, int Assists);

public static class Program
{
    private static readonly Random Rng = new(42); // seed fixa -> resultados reprodutíveis

    private static readonly string[] Personagens =
    {
        "Fantasma", "Trovão", "Sombra", "Aço", "Fênix", "Corvo",
        "Lâmina", "Guardião", "Cinzas", "Nômade"
    };

    private static readonly string[] RanksOrdem =
        { "Bronze", "Prata", "Ouro", "Platina", "Diamante", "Mestre" };

    private static readonly string[] Nomes =
    {
        "Yuri", "Kaique", "Bianca", "Rafa", "Larissa", "Diego", "Camila", "Vitor",
        "Marina", "Thiago", "Alice", "Bruno", "Sofia", "Gustavo", "Isabela",
        "Lucas", "Manuela", "Pedro", "Julia", "Enzo", "Helena", "Davi", "Laura",
        "Miguel", "Valentina", "Arthur", "Heloisa", "Gabriel", "Livia", "Matheus"
    };

    public static void Main(string[] args)
    {
        int qtdJogadores = args.Length > 0 && int.TryParse(args[0], out var q) ? q : 30;

        var baseDir = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", "..", "data"));
        Directory.CreateDirectory(baseDir);

        var personagens = Personagens.Select((nome, i) => new Personagem(i + 1, nome)).ToList();
        var jogadores = GerarJogadores(qtdJogadores);
        var partidas = GerarPartidas(jogadores, personagens);

        SalvarCsvJogadores(Path.Combine(baseDir, "jogadores.csv"), jogadores);
        SalvarCsvPersonagens(Path.Combine(baseDir, "personagens.csv"), personagens);
        SalvarCsvPartidas(Path.Combine(baseDir, "partidas.csv"), partidas);

        var schemaPath = Path.GetFullPath(Path.Combine(baseDir, "..", "sql", "schema.sql"));
        SalvarSqlite(Path.Combine(baseDir, "game_data.db"), schemaPath, jogadores, personagens, partidas);

        Console.WriteLine($"Gerados: {jogadores.Count} jogadores, {personagens.Count} personagens, {partidas.Count} partidas.");
        Console.WriteLine($"Arquivos salvos em: {baseDir}");
    }

    private static List<Jogador> GerarJogadores(int qtd)
    {
        var jogadores = new List<Jogador>();
        var nomesEscolhidos = Nomes.Take(qtd).ToList();

        for (int i = 0; i < nomesEscolhidos.Count; i++)
        {
            double skill = Math.Clamp(AmostraGaussiana(0.5, 0.2), 0, 1);
            int rankIdx = Math.Min((int)(skill * RanksOrdem.Length), RanksOrdem.Length - 1);
            jogadores.Add(new Jogador(i + 1, nomesEscolhidos[i], RanksOrdem[rankIdx], skill));
        }

        return jogadores;
    }

    private static List<Partida> GerarPartidas(List<Jogador> jogadores, List<Personagem> personagens)
    {
        var partidas = new List<Partida>();
        int partidaId = 1;
        var hoje = DateTime.Now;

        foreach (var jogador in jogadores)
        {
            int nPartidas = Rng.Next(25, 161);
            var principal = personagens[Rng.Next(personagens.Count)];

            for (int k = 0; k < nPartidas; k++)
            {
                var personagem = Rng.NextDouble() < 0.55
                    ? principal
                    : personagens[Rng.Next(personagens.Count)];

                double chanceVitoria = Math.Clamp(0.5 + (jogador.Skill - 0.5) * 0.6, 0.1, 0.9);
                int vitoria = Rng.NextDouble() < chanceVitoria ? 1 : 0;

                int kills = Math.Max(0, (int)Math.Round(AmostraGaussiana(4 + jogador.Skill * 10, 3)));
                int deaths = Math.Max(1, (int)Math.Round(AmostraGaussiana(6 - jogador.Skill * 3, 2)));
                int assists = Math.Max(0, (int)Math.Round(AmostraGaussiana(3, 2)));

                int duracaoMin = Rng.Next(12, 46);
                var data = hoje.AddDays(-Rng.Next(0, 181)).AddMinutes(-Rng.Next(0, 1441));

                partidas.Add(new Partida(partidaId++, jogador.Id, personagem.Id, data,
                    duracaoMin, vitoria, kills, deaths, assists));
            }
        }

        return partidas;
    }

    // Gera um número com distribuição normal (Box-Muller), já que o Random do .NET só dá uniforme
    private static double AmostraGaussiana(double media, double desvioPadrao)
    {
        double u1 = 1.0 - Rng.NextDouble();
        double u2 = Rng.NextDouble();
        double z = Math.Sqrt(-2.0 * Math.Log(u1)) * Math.Sin(2.0 * Math.PI * u2);
        return media + desvioPadrao * z;
    }

    private static void SalvarCsvJogadores(string caminho, List<Jogador> jogadores)
    {
        using var w = new StreamWriter(caminho);
        w.WriteLine("id,nome,rank");
        foreach (var j in jogadores)
            w.WriteLine($"{j.Id},{j.Nome},{j.Rank}");
    }

    private static void SalvarCsvPersonagens(string caminho, List<Personagem> personagens)
    {
        using var w = new StreamWriter(caminho);
        w.WriteLine("id,nome");
        foreach (var p in personagens)
            w.WriteLine($"{p.Id},{p.Nome}");
    }

    private static void SalvarCsvPartidas(string caminho, List<Partida> partidas)
    {
        using var w = new StreamWriter(caminho);
        w.WriteLine("id,jogador_id,personagem_id,data,duracao_min,vitoria,kills,deaths,assists");
        foreach (var p in partidas)
            w.WriteLine($"{p.Id},{p.JogadorId},{p.PersonagemId},{p.Data:yyyy-MM-dd HH:mm:ss},{p.DuracaoMin},{p.Vitoria},{p.Kills},{p.Deaths},{p.Assists}");
    }

    private static void SalvarSqlite(string dbPath, string schemaPath,
        List<Jogador> jogadores, List<Personagem> personagens, List<Partida> partidas)
    {
        if (File.Exists(dbPath)) File.Delete(dbPath);

        using var conn = new SqliteConnection($"Data Source={dbPath}");
        conn.Open();

        var schemaSql = File.ReadAllText(schemaPath);
        using (var cmd = conn.CreateCommand())
        {
            cmd.CommandText = schemaSql;
            cmd.ExecuteNonQuery();
        }

        using var transaction = conn.BeginTransaction();

        foreach (var j in jogadores)
        {
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "INSERT INTO Jogadores (id, nome, rank) VALUES ($id, $nome, $rank)";
            cmd.Parameters.AddWithValue("$id", j.Id);
            cmd.Parameters.AddWithValue("$nome", j.Nome);
            cmd.Parameters.AddWithValue("$rank", j.Rank);
            cmd.ExecuteNonQuery();
        }

        foreach (var p in personagens)
        {
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "INSERT INTO Personagens (id, nome) VALUES ($id, $nome)";
            cmd.Parameters.AddWithValue("$id", p.Id);
            cmd.Parameters.AddWithValue("$nome", p.Nome);
            cmd.ExecuteNonQuery();
        }

        foreach (var p in partidas)
        {
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"INSERT INTO Partidas
                (id, jogador_id, personagem_id, data, duracao_min, vitoria, kills, deaths, assists)
                VALUES ($id, $jogadorId, $personagemId, $data, $duracao, $vitoria, $kills, $deaths, $assists)";
            cmd.Parameters.AddWithValue("$id", p.Id);
            cmd.Parameters.AddWithValue("$jogadorId", p.JogadorId);
            cmd.Parameters.AddWithValue("$personagemId", p.PersonagemId);
            cmd.Parameters.AddWithValue("$data", p.Data.ToString("yyyy-MM-dd HH:mm:ss"));
            cmd.Parameters.AddWithValue("$duracao", p.DuracaoMin);
            cmd.Parameters.AddWithValue("$vitoria", p.Vitoria);
            cmd.Parameters.AddWithValue("$kills", p.Kills);
            cmd.Parameters.AddWithValue("$deaths", p.Deaths);
            cmd.Parameters.AddWithValue("$assists", p.Assists);
            cmd.ExecuteNonQuery();
        }

        transaction.Commit();
    }
}
