
import sqlite3
import json
from pathlib import Path

# Banco de dados criado na mesma pasta deste arquivo
DB_PATH = Path(__file__).with_name("chatbot.db")


def conectar():
    return sqlite3.connect(DB_PATH)


def criar_tabela():
    with conectar() as conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS conversas (
                id TEXT PRIMARY KEY,
                titulo TEXT NOT NULL,
                mensagens TEXT NOT NULL,
                criada_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def salvar_conversa(conversa):
    mensagens_json = json.dumps(
        conversa["mensagens"],
        ensure_ascii=False
    )

    with conectar() as conexao:
        conexao.execute("""
            INSERT INTO conversas (id, titulo, mensagens)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                titulo = excluded.titulo,
                mensagens = excluded.mensagens
        """, (
            conversa["id"],
            conversa["titulo"],
            mensagens_json
        ))


def carregar_conversas():
    with conectar() as conexao:
        linhas = conexao.execute("""
            SELECT id, titulo, mensagens
            FROM conversas
            ORDER BY criada_em DESC
        """).fetchall()

    conversas = []

    for identificador, titulo, mensagens in linhas:
        conversas.append({
            "id": identificador,
            "titulo": titulo,
            "mensagens": json.loads(mensagens)
        })

    return conversas


def excluir_conversa(identificador):
    with conectar() as conexao:
        conexao.execute(
            "DELETE FROM conversas WHERE id = ?",
            (identificador,)
        )


# Cria a tabela automaticamente
criar_tabela()
