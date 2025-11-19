import sqlite3
import os
import sys
import tempfile
from datetime import datetime
import shutil

# ============================================================
# DEFINIR CAMINHO DO BANCO (SUPORTA EXECUTÁVEL .EXE)
# ============================================================


def get_db_path():
    """Retorna caminho persistente para o banco (pasta APPDATA se for exe)."""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")),
            "TesteImagensApp"
        )
    else:
        base_dir = os.path.abspath(".")

    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "testes.db")


DB_PATH = get_db_path()

# ============================================================
# CONEXÃO
# ============================================================


def conectar():
    return sqlite3.connect(DB_PATH)

# ============================================================
# CRIAR TABELAS + MIGRAÇÕES RR
# ============================================================


def criar_tabelas():
    conn = conectar()
    c = conn.cursor()

    # TESTES
    c.execute("""
    CREATE TABLE IF NOT EXISTS testes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL,
        descricao TEXT
    )""")

    # IMAGENS
    c.execute("""
    CREATE TABLE IF NOT EXISTS imagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teste_id INTEGER NOT NULL,
        nome_arquivo TEXT NOT NULL,
        imagem BLOB NOT NULL,
        resposta_correta TEXT CHECK(resposta_correta IN ('OK','NOK')),
        FOREIGN KEY(teste_id) REFERENCES testes(id) ON DELETE CASCADE
    )""")

    # OPERADORES
    c.execute("""
    CREATE TABLE IF NOT EXISTS operadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        matricula TEXT UNIQUE NOT NULL,
        turno TEXT
    )""")

    # AVALIADORES
    c.execute("""
    CREATE TABLE IF NOT EXISTS avaliadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL
    )""")

    # TURNOS
    c.execute("""
    CREATE TABLE IF NOT EXISTS turnos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_turno TEXT UNIQUE NOT NULL
    )""")

    # RESULTADOS
    c.execute("""
    CREATE TABLE IF NOT EXISTS resultados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operador_id INTEGER,
        teste_id INTEGER,
        avaliador TEXT,
        acertos INTEGER,
        total INTEGER,
        porcentagem REAL,
        data_hora TEXT,
        tempo_total INTEGER,
        tempo_medio REAL,
        repeticao INTEGER,
        FOREIGN KEY(operador_id) REFERENCES operadores(id),
        FOREIGN KEY(teste_id) REFERENCES testes(id)
    )""")

    # RESPOSTAS
    c.execute("""
    CREATE TABLE IF NOT EXISTS respostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resultado_id INTEGER,
        imagem_id INTEGER,
        nome_arquivo TEXT,
        resposta_usuario TEXT,
        resposta_correta TEXT,
        tempo INTEGER,
        repeticao INTEGER,
        FOREIGN KEY(resultado_id) REFERENCES resultados(id)
    )""")

    # -------------------------------
    # MIGRAÇÕES
    # -------------------------------

    # resultados.repeticao
    c.execute("PRAGMA table_info(resultados)")
    col_res = [row[1] for row in c.fetchall()]
    if "repeticao" not in col_res:
        c.execute("ALTER TABLE resultados ADD COLUMN repeticao INTEGER DEFAULT 1")

    # respostas.repeticao / respostas.imagem_id
    c.execute("PRAGMA table_info(respostas)")
    col_resp = [row[1] for row in c.fetchall()]

    if "repeticao" not in col_resp:
        c.execute("ALTER TABLE respostas ADD COLUMN repeticao INTEGER DEFAULT 1")

    if "imagem_id" not in col_resp:
        c.execute("ALTER TABLE respostas ADD COLUMN imagem_id INTEGER")

    # INSERIR TURNOS PADRÃO
    for t in ("1° Turno", "2° Turno", "3° Turno"):
        c.execute("INSERT OR IGNORE INTO turnos (nome_turno) VALUES (?)", (t,))

    conn.commit()
    conn.close()

# ============================================================
# IMAGENS
# ============================================================


def adicionar_imagem(teste_id, caminho, resposta_correta):
    with open(caminho, "rb") as f:
        blob = f.read()
    nome = os.path.basename(caminho)

    conn = conectar()
    c = conn.cursor()
    c.execute("""
        INSERT INTO imagens (teste_id, nome_arquivo, resposta_correta, imagem)
        VALUES (?,?,?,?)
    """, (teste_id, nome, resposta_correta, blob))
    conn.commit()
    conn.close()


def listar_imagens(teste_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        SELECT id, nome_arquivo, resposta_correta
        FROM imagens
        WHERE teste_id=?
    """, (teste_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def extrair_imagem_temp(imagem_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT nome_arquivo, imagem FROM imagens WHERE id=?", (imagem_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return None

    nome, blob = row
    temp_dir = tempfile.mkdtemp(prefix="img_")
    path = os.path.join(temp_dir, nome)

    with open(path, "wb") as f:
        f.write(blob)

    return path

# ============================================================
# OPERADORES
# ============================================================


def garantir_operador(nome, matricula, turno):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id FROM operadores WHERE matricula=?", (matricula,))
    r = c.fetchone()

    if r:
        op_id = r[0]
        c.execute("UPDATE operadores SET nome=?, turno=? WHERE id=?",
                  (nome, turno, op_id))
    else:
        c.execute("""
            INSERT INTO operadores (nome, matricula, turno)
            VALUES (?,?,?)
        """, (nome, matricula, turno))
        op_id = c.lastrowid

    conn.commit()
    conn.close()
    return op_id


def listar_operadores():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id, nome, matricula, turno FROM operadores ORDER BY nome")
    rows = c.fetchall()
    conn.close()
    return rows


def obter_dados_operador(operador_id):
    conn = conectar()
    c = conn.cursor()
    c.execute("""
        SELECT nome, matricula, turno
        FROM operadores
        WHERE id=?
    """, (operador_id,))
    row = c.fetchone()
    conn.close()
    return row if row else ("", "", "")

# ============================================================
# AVALIADORES E TURNOS
# ============================================================


def garantir_avaliador(nome):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id FROM avaliadores WHERE nome=?", (nome,))
    r = c.fetchone()

    if r:
        aid = r[0]
    else:
        c.execute("INSERT INTO avaliadores (nome) VALUES (?)", (nome,))
        aid = c.lastrowid

    conn.commit()
    conn.close()
    return aid


def listar_avaliadores():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT nome FROM avaliadores ORDER BY nome")
    rows = [x[0] for x in c.fetchall()]
    conn.close()
    return rows


def listar_turnos():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT nome_turno FROM turnos ORDER BY id")
    rows = [x[0] for x in c.fetchall()]
    conn.close()
    return rows

# ============================================================
# SALVAR RESULTADO (ATUALIZADO)
# ============================================================


def salvar_resultado(operador_id, teste_id, avaliador,
                     acertos, total, porcentagem,
                     tempo_total, tempo_medio, respostas_list,
                     repeticao):

    conn = conectar()
    c = conn.cursor()

    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
        INSERT INTO resultados
        (operador_id, teste_id, avaliador, acertos,
         total, porcentagem, data_hora, tempo_total,
         tempo_medio, repeticao)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (operador_id, teste_id, avaliador, acertos,
          total, porcentagem, data_hora, tempo_total, tempo_medio, repeticao))

    resultado_id = c.lastrowid

    # respostas_list agora é: (imagem_id, nome, resp_user, resp_correta, tempo)
    for imagem_id, nome, resp_user, resp_correta, tempo in respostas_list:
        c.execute("""
            INSERT INTO respostas
            (resultado_id, imagem_id, nome_arquivo,
             resposta_usuario, resposta_correta, tempo, repeticao)
            VALUES (?,?,?,?,?,?,?)
        """, (resultado_id, imagem_id, nome, resp_user,
              resp_correta, tempo, repeticao))

    conn.commit()
    conn.close()
    return resultado_id

# ============================================================
# LISTAR RESULTADOS
# ============================================================


def listar_resultados(filters=None):
    filters = filters or {}
    conn = conectar()
    c = conn.cursor()

    query = """
        SELECT r.id, r.operador_id,
               o.nome, o.matricula,
               r.teste_id, t.nome,
               r.avaliador,
               r.acertos, r.total, r.porcentagem,
               r.data_hora, r.tempo_total, r.tempo_medio, r.repeticao
        FROM resultados r
        LEFT JOIN operadores o ON o.id=r.operador_id
        LEFT JOIN testes t ON t.id=r.teste_id
        WHERE 1=1
    """

    params = []

    if filters.get("teste_id"):
        query += " AND r.teste_id=?"
        params.append(filters["teste_id"])

    if filters.get("operador_id"):
        query += " AND r.operador_id=?"
        params.append(filters["operador_id"])

    if filters.get("avaliador"):
        query += " AND r.avaliador=?"
        params.append(filters["avaliador"])

    if filters.get("turno"):
        query += " AND o.turno=?"
        params.append(filters["turno"])

    if filters.get("repeticao"):
        query += " AND r.repeticao=?"
        params.append(filters["repeticao"])

    if filters.get("data_inicio"):
        query += " AND r.data_hora>=?"
        params.append(filters["data_inicio"])

    if filters.get("data_fim"):
        query += " AND r.data_hora<=?"
        params.append(filters["data_fim"])

    c.execute(query, tuple(params))
    rows = c.fetchall()
    conn.close()
    return rows

# ============================================================
# EXPORTAÇÃO / IMPORTAÇÃO
# ============================================================


def exportar_banco(destino_path):
    conn = conectar()
    conn.close()
    shutil.copy2(DB_PATH, destino_path)
    return destino_path


def importar_banco(arquivo_path, substituir=True):
    if not os.path.exists(arquivo_path):
        raise FileNotFoundError("Arquivo de banco não encontrado.")

    # validar estrutura
    check = sqlite3.connect(arquivo_path)
    c = check.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in c.fetchall()}
    check.close()

    needed = {"testes", "imagens", "operadores", "avaliadores",
              "turnos", "resultados", "respostas"}

    if not needed.issubset(tables):
        raise RuntimeError(
            "O banco importado não possui as tabelas necessárias.")

    if substituir:
        shutil.copy2(arquivo_path, DB_PATH)
        return True

    return importar_banco_mesclar(arquivo_path)

# ============================================================
# MESCLAGEM DE BANCOS
# ============================================================


def importar_banco_mesclar(arquivo_import, ignorar_duplicados=True):
    if not os.path.exists(arquivo_import):
        raise FileNotFoundError("Banco a importar não encontrado.")

    conn_atual = conectar()
    cur_atual = conn_atual.cursor()

    conn_imp = sqlite3.connect(arquivo_import)
    cur_imp = conn_imp.cursor()

    # OPERADORES
    cur_imp.execute("SELECT nome, matricula, turno FROM operadores")
    for nome, mat, turno in cur_imp.fetchall():
        if ignorar_duplicados:
            cur_atual.execute(
                "SELECT id FROM operadores WHERE matricula=?", (mat,))
            if cur_atual.fetchone():
                continue

        cur_atual.execute(
            "INSERT INTO operadores (nome, matricula, turno) VALUES (?,?,?)",
            (nome, mat, turno)
        )

    # AVALIADORES
    cur_imp.execute("SELECT nome FROM avaliadores")
    for (nome,) in cur_imp.fetchall():
        if ignorar_duplicados:
            cur_atual.execute(
                "SELECT nome FROM avaliadores WHERE nome=?", (nome,))
            if cur_atual.fetchone():
                continue

        cur_atual.execute("INSERT INTO avaliadores (nome) VALUES (?)", (nome,))

    # TESTES
    cur_imp.execute("SELECT nome, descricao FROM testes")
    for nome, desc in cur_imp.fetchall():
        if ignorar_duplicados:
            cur_atual.execute("SELECT id FROM testes WHERE nome=?", (nome,))
            if cur_atual.fetchone():
                continue

        cur_atual.execute("""
            INSERT INTO testes (nome, descricao) VALUES (?,?)
        """, (nome, desc))

    # RESULTADOS
    cur_imp.execute("""
        SELECT operador_id, teste_id, avaliador,
               acertos, total, porcentagem,
               data_hora, tempo_total, tempo_medio, repeticao
    """)
    for row in cur_imp.fetchall():
        cur_atual.execute("""
            INSERT INTO resultados
            (operador_id, teste_id, avaliador, acertos,
             total, porcentagem, data_hora, tempo_total, tempo_medio, repeticao)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, row)

    # IMAGENS
    cur_imp.execute("""
        SELECT teste_id, nome_arquivo, resposta_correta, imagem
        FROM imagens
    """)
    for teste_id, nome_arquivo, resposta, blob in cur_imp.fetchall():
        if ignorar_duplicados:
            cur_atual.execute("""
                SELECT id FROM imagens WHERE teste_id=? AND nome_arquivo=?
            """, (teste_id, nome_arquivo))
            if cur_atual.fetchone():
                continue

        cur_atual.execute("""
            INSERT INTO imagens (teste_id, nome_arquivo, resposta_correta, imagem)
            VALUES (?,?,?,?)
        """, (teste_id, nome_arquivo, resposta, blob))

    conn_atual.commit()
    conn_imp.close()
    conn_atual.close()
    return True
