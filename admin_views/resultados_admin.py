# admin_views/resultados_admin.py

import tkinter as tk
from tkinter import ttk, filedialog
import csv
import datetime
import database as db
from utils import show_error, show_info


class ResultadosAdmin:
    def __init__(self, root, voltar_callback):
        self.root = root
        self.voltar_callback = voltar_callback

        self.win = tk.Toplevel(self.root)
        self.win.title("Resultados dos Testes")

        # Maximiza a janela
        try:
            self.win.state("zoomed")
        except:
            try:
                self.win.attributes('-zoomed', True)
            except:
                w = self.win.winfo_screenwidth()
                h = self.win.winfo_screenheight()
                self.win.geometry(f"{w}x{h}+0+0")

        self._montar_layout()

    # ============================================================
    # LAYOUT
    # ============================================================
    def _montar_layout(self):
        filtro_frame = tk.LabelFrame(
            self.win, text="Filtros", padx=10, pady=10)
        filtro_frame.pack(fill="x", padx=10, pady=10)

        # Campos de filtro
        ttk.Label(filtro_frame, text="Operador:").grid(
            row=0, column=0, sticky="w")
        self.cb_operador = ttk.Combobox(filtro_frame, values=[
            f"{op[1]} ({op[2]})" for op in db.listar_operadores()
        ], state="readonly", width=30)
        self.cb_operador.grid(row=0, column=1, padx=5)

        ttk.Label(filtro_frame, text="Matrícula:").grid(
            row=0, column=2, sticky="w")
        self.ent_mat = ttk.Entry(filtro_frame, width=20)
        self.ent_mat.grid(row=0, column=3, padx=5)

        ttk.Label(filtro_frame, text="Teste:").grid(
            row=1, column=0, sticky="w")
        self.cb_teste = ttk.Combobox(
            filtro_frame,
            values=[f"{t[0]} - {t[1]}" for t in self._listar_testes()],
            state="readonly", width=30
        )
        self.cb_teste.grid(row=1, column=1, padx=5)

        ttk.Label(filtro_frame, text="Avaliador:").grid(
            row=1, column=2, sticky="w")
        self.cb_avaliador = ttk.Combobox(
            filtro_frame,
            values=db.listar_avaliadores(),
            state="readonly", width=20
        )
        self.cb_avaliador.grid(row=1, column=3, padx=5)

        ttk.Label(filtro_frame, text="Turno:").grid(
            row=2, column=0, sticky="w")
        self.cb_turno = ttk.Combobox(
            filtro_frame,
            values=db.listar_turnos(),
            state="readonly", width=20
        )
        self.cb_turno.grid(row=2, column=1, padx=5)

        ttk.Label(
            filtro_frame, text="Data início (YYYY-MM-DD):").grid(row=2, column=2, sticky="w")
        self.ent_dt_ini = ttk.Entry(filtro_frame, width=20)
        self.ent_dt_ini.grid(row=2, column=3, padx=5)

        ttk.Label(
            filtro_frame, text="Data fim (YYYY-MM-DD):").grid(row=3, column=2, sticky="w")
        self.ent_dt_fim = ttk.Entry(filtro_frame, width=20)
        self.ent_dt_fim.grid(row=3, column=3, padx=5)

        # Botões
        ttk.Button(filtro_frame, text="Aplicar Filtros", command=self.aplicar_filtros)\
            .grid(row=4, column=1, pady=10)

        ttk.Button(filtro_frame, text="Limpar", command=self.limpar_filtros)\
            .grid(row=4, column=2, pady=10)

        ttk.Button(filtro_frame, text="Voltar", command=self.win.destroy)\
            .grid(row=4, column=3, pady=10)

        # Tabela
        colunas = [
            "ID", "Operador", "Matrícula", "Teste", "Avaliador",
            "Acertos", "Total", "%", "Data", "Tempo Total", "Tempo Médio"
        ]

        self.tree = ttk.Treeview(self.win, columns=colunas, show="headings")
        for col in colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        self.carregar_todos()

        # Rodapé exportações
        export_frame = tk.Frame(self.win)
        export_frame.pack(fill="x", pady=10)

        ttk.Button(export_frame, text="Exportar CSV", command=self.exportar_csv)\
            .pack(side="left", padx=10)

        ttk.Button(export_frame, text="Exportar Excel", command=self.exportar_excel)\
            .pack(side="left", padx=10)

    # ============================================================
    # LISTAR TESTES
    # ============================================================
    def _listar_testes(self):
        conn = db.conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, nome FROM testes ORDER BY nome")
        rows = cur.fetchall()
        conn.close()
        return rows

    # ============================================================
    # CARREGAR DADOS
    # ============================================================
    def carregar_todos(self):
        self.tree.delete(*self.tree.get_children())
        for r in db.listar_resultados():
            self.tree.insert("", tk.END, values=(
                r[0], r[2], r[3], r[5], r[6], r[7], r[8],
                f"{r[9]:.2f}" if r[9] else "",
                r[10],
                f"{r[11]}s" if r[11] else "",
                f"{r[12]:.2f}s" if r[12] else ""
            ))

    # ============================================================
    # APLICAR FILTROS
    # ============================================================
    def aplicar_filtros(self):
        filtros = {}

        # Operador (nome + matricula no text)
        if self.cb_operador.get():
            nome = self.cb_operador.get().split(" (")[0]
            # buscar ID
            for op in db.listar_operadores():
                if op[1] == nome:
                    filtros["operador_id"] = op[0]

        # Matrícula específica
        mat = self.ent_mat.get().strip()
        if mat:
            for op in db.listar_operadores():
                if op[2] == mat:
                    filtros["operador_id"] = op[0]

        # Teste
        if self.cb_teste.get():
            teste_id = int(self.cb_teste.get().split(" - ")[0])
            filtros["teste_id"] = teste_id

        # Avaliador
        if self.cb_avaliador.get():
            filtros["avaliador"] = self.cb_avaliador.get()

        # Turno
        if self.cb_turno.get():
            filtros["turno"] = self.cb_turno.get()

        # Datas
        if self.ent_dt_ini.get().strip():
            filtros["data_inicio"] = self.ent_dt_ini.get().strip() + \
                " 00:00:00"

        if self.ent_dt_fim.get().strip():
            filtros["data_fim"] = self.ent_dt_fim.get().strip() + " 23:59:59"

        resultados = db.listar_resultados(filtros)

        self.tree.delete(*self.tree.get_children())

        if not resultados:
            show_info("Aviso", "Nenhum resultado encontrado com esses filtros.")
            return

        for r in resultados:
            self.tree.insert("", tk.END, values=(
                r[0], r[2], r[3], r[5], r[6], r[7], r[8],
                f"{r[9]:.2f}" if r[9] else "",
                r[10],
                f"{r[11]}s" if r[11] else "",
                f"{r[12]:.2f}s" if r[12] else ""
            ))

    # ============================================================
    # LIMPAR FILTROS
    # ============================================================
    def limpar_filtros(self):
        self.cb_operador.set("")
        self.ent_mat.delete(0, tk.END)
        self.cb_teste.set("")
        self.cb_avaliador.set("")
        self.cb_turno.set("")
        self.ent_dt_ini.delete(0, tk.END)
        self.ent_dt_fim.delete(0, tk.END)
        self.carregar_todos()

    # ============================================================
    # EXPORTAR CSV
    # ============================================================
    def exportar_csv(self):
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not arquivo:
            return

        with open(arquivo, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "ID", "Operador", "Matrícula", "Teste", "Avaliador",
                "Acertos", "Total", "%", "Data", "TempoTotal", "TempoMédio"
            ])
            for child in self.tree.get_children():
                writer.writerow(self.tree.item(child)["values"])

        show_info("Sucesso", "Arquivo CSV exportado com sucesso!")

    # ============================================================
    # EXPORTAR EXCEL (CSV renomeado para .xls)
    # ============================================================
    def exportar_excel(self):
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".xls", filetypes=[("Excel", "*.xls")])
        if not arquivo:
            return

        with open(arquivo, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow([
                "ID", "Operador", "Matrícula", "Teste", "Avaliador",
                "Acertos", "Total", "%", "Data", "TempoTotal", "TempoMédio"
            ])
            for child in self.tree.get_children():
                writer.writerow(self.tree.item(child)["values"])

        show_info("Sucesso", "Arquivo Excel exportado com sucesso!")
