# executor_rr.py
import sqlite3
import os
from collections import defaultdict, Counter
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from io import BytesIO
import utils

DB_PATH = None


def _get_conn():
    global DB_PATH
    if DB_PATH is None:
        # importa database.py para descobrir path se disponível
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


def _fetch_respostas(teste_id):
    """
    retorna lista de dicts:
    {operador_id, operador_nome, repeticao (int or inferred), nome_arquivo, resposta_usuario, resposta_correta, data_hora}
    """
    conn = _get_conn()
    cur = conn.cursor()

    # consulta resultados + respostas + operador nome
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

    # rows: resultado_id, operador_id, operador_nome, repeticao (may be None), data_hora, nome_arquivo, resposta_usuario, resposta_correta
    data = []
    for rid, opid, opnome, repeticao, data_hora, nome_arquivo, resp_user, resp_corr in rows:
        data.append({
            "resultado_id": rid,
            "operador_id": opid,
            "operador_nome": opnome or "",
            "repeticao": repeticao,
            "data_hora": data_hora,
            "nome_arquivo": nome_arquivo,
            "resposta_usuario": (resp_user or "").upper().strip(),
            "resposta_correta": (resp_corr or "").upper().strip(),
        })

    # infer repetitions if repeticao is None for some rows
    if not data:
        return data

    if any(d["repeticao"] is None for d in data):
        # infer repeticao per operador by ordering distinct resultado_id timestamps
        # Group by operador_id -> distinct resultado_id -> order by data_hora -> assign 1..n
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
        # mapping resultado_id -> inferred repeticao index per operador
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

        # apply mapping to data (resultados ids available earlier)
        # but our 'data' entries don't include resultado_id consistently; we have it as "resultado_id" field
        for d in data:
            if d["repeticao"] is None:
                rid = d["resultado_id"]
                d["repeticao"] = rep_map.get(rid, 1)

    # ensure repeticao are integers
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
    """
    Retorna dict:
    {
      operador_id, operador_nome,
      total_imagens, imagens_consistentes, porcentagem_consistencia,
      inconsistencias: [(nome_arquivo, respostas_por_repeticao_dict)]
    }
    """
    dados = _fetch_respostas(teste_id)
    # filtrar por operador
    dados_op = [d for d in dados if d["operador_id"] == operador_id]
    if not dados_op:
        return None

    # agrupar por imagem -> repeticao -> resposta
    mapa = defaultdict(lambda: defaultdict(list))
    nome_op = None
    for d in dados_op:
        nome_op = d["operador_nome"] or nome_op
        mapa[d["nome_arquivo"]][d["repeticao"]].append(d["resposta_usuario"])

    total = len(mapa)
    inconsistencias = []
    consistentes = 0
    for nome_img, reps in mapa.items():
        # reduzir respostas por repetição para single value: majority within repetition (should be one)
        vals = []
        for rep in sorted(reps.keys()):
            vlist = [v for v in reps[rep] if v]
            if not vlist:
                vals.append(None)
            else:
                vals.append(Counter(vlist).most_common(1)[0][0])
        # check if all vals equal and not None
        unique = set([v for v in vals if v is not None])
        if len(unique) <= 1:
            consistentes += 1
        else:
            inconsistencias.append(
                (nome_img, {rep: reps[rep] for rep in reps}))
    porcent = (consistentes / total * 100) if total else 0
    return {
        "operador_id": operador_id,
        "operador_nome": nome_op,
        "total_imagens": total,
        "imagens_consistentes": consistentes,
        "porcentagem_consistencia": porcent,
        "inconsistencias": inconsistencias
    }

# -----------------------------
# 2) Reprodutibilidade (entre operadores)
# -----------------------------


def calcular_reprodutibilidade(teste_id):
    """
    Retorna:
    {
       testes_id,
       operadores: [ids...],
       operador_majority_resposta: {operador_id: {nome_arquivo: majority_response}},
       matriz_concordancia: {opA: {opB: percent_equal}},
       concordancia_vs_majority: {operador_id: percent}
    }
    """
    dados = _fetch_respostas(teste_id)
    if not dados:
        return None

    # compute per-operator majority per image (collapse repetitions by majority)
    per_op_img = defaultdict(lambda: defaultdict(list))
    op_names = {}
    for d in dados:
        op = d["operador_id"]
        op_names[op] = d["operador_nome"]
        per_op_img[op][d["nome_arquivo"]].append(d["resposta_usuario"])

    # majority
    majority_per_op = {}
    for op, imgs in per_op_img.items():
        majority_per_op[op] = {}
        for img, responses in imgs.items():
            filtered = [r for r in responses if r]
            majority_per_op[op][img] = Counter(filtered).most_common(1)[
                0][0] if filtered else None

    # list of operators
    operadores = sorted(majority_per_op.keys())

    # build concordance matrix
    matriz = {a: {} for a in operadores}
    for a in operadores:
        for b in operadores:
            # compare only images both have
            imgs_a = set(majority_per_op[a].keys())
            imgs_b = set(majority_per_op[b].keys())
            comuns = imgs_a & imgs_b
            if not comuns:
                matriz[a][b] = None
                continue
            iguais = sum(1 for img in comuns if (
                majority_per_op[a].get(img) == majority_per_op[b].get(img)))
            matriz[a][b] = iguais / len(comuns) * 100

    # compute majority across operators per image, then concordance of each operator vs global majority
    images_all = set(d["nome_arquivo"] for d in dados)
    majority_global = {}
    for img in images_all:
        votes = []
        for op in operadores:
            v = majority_per_op.get(op, {}).get(img)
            if v:
                votes.append(v)
        if votes:
            majority_global[img] = Counter(votes).most_common(1)[0][0]
        else:
            majority_global[img] = None

    concord_vs_global = {}
    for op in operadores:
        total = 0
        match = 0
        for img, maj in majority_global.items():
            if maj is None:
                continue
            v = majority_per_op.get(op, {}).get(img)
            if v is None:
                continue
            total += 1
            if v == maj:
                match += 1
        concord_vs_global[op] = (match / total * 100) if total else None

    return {
        "teste_id": teste_id,
        "operadores": operadores,
        "operador_nomes": op_names,
        "majority_per_op": majority_per_op,
        "matriz_concordancia": matriz,
        "concordancia_vs_global": concord_vs_global,
        "majority_global": majority_global
    }

# -----------------------------
# 3) Operadores desalinhados
# -----------------------------


def identificar_operadores_desalinhados(teste_id, top_n=5):
    rep = calcular_reprodutibilidade(teste_id)
    if not rep:
        return []
    concord = rep["concordancia_vs_global"]
    # build list of (op, percent) sorted ascending (lowest agreement first)
    lst = []
    for op, val in concord.items():
        lst.append((op, rep["operador_nomes"].get(
            op, ""), val if val is not None else -1))
    lst_sorted = sorted(lst, key=lambda x: (x[2] if x[2] is not None else -1))
    return lst_sorted[:top_n]

# -----------------------------
# 4) Itens confusos
# -----------------------------


def calcular_itens_confusos(teste_id):
    dados = _fetch_respostas(teste_id)
    if not dados:
        return []
    # for each image gather all responses (use all reps and operators)
    mapa = defaultdict(list)
    for d in dados:
        if d["resposta_usuario"]:
            mapa[d["nome_arquivo"]].append(d["resposta_usuario"])
    results = []
    for img, votes in mapa.items():
        cnt = Counter(votes)
        total = sum(cnt.values())
        if total == 0:
            disagreement = 0.0
        else:
            top = cnt.most_common(1)[0][1]
            # 0 = full agreement, 1 = full disagreement
            disagreement = 1 - (top / total)
        results.append({
            "nome_arquivo": img,
            "total_respostas": total,
            "contagem": dict(cnt),
            "discordancia": disagreement
        })
    # sort by highest discordancia
    results.sort(key=lambda x: x["discordancia"], reverse=True)
    return results

# -----------------------------
# 5) Gerar relatório RR (PDF resumido)
# -----------------------------


def gerar_relatorio_rr(teste_id, destino_folder=None):
    """
    Gera um PDF com:
     - resumo por operador (repetibilidade)
     - matriz de concordância
     - itens confusos top 20
    Retorna caminho do PDF
    """
    if destino_folder is None:
        destino_folder = os.path.join(os.path.abspath("."), "resultados")
    os.makedirs(destino_folder, exist_ok=True)

    # fetch basic info
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT nome FROM testes WHERE id=?", (teste_id,))
    t = cur.fetchone()
    nome_teste = t[0] if t else f"Teste {teste_id}"
    conn.close()

    # prepare data
    # operadores list
    rep = calcular_reprodutibilidade(teste_id)
    it_confusos = calcular_itens_confusos(teste_id)

    # repetibilidade por operador
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, nome FROM operadores ORDER BY nome")
    ops = cur.fetchall()
    conn.close()

    rep_stats = []
    for opid, opname in ops:
        r = calcular_repetibilidade_operador(opid, teste_id)
        if r:
            rep_stats.append(r)

    # create pdf
    arquivo_pdf = os.path.join(
        destino_folder, f"RR_{teste_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    largura, altura = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, altura - 2*cm, f"Relatório RR - {nome_teste}")
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, altura - 2.8*cm,
                 f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    y = altura - 3.6*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Repetibilidade por Operador")
    y -= 0.8*cm
    c.setFont("Helvetica", 10)
    for s in rep_stats:
        if y < 4*cm:
            c.showPage()
            y = altura - 2*cm
        c.drawString(
            2*cm, y, f"{s['operador_nome'] or s['operador_id']}: {s['imagens_consistentes']}/{s['total_imagens']} consistentes ({s['porcentagem_consistencia']:.1f}%)")
        y -= 0.5*cm

    y -= 0.6*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Concordância entre operadores (matriz %)")
    y -= 0.8*cm
    c.setFont("Helvetica", 9)
    if rep and rep.get("matriz_concordancia"):
        ops_list = rep["operadores"]
        # header
        line_x = 2*cm
        c.drawString(line_x, y, "Operador")
        x = line_x + 4*cm
        for op in ops_list:
            c.drawString(x, y, str(op))
            x += 2*cm
        y -= 0.4*cm
        for a in ops_list:
            if y < 4*cm:
                c.showPage()
                y = altura - 2*cm
            line_x = 2*cm
            c.drawString(line_x, y, str(a))
            x = line_x + 4*cm
            for b in ops_list:
                val = rep["matriz_concordancia"].get(a, {}).get(b)
                s_val = f"{val:.0f}" if (val is not None) else "-"
                c.drawString(x, y, s_val)
                x += 2*cm
            y -= 0.4*cm

    y -= 0.6*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y, "Itens com maior discordância (top 20)")
    y -= 0.8*cm
    c.setFont("Helvetica", 10)
    for it in it_confusos[:20]:
        if y < 4*cm:
            c.showPage()
            y = altura - 2*cm
        c.drawString(
            2*cm, y, f"{it['nome_arquivo']} - discordância: {it['discordancia']:.2f} - respostas: {it['contagem']}")
        y -= 0.5*cm

    c.showPage()
    c.save()

    utils.show_info("RR Gerado", f"Relatório RR salvo em:\n{arquivo_pdf}")
    return arquivo_pdf
