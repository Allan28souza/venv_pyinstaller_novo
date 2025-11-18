# executor_rr_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import database as db
from .executor_rr import (
    calcular_repetibilidade_operador,
    calcular_reprodutibilidade,
    identificar_operadores_desalinhados,
    calcular_itens_confusos,
    gerar_relatorio_rr
)
import os


class RRView:
    def __init__(self, root, on_close=None):
        self.root = root
        self.on_close = on_close
        self.win = tk.Toplevel(root)
        self.win.title("Análise RR")
        self.win.geometry("800x600")

        self._build_ui()
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        top = tk.Frame(self.win)
        top.pack(fill="x", padx=10, pady=8)

        tk.Label(top, text="Selecione Teste:").pack(side="left")
        self.tests_cb = ttk.Combobox(top, state="readonly", width=40)
        self.tests_cb.pack(side="left", padx=8)

        btn_refresh = ttk.Button(top, text="Carregar",
                                 command=self._carregar_testes)
        btn_refresh.pack(side="left", padx=6)

        ttk.Button(top, text="Executar Análise RR",
                   command=self._executar).pack(side="right")

        # painel texto com resultados
        self.txt = tk.Text(self.win, wrap="word")
        self.txt.pack(expand=True, fill="both", padx=10, pady=10)

        bottom = tk.Frame(self.win)
        bottom.pack(fill="x", padx=10, pady=6)
        ttk.Button(bottom, text="Exportar PDF RR",
                   command=self._export_pdf).pack(side="right")

        self._carregar_testes()

    def _carregar_testes(self):
        conn = db.conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, nome FROM testes ORDER BY nome")
        rows = cur.fetchall()
        conn.close()
        self.tests = rows
        vals = [f"{r[0]} - {r[1]}" for r in rows]
        self.tests_cb['values'] = vals
        if vals:
            self.tests_cb.current(0)

    def _get_selected_teste(self):
        sel = self.tests_cb.get()
        if not sel:
            return None
        return int(sel.split(" - ", 1)[0])

    def _executar(self):
        teste_id = self._get_selected_teste()
        if not teste_id:
            messagebox.showerror("Erro", "Selecione um teste")
            return

        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, f"Analisando teste {teste_id}...\n\n")

        # repetibilidade por operador
        conn = db.conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, nome FROM operadores ORDER BY nome")
        operadores = cur.fetchall()
        conn.close()

        self.txt.insert(tk.END, "Repetibilidade por operador:\n")
        for opid, opname in operadores:
            r = calcular_repetibilidade_operador(opid, teste_id)
            if not r:
                continue
            self.txt.insert(
                tk.END, f" - {r['operador_nome'] or opid}: {r['imagens_consistentes']}/{r['total_imagens']} consistentes ({r['porcentagem_consistencia']:.1f}%)\n")

        self.txt.insert(tk.END, "\nReprodutibilidade (entre operadores):\n")
        rep = calcular_reprodutibilidade(teste_id)
        if rep:
            self.txt.insert(
                tk.END, f"Operadores analisados: {len(rep['operadores'])}\n")
            self.txt.insert(tk.END, "Concordância vs global:\n")
            for op, val in rep['concordancia_vs_global'].items():
                nome = rep['operador_nomes'].get(op, "")
                self.txt.insert(tk.END, f" - {nome or op}: {val:.1f}%\n")

        self.txt.insert(tk.END, "\nItens mais confusos:\n")
        itens = calcular_itens_confusos(teste_id)
        for it in itens[:20]:
            self.txt.insert(
                tk.END, f" - {it['nome_arquivo']}: discordância {it['discordancia']:.2f}, respostas {it['contagem']}\n")

        self.txt.insert(tk.END, "\nOperadores mais desalinhados:\n")
        desalinhados = identificar_operadores_desalinhados(teste_id, top_n=10)
        for opid, opnome, val in desalinhados:
            self.txt.insert(
                tk.END, f" - {opnome or opid}: {val if val is not None else 'N/A'}\n")

        self.txt.see("1.0")

    def _export_pdf(self):
        teste_id = self._get_selected_teste()
        if not teste_id:
            messagebox.showerror("Erro", "Selecione um teste")
            return
        caminho = gerar_relatorio_rr(teste_id)
        try:
            os.startfile(caminho)
        except:
            pass

    def _on_close(self):
        try:
            if callable(self.on_close):
                self.on_close()
        finally:
            self.win.destroy()
