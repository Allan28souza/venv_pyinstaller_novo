# executar/rr_analise.py

import database as db
from collections import defaultdict
from statistics import mode


# ----------------------------------------------------------
# Coleta respostas do banco
# ----------------------------------------------------------
def _coletar_respostas(teste_id):
    conn = db.conectar()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            o.id, 
            o.nome, 
            r.id, 
            resp.nome_arquivo, 
            resp.resposta_usuario, 
            resp.resposta_correta
        FROM respostas resp
        JOIN resultados r ON r.id = resp.resultado_id
        LEFT JOIN operadores o ON o.id = r.operador_id
        WHERE r.teste_id=?
    """, (teste_id,))

    rows = cur.fetchall()
    conn.close()

    respostas_por_operador = defaultdict(lambda: defaultdict(list))
    nomes_operadores = {}

    # rows = (op_id, op_nome, resultado_id, nome_arquivo, resp_user, resp_corr)
    for op_id, op_nome, r_id, arquivo, resp_user, resp_corr in rows:
        if op_id is None:
            continue

        nomes_operadores[op_id] = op_nome or f"Operador {op_id}"

        if arquivo:
            respostas_por_operador[op_id][arquivo].append(
                (resp_user or "").upper().strip()
            )

    return respostas_por_operador, nomes_operadores


# ----------------------------------------------------------
# Repetibilidade por operador
# ----------------------------------------------------------
def calcular_repetibilidade_operador(op_id, teste_id):
    respostas_por_operador, nomes = _coletar_respostas(teste_id)
    dados = respostas_por_operador.get(op_id, {})

    total_itens = 0
    consistentes = 0

    for arquivo, respostas in dados.items():
        respostas = [r for r in respostas if r]  # ignora vazios
        if len(respostas) > 1:
            total_itens += 1
            if len(set(respostas)) == 1:
                consistentes += 1

    if total_itens == 0:
        return None

    return {
        "operador_id": op_id,
        "operador_nome": nomes.get(op_id, f"Operador {op_id}"),
        "itens": total_itens,
        "consistentes": consistentes,
        "porcentagem_consistencia": (consistentes / total_itens) * 100
    }


# ----------------------------------------------------------
# Reprodutibilidade entre operadores
# ----------------------------------------------------------
def calcular_reprodutibilidade(teste_id):
    respostas_por_operador, nomes = _coletar_respostas(teste_id)
    operadores = list(respostas_por_operador.keys())

    if not operadores:
        return None

    # Base geral por imagem
    votos_por_img = defaultdict(list)
    for op, imgs in respostas_por_operador.items():
        for img, reps in imgs.items():
            votos_por_img[img].extend(reps)

    # Consenso global
    consenso = {}
    for img, respostas in votos_por_img.items():
        respostas = [r for r in respostas if r]
        try:
            consenso[img] = mode(respostas)
        except:
            consenso[img] = "NOK"  # padrão mais rígido

    # Concordância vs consenso global
    concord = {}
    for op, imgs in respostas_por_operador.items():
        total = 0
        acertos = 0
        for img, reps in imgs.items():
            for r in reps:
                total += 1
                if r == consenso.get(img):
                    acertos += 1
        concord[op] = (acertos / total * 100) if total else 0

    # Matriz operador vs operador
    matriz = defaultdict(dict)
    for a in operadores:
        for b in operadores:
            total = 0
            iguais = 0
            for img in respostas_por_operador[a]:
                if img in respostas_por_operador[b]:
                    ra = respostas_por_operador[a][img][0]
                    rb = respostas_por_operador[b][img][0]
                    total += 1
                    if ra == rb:
                        iguais += 1
            matriz[a][b] = (iguais / total * 100) if total else None

    return {
        "operadores": operadores,
        "operador_nomes": nomes,
        "concordancia_vs_global": concord,
        "matriz_concordancia": matriz,
        "consenso": consenso,
        "respostas": respostas_por_operador
    }


# ----------------------------------------------------------
# Itens confusos
# ----------------------------------------------------------
def calcular_itens_confusos(teste_id):
    respostas_por_operador, _ = _coletar_respostas(teste_id)

    cont = defaultdict(lambda: {"OK": 0, "NOK": 0})

    for op, imgs in respostas_por_operador.items():
        for img, reps in imgs.items():
            for r in reps:
                if r in ("OK", "NOK"):
                    cont[img][r] += 1

    itens = []
    for img, c in cont.items():
        total = c["OK"] + c["NOK"]
        if total == 0:
            continue
        disc = 2 * (min(c["OK"], c["NOK"]) / total)  # vai de 0 a 1

        itens.append({
            "nome_arquivo": img,
            "contagem": c,
            "discordancia": disc
        })

    itens.sort(key=lambda x: x["discordancia"], reverse=True)
    return itens


# ----------------------------------------------------------
# Texto usado no painel RRView
# ----------------------------------------------------------
def analisar_rr(teste_id):
    rep = calcular_reprodutibilidade(teste_id)
    if not rep:
        return "Nenhum dado encontrado para este teste."

    operadores = rep["operadores"]
    nomes = rep["operador_nomes"]
    concord = rep["concordancia_vs_global"]

    texto = "Repetibilidade por operador:\n"
    for op in operadores:
        r = calcular_repetibilidade_operador(op, teste_id)
        if r:
            texto += f" - {r['operador_nome']}: {r['consistentes']}/{r['itens']} consistentes ({r['porcentagem_consistencia']:.1f}%)\n"
        else:
            texto += f" - {nomes.get(op, op)}: sem dados suficientes.\n"

    texto += "\nReprodutibilidade (entre operadores):\n"
    texto += f"Operadores analisados: {len(operadores)}\n"
    for op in operadores:
        texto += f" - {nomes.get(op, op)}: {concord.get(op, 0):.1f}%\n"

    itens = calcular_itens_confusos(teste_id)
    texto += "\nItens mais confusos:\n"
    for it in itens[:10]:
        texto += f" - {it['nome_arquivo']}: discordância {it['discordancia']:.2f}, respostas {it['contagem']}\n"

    texto += "\nOperadores mais desalinhados:\n"
    lista = sorted(concord.items(), key=lambda x: x[1])
    for op, c in lista:
        texto += f" - {nomes.get(op, op)}: {c:.1f}\n"

    return texto
