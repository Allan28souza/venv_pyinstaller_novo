# database.py
import os
import sys
import sqlite3

APP_NAME = "TesteImagensApp"
DB_FILENAME = "testes.db"
PASTA_IMAGENS = "imagens"
PASTA_RESULTADOS = "resultados"


def resource_path(relative_path):
    """Caminho absoluto para recursos empacotados pelo PyInstaller (read-only)."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_data_dir():
    """Pasta de dados persistentes (onde vamos gravar o DB e resultados)."""
    if sys.platform == "win32":
        base = os.getenv("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser(
            "~"), "Library", "Application Support")
    else:
        base = os.path.join(os.path.expanduser("~"), ".local", "share")
    data_dir = os.path.join(base, APP_NAME)
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_db_path():
    """Retorna caminho do banco persistente."""
    # Em tempo de desenvolvimento, se houver um testes.db no CWD, usa ele.
    # Em exe, usa data_dir.
    dev_db = os.path.join(os.path.abspath("."), DB_FILENAME)
    if os.path.exists(dev_db) and not getattr(sys, "frozen", False):
        return dev_db
    return os.path.join(get_data_dir(), DB_FILENAME)


def conectar():
    path = get_db_path()
    conn = sqlite3.connect(path)
    # habilitar foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


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
        teste_id INTEGER,
        caminho TEXT,
        resposta_correta TEXT CHECK(resposta_correta IN ('OK','NOK')),
        FOREIGN KEY (teste_id) REFERENCES testes(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()
