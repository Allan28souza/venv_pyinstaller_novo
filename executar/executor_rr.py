# executar_rr.py
import sqlite3
import os
from collections import defaultdict, Counter
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from io import BytesIO
import utils

DB_PATH = None


def _get_conn():
    global DB_PATH
    if DB_PATH is None:
        try:
            import database as dbmod
            DB_PATH = dbmod.get_db_path() if hasattr(
                dbmod, "get_db_path") else dbmod.DB_PATH
        except Exception:
            DB_PATH = os.path.join(os.path.abspath("."), "testes.db")
    return sqlite3.connect(DB_PATH)


def _has_repeticao():
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(resultados)")
        cols = [r[1] for r in cur.fetchall()]
        return "repeticao" in cols
    finally:
        conn.close()


# ------------------------------------------------
# Utilitários para resolver nomes/ids de imagens
# ------------------------------------------------
def get_nome_atual_imagem_por_id(imagem_id):
    """Retorna nome_arquivo atual dado imagem.id — None se não existir."""
    if imagem_id is None:
        return None
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT nome_arquivo FROM imagens WHERE id=?", (imagem_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def encontrar_imagem_por_nome_e_teste(nome_arquivo, teste_id):
    """Tenta localizar imagem pelo nome e teste_id. Retorna (id, nome_arquivo) ou (None, None)."""
    if not nome_arquivo:
        return None, None
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, nome_arquivo FROM imagens WHERE nome_arquivo=? AND teste_id=? LIMIT 1",
        (nome_arquivo, teste_id),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None


# ------------------------------------------------
# BUSCA DE RESPOSTAS (robusta: usa nome salvo e tenta mapear)
# ------------------------------------------------
def _fetch_respostas(teste_id):
    """
    Retorna lista de dicts:
    {
      resultado_id, operador_id, operador_nome, repeticao, data_hora,
      imagem_id (pode ser None), nome_arquivo (NOME ATUALIZADO OU SALVO),
      resposta_usuario, resposta_correta
    }
    """

    conn = _get_conn()
    cur = conn.cursor()

    # NOTE: puxamos o campo que sabemos que existe: resp.nome_arquivo (não resp.imagem_id)
    query = """
        SELECT r.id, r.operador_id, o.nome, r.repeticao, r.data_hora,
               resp.nome_arquivo, resp.resposta_usuario, resp.resposta_correta
        FROM resultados r
        LEFT JOIN respostas resp ON resp.resultado_id = r.id
        LEFT JOIN operadores o ON o.id = r.operador_id
        WHERE r.teste_id = ?
        ORDER BY r.operador_id, r.data_hora, r.id, resp.id
    """
    cur.execute(query, (teste_id,))
    rows = cur.fetchall()
    conn.close()

    data = []
    for rid, opid, opnome, repeticao, data_hora, nome_arquivo_salvo, resp_user, resp_corr in rows:

        imagem_id = None
        nome_atual = None

        # 1) Se respostas já tiver imagem_id (caso sua DB tenha sido migrada),
        #    tratamos isso com uma tentativa silenciosa — mas como não selecionamos imagem_id,
        #    vamos primeiro tentar encontrar pela correspondência nome+teste.
        # 2) Tentar localizar a imagem no catálogo atual pelo nome salvo
        if nome_arquivo_salvo:
            found_id, found_nome = encontrar_imagem_por_nome_e_teste(
                nome_arquivo_salvo, teste_id)
            if found_id:
                imagem_id = found_id
                nome_atual = found_nome

        # 3) fallback: tentar, se não encontrou e o campo salvo já é vazio ou diferente,
        #    apenas usar o nome salvo (padrão)
        if not nome_atual:
            nome_atual = nome_arquivo_salvo

        data.append({
            "resultado_id": rid,
            "operador_id": opid,
            "operador_nome": opnome or "",
            "repeticao": repeticao,
            "data_hora": data_hora,
            "imagem_id": imagem_id,
            "nome_arquivo": nome_atual,
            "resposta_usuario": (resp_user or "").upper().strip(),
            "resposta_correta": (resp_corr or "").upper().strip(),
        })

    # inferência de repetição se faltar (mesma lógica de antes)
    if not data:
        return data

    if any(d["repeticao"] is None for d in data):
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, operador_id, data_hora
            FROM resultados
            WHERE teste_id=?
            ORDER BY operador_id, data_hora, id
        """, (teste_id,))
        res_rows = cur.fetchall()
        conn.close()

        rep_map = {}
        last_op = None
        counter = 0

        for rid, opid, datahora in res_rows:
            if opid != last_op:
                counter = 1
                last_op = opid
            else:
                counter += 1
            rep_map[rid] = counter

        for d in data:
            if d["repeticao"] is None:
                d["repeticao"] = rep_map.get(d["resultado_id"], 1)

    for d in data:
        try:
            d["repeticao"] = int(d["repeticao"])
        except:
            d["repeticao"] = 1

    return data


# -----------------------------
# 1) Repetibilidade por operador
# -----------------------------
def calcular_repetibilidade_operador(operador_id, teste_id, num_ciclos_expected=None):
    dados = _fetch_respostas(teste_id)
    dados_op = [d for d in dados if d["operador_id"] == operador_id]
    if not dados_op:
        return None

    mapa = defaultdict(lambda: defaultdict(list))
    nome_op = None

    for d in dados_op:
        nome_op = d["operador_nome"] or nome_op
        mapa[d["nome_arquivo"]][d["repeticao"]].append(d["resposta_usuario"])

    total = len(mapa)
    inconsistencias = []
    consistentes = 0

    for nome_img, reps in mapa.items():
        vals = []
        for rep in sorted(reps.keys()):
            vlist = [v for v in reps[rep] if v]
            vals.append(Counter(vlist).most_common(1)[0][0] if vlist else None)

        unique = set([v for v in vals if v is not None])
        if len(unique) <= 1:
            consistentes += 1
        else:
            inconsistencias.append((nome_img, reps))

    porcent = (consistentes / total * 100) if total else 0

    return {
        "operador_id": operador_id,
        "operador_nome": nome_op,
        "total_imagens": total,
        "imagens_consistentes": consistentes,
        "porcentagem_consistencia": porcent,
        "inconsistencias": inconsistencias,
    }


# -----------------------------
# 2) Reprodutibilidade
# -----------------------------
def calcular_reprodutibilidade(teste_id):
    dados = _fetch_respostas(teste_id)
    if not dados:
        return None

    per_op_img = defaultdict(lambda: defaultdict(list))
    op_names = {}

    for d in dados:
        op = d["operador_id"]
        op_names[op] = d["operador_nome"]
        per_op_img[op][d["nome_arquivo"]].append(d["resposta_usuario"])

    majority_per_op = {}
    for op, imgs in per_op_img.items():
        majority_per_op[op] = {}
        for img, responses in imgs.items():
            filtered = [v for v in responses if v]
            majority_per_op[op][img] = Counter(filtered).most_common(1)[
                0][0] if filtered else None

    operadores = sorted(majority_per_op.keys())

    matriz = {a: {} for a in operadores}
    for a in operadores:
        for b in operadores:
            comuns = set(majority_per_op[a].keys()) & set(
                majority_per_op[b].keys())
            if not comuns:
                matriz[a][b] = None
                continue
            iguais = sum(
                1 for img in comuns if majority_per_op[a][img] == majority_per_op[b][img])
            matriz[a][b] = iguais / len(comuns) * 100

    images_all = set(d["nome_arquivo"] for d in dados)
    majority_global = {}
    for img in images_all:
        votos = []
        for op in operadores:
            v = majority_per_op.get(op, {}).get(img)
            if v:
                votos.append(v)
        majority_global[img] = Counter(votos).most_common(1)[
            0][0] if votos else None

    concord = {}
    for op in operadores:
        total = 0
        match = 0
        for img, maj in majority_global.items():
            if maj is None:
                continue
            resp = majority_per_op.get(op, {}).get(img)
            if resp is None:
                continue
            total += 1
            if resp == maj:
                match += 1
        concord[op] = (match / total * 100) if total else None

    return {
        "teste_id": teste_id,
        "operadores": operadores,
        "operador_nomes": op_names,
        "majority_per_op": majority_per_op,
        "matriz_concordancia": matriz,
        "concordancia_vs_global": concord,
        "majority_global": majority_global,
    }


# -----------------------------
# 3) Itens confusos
# -----------------------------
def calcular_itens_confusos(teste_id):
    dados = _fetch_respostas(teste_id)
    if not dados:
        return []

    mapa = defaultdict(list)
    for d in dados:
        if d["resposta_usuario"]:
            mapa[d["nome_arquivo"]].append(d["resposta_usuario"])

    results = []
    for img, votes in mapa.items():
        cnt = Counter(votes)
        top = cnt.most_common(1)[0][1]
        total = sum(cnt.values())
        disc = 1 - (top / total) if total else 0.0

        results.append({
            "nome_arquivo": img,
            "contagem": dict(cnt),
            "total_respostas": total,
            "discordancia": disc
        })

    results.sort(key=lambda x: x["discordancia"], reverse=True)
    return results


# -----------------------------
# 4) Gerar PDF RR
# -----------------------------
def gerar_relatorio_rr(teste_id, destino_folder=None):
    if destino_folder is None:
        destino_folder = os.path.join(os.path.abspath("."), "resultados")
    os.makedirs(destino_folder, exist_ok=True)

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT nome FROM testes WHERE id=?", (teste_id,))
    row = cur.fetchone()
    nome_teste = row[0] if row else f"Teste {teste_id}"
    conn.close()

    rep = calcular_reprodutibilidade(teste_id)
    itens = calcular_itens_confusos(teste_id)

    arquivo_pdf = os.path.join(
        destino_folder, f"RR_{teste_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    largura, altura = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, altura - 2*cm, f"Relatório RR — {nome_teste}")
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, altura - 2.8*cm,
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    y = altura - 4*cm

    # Concordância vs consenso
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Concordância vs consenso")
    y -= 0.8*cm

    for op in rep["operadores"]:
        nome = rep["operador_nomes"].get(op, f"Op {op}")
        val = rep["concordancia_vs_global"].get(op)
        txt = f"{nome}: {val:.1f}%" if val is not None else f"{nome}: -"
        c.setFont("Helvetica", 10)
        c.drawString(2*cm, y, txt)
        y -= 0.5*cm

    # Itens confusos
    y -= 1*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Itens mais confusos")
    y -= 0.8*cm

    c.setFont("Helvetica", 10)
    for it in itens[:20]:
        txt = f"{it['nome_arquivo']} — disc: {it['discordancia']:.2f} — {it['contagem']}"
        if y < 4*cm:
            c.showPage()
            y = altura - 2*cm
        c.drawString(2*cm, y, txt)
        y -= 0.5*cm

    c.showPage()
    c.save()

    utils.show_info("RR Gerado", f"Arquivo salvo:\n{arquivo_pdf}")
    return arquivo_pdf
