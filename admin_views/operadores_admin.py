# admin_views/operadores_admin.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import database as db
from utils import show_info, show_error


class OperadoresAdmin:
    """
    CRUD completo de Operadores.
    Inclui: criar, editar, excluir e listagem.
    """

    def __init__(self, root, callback_voltar):
        self.root = root
        self.callback_voltar = callback_voltar

        self._build_ui()
        self._carregar()

    # -------------------------------------------------------
    def _limpar(self):
        for w in self.root.winfo_children():
            w.destroy()

    # -------------------------------------------------------
    def _build_ui(self):
        self._limpar()

        tk.Label(self.root, text="Operadores",
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

    # -------------------------------------------------------
    def _carregar(self):
        self.lista.delete(0, tk.END)
        try:
            operadores = db.listar_operadores()
            for op_id, nome, mat, turno in operadores:
                self.lista.insert(
                    tk.END, f"{op_id} - {nome} | {mat} | {turno}")
        except Exception as e:
            show_error("Erro", f"Falha ao carregar operadores:\n{e}")

    # -------------------------------------------------------
    def _novo(self):
        nome = simpledialog.askstring("Nome", "Nome:", parent=self.root)
        self.root.update()
        if not nome:
            return

        mat = simpledialog.askstring(
            "Matrícula", "Matrícula:", parent=self.root)
        self.root.update()
        if not mat:
            return

        turnos = db.listar_turnos()
        turno = simpledialog.askstring(
            "Turno",
            f"Informe o turno ({', '.join(turnos)})"
            if turnos else "Informe o turno:",
            parent=self.root
        )
        self.root.update()
        if not turno:
            return

        try:
            db.garantir_operador(nome, mat, turno)
            show_info("Sucesso", "Operador cadastrado")
            self._carregar()
        except Exception as e:
            show_error("Erro", f"Falha ao criar operador:\n{e}")

    # -------------------------------------------------------
    def _editar(self):
        sel = self.lista.curselection()
        if not sel:
            show_error("Erro", "Selecione um operador!", parent=self.root)
            return

        item = self.lista.get(sel[0])
        op_id = int(item.split(" - ")[0])

        dados = db.obter_dados_operador(op_id)
        if not dados:
            show_error("Erro", "Operador não encontrado!", parent=self.root)
            return

        # Aceita formatos diferentes
        if len(dados) == 4:   # (id, nome, mat, turno)
            _, nome_atual, mat_atual, turno_atual = dados
        elif len(dados) == 3:  # (nome, mat, turno)
            nome_atual, mat_atual, turno_atual = dados
        else:
            nome_atual = dados[0]
            mat_atual = dados[1] if len(dados) > 1 else ""
            turno_atual = dados[2] if len(dados) > 2 else ""

        novo_nome = simpledialog.askstring(
            "Editar Nome", "Nome:", initialvalue=nome_atual, parent=self.root)
        self.root.update()
        if not novo_nome:
            return

        nova_mat = simpledialog.askstring(
            "Editar Matrícula", "Matrícula:", initialvalue=mat_atual, parent=self.root)
        self.root.update()
        if not nova_mat:
            return

        turnos = db.listar_turnos()
        novo_turno = simpledialog.askstring(
            "Editar Turno",
            f"Informe o turno ({', '.join(turnos)})"
            if turnos else "Turno:",
            initialvalue=turno_atual,
            parent=self.root
        )
        self.root.update()

        try:
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("UPDATE operadores SET nome=?, matricula=?, turno=? WHERE id=?",
                        (novo_nome, nova_mat, novo_turno, op_id))
            conn.commit()
            conn.close()

            show_info("Sucesso", "Operador atualizado")
            self._carregar()

        except Exception as e:
            show_error("Erro", f"Falha ao atualizar operador:\n{e}")

    # -------------------------------------------------------
    def _excluir(self):
        sel = self.lista.curselection()
        if not sel:
            show_error("Erro", "Selecione um operador!", parent=self.root)
            return

        item = self.lista.get(sel[0])
        op_id = int(item.split(" - ")[0])

        if not messagebox.askyesno("Confirmar",
                                   "Excluir operador?",
                                   parent=self.root):
            return

        try:
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM operadores WHERE id=?", (op_id,))
            conn.commit()
            conn.close()

            show_info("OK", "Operador excluído")
            self._carregar()

        except Exception as e:
            show_error("Erro", f"Falha ao excluir operador:\n{e}")
