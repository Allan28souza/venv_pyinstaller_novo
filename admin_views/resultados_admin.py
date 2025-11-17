# admin_views/resultados_admin.py
import tkinter as tk
from tkinter import ttk
from utils import show_error
import database as db


class ResultadosAdmin:
    """
    Tela que lista todos os resultados registrados no sistema.
    """

    def __init__(self, root, callback_voltar):
        self.root = root
        self.callback_voltar = callback_voltar

        self._build_ui()
        self._carregar_resultados()

    # -------------------------------------------------------
    def _limpar(self):
        for w in self.root.winfo_children():
            w.destroy()

    # -------------------------------------------------------
    def _build_ui(self):
        self._limpar()

        tk.Label(self.root, text="Resultados Registrados",
                 font=("Arial", 16, "bold")).pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        cols = ("ID", "Operador", "Matrícula", "Teste", "Avaliador",
                "Acertos", "Total", "%", "Data", "Tempo Total (s)")

        self.tree = ttk.Treeview(frame, columns=cols, show="headings")

        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Voltar
        ttk.Button(self.root, text="Voltar",
                   command=self.callback_voltar).pack(pady=8)

    # -------------------------------------------------------
    def _carregar_resultados(self):
        """
        Carrega resultados do banco e insere na tabela.
        """
        try:
            resultados = db.listar_resultados()
        except Exception as e:
            show_error("Erro", f"Falha ao carregar resultados:\n{e}")
            return

        for r in resultados:
            # Ajuste conforme estrutura retornada pelo seu DB
            # Esperado: (id, operador_id, operador_nome, matricula, teste_id, teste_nome,
            # avaliador, acertos, total, porcentagem, data, tempo_total)
            try:
                resultado_id = r[0]
                operador = r[2]
                matricula = r[3]
                teste_nome = r[5]
                avaliador = r[6]
                acertos = r[7]
                total = r[8]
                porcentagem = f"{r[9]:.2f}" if r[9] is not None else ""
                data = r[10]
                tempo_total = r[11]

                self.tree.insert("", tk.END, values=(
                    resultado_id, operador, matricula, teste_nome,
                    avaliador, acertos, total, porcentagem, data, tempo_total
                ))
            except Exception:
                # Em caso de inconsistência no DB, evita travar a tela
                continue
