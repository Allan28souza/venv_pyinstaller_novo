# executar/rr_graficos.py
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from io import BytesIO

# Importações principais do RR
from .executor_rr import (
    calcular_repetibilidade_operador,
    calcular_reprodutibilidade,
    calcular_itens_confusos
)

# -----------------------------
# Utilidades
# -----------------------------


def _ensure_dir(folder):
    os.makedirs(folder, exist_ok=True)
    return folder


def _save_fig(fig, nome_arquivo, pasta="resultados/rr_figs", dpi=150):
    _ensure_dir(pasta)
    path = os.path.join(pasta, nome_arquivo)
    fig.savefig(path, bbox_inches="tight", dpi=dpi)
    plt.close(fig)
    return path


# -----------------------------
# 1) Repetibilidade por operador
# -----------------------------
def plot_repetibilidade(teste_id, operadores_ids=None, pasta="resultados/rr_figs"):
    rep_overall = calcular_reprodutibilidade(teste_id)
    if not rep_overall:
        raise RuntimeError("Sem dados para esse teste.")

    operadores = rep_overall["operadores"]

    nomes = []
    valores = []

    for op in operadores:
        r = calcular_repetibilidade_operador(op, teste_id)
        if r:
            nomes.append(r["operador_nome"] or str(op))
            valores.append(r["porcentagem_consistencia"])
        else:
            nomes.append(str(op))
            valores.append(0.0)

    # FIGSIZE reduzido em 20%
    fig, ax = plt.subplots(figsize=(8 * 0.8, max(3, 0.5 * len(nomes)) * 0.8))

    y_pos = np.arange(len(nomes))
    ax.barh(y_pos, valores)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(nomes)
    ax.invert_yaxis()
    ax.set_xlabel("Porcentagem de consistência (%)")
    ax.set_title("Repetibilidade por operador")

    for i, v in enumerate(valores):
        ax.text(v + 1, i, f"{v:.1f}%", va="center")

    nome = f"repetibilidade_{teste_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    return _save_fig(fig, nome, pasta=pasta)


# -----------------------------
# 2) Reprodutibilidade
# -----------------------------
def plot_reprodutibilidade(teste_id, pasta="resultados/rr_figs"):
    rep = calcular_reprodutibilidade(teste_id)
    if not rep:
        raise RuntimeError("Sem dados para esse teste.")

    operadores = rep["operadores"]
    nomes_map = rep.get("operador_nomes", {})
    concord = rep["concordancia_vs_global"]

    nomes = []
    valores = []

    for op in operadores:
        nomes.append(nomes_map.get(op, str(op)))
        v = concord.get(op)
        valores.append(v if v is not None else 0.0)

    fig, ax = plt.subplots(figsize=(8 * 0.8, max(3, 0.5 * len(nomes)) * 0.8))

    x = np.arange(len(nomes))
    ax.bar(x, valores)
    ax.set_xticks(x)
    ax.set_xticklabels(nomes, rotation=45, ha="right")
    ax.set_ylabel("Concordância vs consenso (%)")
    ax.set_title("Reprodutibilidade - Concordância vs Consenso")

    for i, v in enumerate(valores):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center")

    nome = f"reprodutibilidade_{teste_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    return _save_fig(fig, nome, pasta=pasta)


# -----------------------------
# 3) Itens mais confusos
# -----------------------------
def plot_itens_confusos(teste_id, top_n=20, pasta="resultados/rr_figs"):
    itens = calcular_itens_confusos(teste_id)
    if not itens:
        raise RuntimeError("Sem dados para esse teste.")

    top = itens[:top_n]
    nomes = [it["nome_arquivo"] for it in top][::-1]
    disc = [it["discordancia"] for it in top][::-1]

    fig, ax = plt.subplots(figsize=(9 * 0.8, max(3, 0.4 * len(nomes)) * 0.8))

    y_pos = np.arange(len(nomes))
    ax.barh(y_pos, disc)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(nomes)
    ax.invert_yaxis()
    ax.set_xlabel("Discordância (0 a 1)")
    ax.set_title("Itens com maior discordância")

    for i, v in enumerate(disc):
        ax.text(v + 0.01, i, f"{v:.2f}", va="center")

    nome = f"itens_confusos_{teste_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    return _save_fig(fig, nome, pasta=pasta)


# -----------------------------
# 4) OK / NOK por imagem
# -----------------------------
def plot_ok_nok_por_imagem(teste_id, top_n=10, pasta="resultados/rr_figs"):
    itens = calcular_itens_confusos(teste_id)
    if not itens:
        raise RuntimeError("Sem dados para esse teste.")

    selection = itens[:top_n]

    nomes = [it["nome_arquivo"] for it in selection][::-1]
    oks = [it["contagem"].get("OK", 0) for it in selection][::-1]
    noks = [it["contagem"].get("NOK", 0) for it in selection][::-1]

    fig, ax = plt.subplots(figsize=(10 * 0.8, max(3, 0.6 * len(nomes)) * 0.8))

    ind = np.arange(len(nomes))
    p1 = ax.barh(ind, oks)
    p2 = ax.barh(ind, noks, left=oks)

    ax.set_yticks(ind)
    ax.set_yticklabels(nomes)
    ax.invert_yaxis()
    ax.set_xlabel("Quantidade de respostas")
    ax.set_title("OK / NOK por imagem")

    for i, (o, no) in enumerate(zip(oks, noks)):
        ax.text(o/2, i, str(o), color="white", ha="center")
        ax.text(o + no/2, i, str(no), color="white", ha="center")

    nome = f"ok_nok_{teste_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    return _save_fig(fig, nome, pasta=pasta)


# -----------------------------
# 5) Heatmap de concordância
# -----------------------------
def plot_heatmap_concordancia(teste_id, pasta="resultados/rr_figs"):
    rep = calcular_reprodutibilidade(teste_id)
    if not rep:
        raise RuntimeError("Sem dados para esse teste.")

    matriz = rep["matriz_concordancia"]
    operadores = rep["operadores"]
    nomes_map = rep.get("operador_nomes", {})

    n = len(operadores)
    M = np.zeros((n, n), dtype=float)

    for i, a in enumerate(operadores):
        for j, b in enumerate(operadores):
            v = matriz.get(a, {}).get(b)
            M[i, j] = np.nan if v is None else v

    fig, ax = plt.subplots(figsize=(8 * 0.8, 6 * 0.8))

    sns.heatmap(
        M,
        xticklabels=[nomes_map.get(o, o) for o in operadores],
        yticklabels=[nomes_map.get(o, o) for o in operadores],
        annot=True, fmt=".0f", cmap="viridis",
        ax=ax, cbar_kws={"label": "Concordância (%)"}
    )

    ax.set_title("Heatmap de Concordância entre Operadores")

    nome = f"heatmap_concordancia_{teste_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    return _save_fig(fig, nome, pasta=pasta)


# -----------------------------
# 6) Tendência OK/NOK por operador
# -----------------------------
def plot_tendencia_operador(teste_id, pasta="resultados/rr_figs"):
    rep = calcular_reprodutibilidade(teste_id)
    if not rep:
        raise RuntimeError("Sem dados para esse teste.")

    operadores = rep["operadores"]
    nomes_map = rep.get("operador_nomes", {})

    maj = rep["majority_per_op"]
    oks = []
    noks = []

    for op in operadores:
        opdict = maj.get(op, {})
        ok_c = sum(1 for v in opdict.values() if str(v).upper() == "OK")
        nok_c = sum(1 for v in opdict.values() if str(v).upper() == "NOK")
        oks.append(ok_c)
        noks.append(nok_c)

    fig, ax = plt.subplots(
        figsize=(9 * 0.8, max(3, 0.4 * len(operadores)) * 0.8))

    ind = np.arange(len(operadores))
    ax.bar(ind, oks)
    ax.bar(ind, noks, bottom=oks)

    ax.set_xticks(ind)
    ax.set_xticklabels([nomes_map.get(o, o)
                        for o in operadores], rotation=45, ha="right")
    ax.set_title("Tendência OK / NOK por operador")

    for i, (o, no) in enumerate(zip(oks, noks)):
        total = o + no
        if total:
            ax.text(i, total + 0.5, f"{o}/{total}", ha="center")

    nome = f"tendencia_operador_{teste_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    return _save_fig(fig, nome, pasta=pasta)


# -----------------------------
# 7) Gera todos os gráficos
# -----------------------------
def gerar_todos_graficos(teste_id, pasta="resultados/rr_figs"):
    _ensure_dir(pasta)
    return {
        "repetibilidade": plot_repetibilidade(teste_id, pasta=pasta),
        "reprodutibilidade": plot_reprodutibilidade(teste_id, pasta=pasta),
        "itens_confusos": plot_itens_confusos(teste_id, pasta=pasta),
        "ok_nok": plot_ok_nok_por_imagem(teste_id, pasta=pasta),
        "heatmap": plot_heatmap_concordancia(teste_id, pasta=pasta),
        "tendencia": plot_tendencia_operador(teste_id, pasta=pasta),
    }
