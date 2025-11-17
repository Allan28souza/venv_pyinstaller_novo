# admin_views/avaliadores_admin.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import database as db
from utils import show_info, show_error


class AvaliadoresAdmin:
    """
    Gerenciador de Avaliadores – CRUD completo.
    Abre dentro da janela principal do Admin.
    """

    def __init__(self, root, callback_voltar):
        self.root = root
        self.callback_voltar = callback_voltar

        self._build_ui()
        self._carregar()

    # ---------------------------------------------------
    def _limpar(self):
        for w in self.root.winfo_children():
            w.destroy()

    # ---------------------------------------------------
    def _build_ui(self):
        self._limpar()

        tk.Label(self.root, text="Avaliadores",
                 font=("Arial", 16, "bold")).pack(pady=8)

        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.lista = tk.Listbox(frame)
        self.lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(frame, command=self.lista.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        self.lista.config(yscrollcommand=sb.set)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Novo", width=16,
                   command=self._novo).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text="Editar", width=16,
                   command=self._editar).grid(row=0, column=1, padx=6)
        ttk.Button(btn_frame, text="Excluir", width=16,
                   command=self._excluir).grid(row=0, column=2, padx=6)
        ttk.Button(btn_frame, text="Voltar", width=16,
                   command=self.callback_voltar).grid(row=0, column=3, padx=6)

    # ---------------------------------------------------
    def _carregar(self):
        self.lista.delete(0, tk.END)
        try:
            avaliadores = db.listar_avaliadores()
            for a in avaliadores:
                self.lista.insert(tk.END, a)
        except Exception as e:
            show_error("Erro", f"Falha ao carregar avaliadores:\n{e}")

    # ---------------------------------------------------
    def _novo(self):
        nome = simpledialog.askstring(
            "Novo Avaliador", "Nome:", parent=self.root)
        if not nome:
            return

        try:
            db.garantir_avaliador(nome)
            show_info("Sucesso", "Avaliador cadastrado")
            self._carregar()
        except Exception as e:
            show_error("Erro", f"Falha ao criar avaliador:\n{e}")

    # ---------------------------------------------------
    def _editar(self):
        sel = self.lista.curselection()
        if not sel:
            show_error("Erro", "Selecione um avaliador!", parent=self.root)
            return

        nome_atual = self.lista.get(sel[0])

        novo_nome = simpledialog.askstring(
            "Editar Avaliador",
            "Nome:",
            initialvalue=nome_atual,
            parent=self.root
        )
        if not novo_nome:
            return

        try:
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("UPDATE avaliadores SET nome=? WHERE nome=?",
                        (novo_nome, nome_atual))
            conn.commit()
            conn.close()

            show_info("Sucesso", "Avaliador atualizado")
            self._carregar()

        except Exception as e:
            show_error("Erro", f"Falha ao atualizar avaliador:\n{e}")

    # ---------------------------------------------------
    def _excluir(self):
        sel = self.lista.curselection()
        if not sel:
            show_error("Erro", "Selecione um avaliador!", parent=self.root)
            return

        nome = self.lista.get(sel[0])

        if not messagebox.askyesno("Confirmar",
                                   f"Excluir avaliador '{nome}'?",
                                   parent=self.root):
            return

        try:
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM avaliadores WHERE nome=?", (nome,))
            conn.commit()
            conn.close()

            show_info("OK", "Avaliador excluído")
            self._carregar()

        except Exception as e:
            show_error("Erro", f"Falha ao excluir avaliador:\n{e}")
