# admin_views/testes_admin.py
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog, ttk
from PIL import Image, ImageTk
import database as db
from utils import show_info, show_error, centralizar_janela


class TestesAdmin:
    def __init__(self, root, voltar_callback):
        self.root = root
        self.voltar_callback = voltar_callback
        self.frame = tk.Frame(self.root)

        self.montar_tela()

    # ---------------------------------------------------------
    def montar_tela(self):
        for w in self.root.winfo_children():
            w.destroy()

        tk.Label(self.root, text="Testes Cadastrados",
                 font=("Arial", 14)).pack(pady=6)

        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.lista = tk.Listbox(frame)
        self.lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(frame, command=self.lista.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        self.lista.config(yscrollcommand=sb.set)

        btns = tk.Frame(self.root)
        btns.pack(pady=6)

        ttk.Button(btns, text="Novo Teste",
                   command=self.novo_teste).grid(row=0, column=0, padx=6)

        ttk.Button(btns, text="Editar",
                   command=self.editar_teste).grid(row=0, column=1, padx=6)

        ttk.Button(btns, text="Excluir",
                   command=self.excluir_teste).grid(row=0, column=2, padx=6)

        ttk.Button(btns, text="Adicionar Imagem",
                   command=self.adicionar_imagem).grid(row=0, column=3, padx=6)

        ttk.Button(btns, text="Gerenciar Imagens",
                   command=self.gerenciar_imagens).grid(row=0, column=4, padx=6)

        ttk.Button(btns, text="Voltar",
                   command=self.voltar_callback).grid(row=0, column=5, padx=6)

        self.carregar_testes()

    # ---------------------------------------------------------
    def carregar_testes(self):
        self.lista.delete(0, tk.END)
        conn = db.conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, nome, descricao FROM testes ORDER BY nome")
        for r in cur.fetchall():
            self.lista.insert(tk.END, f"{r[0]} - {r[1]} - {r[2] or ''}")
        conn.close()

    # ---------------------------------------------------------
    def novo_teste(self):
        nome = simpledialog.askstring(
            "Nome do Teste", "Nome:", parent=self.root)
        if not nome:
            return

        desc = simpledialog.askstring(
            "Descrição", "Descrição (opcional):", parent=self.root)

        try:
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("INSERT INTO testes (nome, descricao) VALUES (?, ?)",
                        (nome, desc))
            conn.commit()
            conn.close()
            show_info("Sucesso", "Teste criado!")
            self.carregar_testes()
        except Exception as e:
            show_error("Erro", f"Erro ao criar teste: {e}")

    # ---------------------------------------------------------
    def editar_teste(self):
        sel = self.lista.curselection()
        if not sel:
            show_error("Erro", "Selecione um teste!")
            return

        item = self.lista.get(sel[0])
        teste_id = int(item.split(" - ")[0])

        conn = db.conectar()
        cur = conn.cursor()
        cur.execute(
            "SELECT nome, descricao FROM testes WHERE id=?", (teste_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            show_error("Erro", "Teste não encontrado!")
            return

        novo_nome = simpledialog.askstring(
            "Editar Teste", "Nome:", initialvalue=row[0], parent=self.root)

        if not novo_nome:
            return

        nova_desc = simpledialog.askstring(
            "Descrição", "Descrição:", initialvalue=row[1] or "", parent=self.root)

        try:
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("UPDATE testes SET nome=?, descricao=? WHERE id=?",
                        (novo_nome, nova_desc, teste_id))
            conn.commit()
            conn.close()
            show_info("Sucesso", "Teste atualizado!")
            self.carregar_testes()
        except Exception as e:
            show_error("Erro", f"Erro ao atualizar: {e}")

    # ---------------------------------------------------------
    def excluir_teste(self):
        sel = self.lista.curselection()
        if not sel:
            show_error("Erro", "Selecione um teste!")
            return

        item = self.lista.get(sel[0])
        teste_id = int(item.split(" - ")[0])

        if not messagebox.askyesno("Confirmar", "Excluir teste e imagens associadas?"):
            return

        try:
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM testes WHERE id=?", (teste_id,))
            conn.commit()
            conn.close()
            show_info("OK", "Teste excluído!")
            self.carregar_testes()
        except Exception as e:
            show_error("Erro", f"Erro ao excluir teste: {e}")

    # ---------------------------------------------------------
    def adicionar_imagem(self):
        sel = self.lista.curselection()
        if not sel:
            show_error("Erro", "Selecione um teste!")
            return

        item = self.lista.get(sel[0])
        teste_id = int(item.split(" - ")[0])

        arquivo = filedialog.askopenfilename(
            title="Selecione uma imagem",
            filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")],
            parent=self.root
        )
        if not arquivo:
            return

        resp = messagebox.askquestion("Resposta correta", "Esta imagem é OK?")
        resposta = "OK" if resp == "yes" else "NOK"

        try:
            db.adicionar_imagem(teste_id, arquivo, resposta)
            show_info("Sucesso", "Imagem adicionada!")
        except Exception as e:
            show_error("Erro", f"Erro ao adicionar imagem: {e}")

    # ---------------------------------------------------------
    def gerenciar_imagens(self):
        sel = self.lista.curselection()
        if not sel:
            show_error("Erro", "Selecione um teste!")
            return

        item = self.lista.get(sel[0])
        teste_id = int(item.split(" - ")[0])
        nome_teste = item.split(" - ")[1]

        from admin_views.imagens_admin import ImagensAdmin
        ImagensAdmin(self.root, teste_id, nome_teste, self.montar_tela)
