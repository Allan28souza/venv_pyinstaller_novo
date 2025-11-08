import sqlite3
import os
import sys
import tempfile

# Caminho do banco de dados (pasta persistente)


def get_db_path():
    if getattr(sys, 'frozen', False):  # executável (PyInstaller)
        base_dir = os.path.join(os.environ.get(
            "APPDATA", os.path.expanduser("~")), "TesteImagensApp")
    else:
        base_dir = os.path.abspath(".")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "testes.db")


# Função para conectar ao banco
def conectar():
    return sqlite3.connect(get_db_path())


# Criação das tabelas
def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS testes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL,
        descricao TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS imagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teste_id INTEGER NOT NULL,
        nome_arquivo TEXT NOT NULL,
        imagem BLOB NOT NULL,
        resposta_correta TEXT CHECK(resposta_correta IN ('OK', 'NOK')),
        FOREIGN KEY (teste_id) REFERENCES testes(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()


# Adiciona imagem ao banco
def adicionar_imagem(teste_id, caminho, resposta_correta):
    with open(caminho, "rb") as f:
        imagem_blob = f.read()
    nome_arquivo = os.path.basename(caminho)

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO imagens (teste_id, nome_arquivo, resposta_correta, imagem)
        VALUES (?, ?, ?, ?)
    """, (teste_id, nome_arquivo, resposta_correta, imagem_blob))
    conn.commit()
    conn.close()


# Lista as imagens de um teste
def listar_imagens(teste_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nome_arquivo, resposta_correta FROM imagens WHERE teste_id=?
    """, (teste_id,))
    imagens = cursor.fetchall()
    conn.close()
    return imagens


# Extrai imagem temporariamente (para exibir no teste)
def extrair_imagem_temp(imagem_id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nome_arquivo, imagem FROM imagens WHERE id=?", (imagem_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    nome_arquivo, imagem_blob = row
    temp_dir = tempfile.mkdtemp()
    caminho_temp = os.path.join(temp_dir, nome_arquivo)
    with open(caminho_temp, "wb") as f:
        f.write(imagem_blob)
    return caminho_temp


# Função para retornar caminho compatível com executável
def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
