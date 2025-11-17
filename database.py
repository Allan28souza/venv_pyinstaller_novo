# database.py
import sqlite3
import os
import sys
import tempfile
from datetime import datetime
import shutil


def get_db_path():
    """Retorna caminho persistente para o banco (pasta APPDATA se for exe)."""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.join(os.environ.get(
            "APPDATA", os.path.expanduser("~")), "TesteImagensApp")
    else:
        base_dir = os.path.abspath(".")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "testes.db")


DB_PATH = get_db_path()


def conectar():
    return sqlite3.connect(DB_PATH)


def criar_tabelas():
    conn = conectar()
    c = conn.cursor()

    # testes, imagens (existentes)
    c.execute("""
    CREATE TABLE IF NOT EXISTS testes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL,
        descricao TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS imagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teste_id INTEGER NOT NULL,
        nome_arquivo TEXT NOT NULL,
        imagem BLOB NOT NULL,
        resposta_correta TEXT CHECK(resposta_correta IN ('OK','NOK')),
        FOREIGN KEY(teste_id) REFERENCES testes(id) ON DELETE CASCADE
    )""")

    # novos: operadores, avaliadores, turnos, resultados, respostas
    c.execute("""
    CREATE TABLE IF NOT EXISTS operadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        matricula TEXT UNIQUE NOT NULL,
        turno TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS avaliadores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE NOT NULL
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS turnos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_turno TEXT UNIQUE NOT NULL
    )""")

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
        FOREIGN KEY(operador_id) REFERENCES operadores(id),
        FOREIGN KEY(teste_id) REFERENCES testes(id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS respostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resultado_id INTEGER,
        nome_arquivo TEXT,
        resposta_usuario TEXT,
        resposta_correta TEXT,
        tempo INTEGER,
        FOREIGN KEY(resultado_id) REFERENCES resultados(id)
    )""")

    # garante turnos padrão (1°, 2°, 3°)
    for t in ("1° Turno", "2° Turno", "3° Turno"):
        try:
            c.execute(
                "INSERT OR IGNORE INTO turnos (nome_turno) VALUES (?)", (t,))
        except:
            pass

    conn.commit()
    conn.close()

# imagens helpers


def adicionar_imagem(teste_id, caminho, resposta_correta):
    with open(caminho, "rb") as f:
        blob = f.read()
    nome = os.path.basename(caminho)
    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO imagens (teste_id, nome_arquivo, resposta_correta, imagem) VALUES (?,?,?,?)",
              (teste_id, nome, resposta_correta, blob))
    conn.commit()
    conn.close()


def listar_imagens(teste_id):
    conn = conectar()
    c = conn.cursor()
    c.execute(
        "SELECT id, nome_arquivo, resposta_correta FROM imagens WHERE teste_id=?", (teste_id,))
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


def buscar_blob_imagem(nome_arquivo, teste_id):
    """
    Retorna o BLOB da imagem correspondente.
    """
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT imagem
        FROM imagens
        WHERE nome_arquivo = ? AND teste_id = ?
    """, (nome_arquivo, teste_id))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# operadores / avaliadores / turnos


def garantir_operador(nome, matricula, turno):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id FROM operadores WHERE matricula=?", (matricula,))
    r = c.fetchone()
    if r:
        op_id = r[0]
        # atualiza nome/turno caso tenha mudado
        c.execute("UPDATE operadores SET nome=?, turno=? WHERE id=?",
                  (nome, turno, op_id))
    else:
        c.execute("INSERT INTO operadores (nome, matricula, turno) VALUES (?,?,?)",
                  (nome, matricula, turno))
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
    """
    Retorna (nome, matricula, turno) do operador.
    """
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nome, matricula, turno
        FROM operadores
        WHERE id = ?
    """, (operador_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0], row[1], row[2]  # nome, matricula, turno
    else:
        return "", "", ""


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
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows


def listar_turnos():
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT nome_turno FROM turnos ORDER BY id")
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows


def garantir_turno(nome_turno):
    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT id FROM turnos WHERE nome_turno=?", (nome_turno,))
    r = c.fetchone()
    if r:
        tid = r[0]
    else:
        c.execute("INSERT INTO turnos (nome_turno) VALUES (?)", (nome_turno,))
        tid = c.lastrowid
    conn.commit()
    conn.close()
    return tid

# resultados


def salvar_resultado(operador_id, teste_id, avaliador, acertos, total, porcentagem, tempo_total, tempo_medio, respostas_list):
    """
    respostas_list: lista de tuples (nome_arquivo, resposta_usuario, resposta_correta, tempo_s)
    retorna id do resultado
    """
    conn = conectar()
    c = conn.cursor()
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT INTO resultados (operador_id, teste_id, avaliador, acertos, total, porcentagem, data_hora, tempo_total, tempo_medio)
                 VALUES (?,?,?,?,?,?,?,?,?)""",
              (operador_id, teste_id, avaliador, acertos, total, porcentagem, data_hora, tempo_total, tempo_medio))
    resultado_id = c.lastrowid
    for nome, resp_user, resp_correta, tempo in respostas_list:
        c.execute("""INSERT INTO respostas (resultado_id, nome_arquivo, resposta_usuario, resposta_correta, tempo)
                     VALUES (?,?,?,?,?)""", (resultado_id, nome, resp_user, resp_correta, tempo))
    conn.commit()
    conn.close()
    return resultado_id


def listar_resultados(filters=None):
    """
    Retorna resultados com filtros opcionais (dict): teste_id, operador_id, avaliador, turno, data_inicio, data_fim
    """
    filters = filters or {}
    conn = conectar()
    c = conn.cursor()
    query = """SELECT r.id, r.operador_id, o.nome, o.matricula, r.teste_id, t.nome, r.avaliador, r.acertos, r.total, r.porcentagem, r.data_hora, r.tempo_total, r.tempo_medio
               FROM resultados r
               LEFT JOIN operadores o ON o.id=r.operador_id
               LEFT JOIN testes t ON t.id=r.teste_id
               WHERE 1=1"""
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


def exportar_banco(destino_path):
    """Copia o arquivo DB atual para destino_path."""
    conn = conectar()
    conn.close()
    shutil.copy2(DB_PATH, destino_path)
    return destino_path


def importar_banco(arquivo_path, substituir=True):
    """
    Importa banco .db. Se substituir=True substitui o DB atual (após validação mínima).
    Retorna True se ok.
    """
    # valida presença de tabelas esperadas (abertura em DB temporario)
    tmp_conn = sqlite3.connect(":memory:")
    try:
        tmp_conn.close()
        # valida abrindo arquivo importado
        test_conn = sqlite3.connect(arquivo_path)
        c = test_conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in c.fetchall()]
        test_conn.close()
        needed = {"testes", "imagens", "operadores",
                  "avaliadores", "turnos", "resultados", "respostas"}
        if not needed.issubset(set(tables)):
            raise RuntimeError(
                "Arquivo selecionado não possui todas as tabelas necessárias.")
        if substituir:
            shutil.copy2(arquivo_path, DB_PATH)
            return True
        else:
            # mesclagem não implementada aqui (poderíamos criar lógica mais complexa)
            raise NotImplementedError(
                "Importação com mesclagem não implementada neste modo.")
    except Exception as e:
        raise e


def importar_banco_mesclar(arquivo_import, ignorar_duplicados=True):
    """
    Importa outro banco .db e MESCLA com o banco atual.
    Se ignorar_duplicados=True, não sobrescreve operadores, avaliadores, testes etc.
    """
    if not os.path.exists(arquivo_import):
        raise FileNotFoundError("Banco a importar não encontrado.")

    conn_atual = conectar()
    cur_atual = conn_atual.cursor()

    conn_import = sqlite3.connect(arquivo_import)
    cur_imp = conn_import.cursor()

    # -------------------------------
    # IMPORTAR OPERADORES
    # -------------------------------
    cur_imp.execute("SELECT nome, matricula, turno FROM operadores")
    for nome, mat, turno in cur_imp.fetchall():
        if ignorar_duplicados:
            cur_atual.execute(
                "SELECT id FROM operadores WHERE matricula=?", (mat,))
            existe = cur_atual.fetchone()
            if existe:
                continue
        cur_atual.execute(
            "INSERT INTO operadores (nome, matricula, turno) VALUES (?,?,?)",
            (nome, mat, turno)
        )

    # -------------------------------
    # IMPORTAR AVALIADORES
    # -------------------------------
    cur_imp.execute("SELECT nome FROM avaliadores")
    for (nome,) in cur_imp.fetchall():
        if ignorar_duplicados:
            cur_atual.execute(
                "SELECT nome FROM avaliadores WHERE nome=?", (nome,))
            if cur_atual.fetchone():
                continue
        cur_atual.execute("INSERT INTO avaliadores (nome) VALUES (?)", (nome,))

    # -------------------------------
    # IMPORTAR TESTES
    # -------------------------------
    cur_imp.execute("SELECT nome, descricao FROM testes")
    for nome, desc in cur_imp.fetchall():
        if ignorar_duplicados:
            cur_atual.execute(
                "SELECT id FROM testes WHERE nome=?", (nome,))
            if cur_atual.fetchone():
                continue
        cur_atual.execute(
            "INSERT INTO testes (nome, descricao) VALUES (?,?)",
            (nome, desc)
        )

    # -------------------------------
    # IMPORTAR RESULTADOS
    # -------------------------------
    cur_imp.execute(
        "SELECT operador_id, teste_id, avaliador, acertos, total, porcentagem, data_hora, tempo_total, tempo_medio FROM resultados")
    for r in cur_imp.fetchall():
        cur_atual.execute("""
            INSERT INTO resultados 
            (operador_id, teste_id, avaliador, acertos, total, porcentagem, data_hora, tempo_total, tempo_medio)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, r)

    # -------------------------------
    # IMPORTAR IMAGENS
    # -------------------------------
    cur_imp.execute(
        "SELECT teste_id, nome_arquivo, resposta_correta, imagem FROM imagens")
    for row in cur_imp.fetchall():
        teste_id, nome_arquivo, resposta, blob = row

        if ignorar_duplicados:
            cur_atual.execute(
                "SELECT id FROM imagens WHERE teste_id=? AND nome_arquivo=?",
                (teste_id, nome_arquivo)
            )
            if cur_atual.fetchone():
                continue

        cur_atual.execute(
            "INSERT INTO imagens (teste_id, nome_arquivo, resposta_correta, imagem) VALUES (?,?,?,?)",
            (teste_id, nome_arquivo, resposta, blob)
        )

    conn_atual.commit()
    conn_import.close()
    conn_atual.close()
