# admin.py
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk
import os
import database as db
from utils import centralizar_janela, criar_rodape, show_error, show_info, abrir_pasta


class AdminApp:
    def __init__(self, root, voltar=None):
        db.criar_tabelas()
        self.root = root
        self.voltar = voltar
        self.root.title("Motherson Taubaté - Administração")
        centralizar_janela(root, 800, 600)
        self.rodape = None
        self.abrir_tela_principal()

    def limpar_tela(self):
        for w in self.root.winfo_children():
            # preserva rodapé
            if self.rodape and w == self.rodape:
                continue
            w.destroy()

    def abrir_tela_principal(self):
        self.limpar_tela()
        tk.Label(self.root, text="Painel de Administração",
                 font=("Arial", 16, "bold")).pack(pady=10)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="Gerenciar Testes", width=20,
                   command=self.tela_testes).grid(row=0, column=0, padx=6, pady=6)
        ttk.Button(btn_frame, text="Gerenciar Operadores", width=20,
                   command=self.tela_operadores).grid(row=0, column=1, padx=6, pady=6)
        ttk.Button(btn_frame, text="Resultados", width=20,
                   command=self.tela_resultados).grid(row=0, column=2, padx=6, pady=6)
        ttk.Button(btn_frame, text="Importar Banco (.db)", width=20,
                   command=self.importar_banco).grid(row=1, column=0, padx=6, pady=6)
        ttk.Button(btn_frame, text="Exportar Banco (.db)", width=20,
                   command=self.exportar_banco).grid(row=1, column=1, padx=6, pady=6)

        if self.voltar:
            ttk.Button(self.root, text="Voltar",
                       command=self.voltar).pack(pady=8)
        if self.rodape:
            try:
                self.rodape.destroy()
            except:
                pass
        self.rodape, _ = criar_rodape(self.root)

    # ---------- Testes ----------
    def tela_testes(self):
        self.limpar_tela()
        tk.Label(self.root, text="Testes Cadastrados",
                 font=("Arial", 14)).pack(pady=6)
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.lista_testes = tk.Listbox(frame)
        self.lista_testes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = tk.Scrollbar(frame, command=self.lista_testes.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        self.lista_testes.config(yscrollcommand=sb.set)
        btns = tk.Frame(self.root)
        btns.pack(pady=6)
        ttk.Button(btns, text="Novo Teste", command=self.novo_teste).grid(
            row=0, column=0, padx=6)
        ttk.Button(btns, text="Adicionar Imagem",
                   command=self.adicionar_imagem).grid(row=0, column=1, padx=6)
        ttk.Button(btns, text="Gerenciar Imagens",
                   command=self.gerenciar_imagens).grid(row=0, column=2, padx=6)
        ttk.Button(btns, text="Voltar", command=self.abrir_tela_principal).grid(
            row=0, column=3, padx=6)
        self.carregar_testes()

    def carregar_testes(self):
        self.lista_testes.delete(0, tk.END)
        conn = db.conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, nome, descricao FROM testes ORDER BY nome")
        for r in cur.fetchall():
            self.lista_testes.insert(tk.END, f"{r[0]} - {r[1]} - {r[2] or ''}")
        conn.close()

    def novo_teste(self):
        nome = simpledialog.askstring("Nome do Teste", "Nome:")
        if not nome:
            return
        desc = simpledialog.askstring("Descrição", "Descrição (opcional):")
        conn = db.conectar()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO testes (nome, descricao) VALUES (?,?)", (nome, desc))
            conn.commit()
            show_info("Sucesso", "Teste criado")
            self.carregar_testes()
        except Exception as e:
            show_error("Erro", f"Não foi possível criar teste: {e}")
        finally:
            conn.close()

    def adicionar_imagem(self):
        sel = self.lista_testes.curselection()
        if not sel:
            show_error("Erro", "Selecione um teste!")
            return
        item = self.lista_testes.get(sel[0])
        teste_id = int(item.split(" - ", 1)[0])
        arquivo = filedialog.askopenfilename(title="Selecione imagem", filetypes=[
                                             ("Imagens", "*.png;*.jpg;*.jpeg")])
        if not arquivo:
            return
        resp = messagebox.askquestion("Resposta correta", "Esta imagem é OK?")
        resposta = "OK" if resp == "yes" else "NOK"
        try:
            db.adicionar_imagem(teste_id, arquivo, resposta)
            show_info("Sucesso", "Imagem adicionada")
        except Exception as e:
            show_error("Erro", f"Falha ao adicionar imagem: {e}")

    def gerenciar_imagens(self):
        sel = self.lista_testes.curselection()
        if not sel:
            show_error("Erro", "Selecione um teste!")
            return
        item = self.lista_testes.get(sel[0])
        teste_id, nome = int(item.split(" - ", 1)[0]), item.split(" - ", 1)[1]
        jan = tk.Toplevel(self.root)
        jan.title(f"Gerenciar imagens - {nome}")
        centralizar_janela(jan, 800, 500)
        lista = tk.Listbox(jan)
        lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)
        frame = tk.Frame(jan)
        frame.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)
        canvas = tk.Canvas(frame, width=400, height=300,
                           bd=2, relief=tk.SUNKEN)
        canvas.pack()
        imgs = db.listar_imagens(teste_id)
        for r in imgs:
            lista.insert(tk.END, f"{r[0]} - {r[1]} - {r[2]}")

        def mostrar(event=None):
            seli = lista.curselection()
            if not seli:
                return
            idx = seli[0]
            row = imgs[idx]
            caminho = db.extrair_imagem_temp(row[0])
            if caminho:
                img = Image.open(caminho)
                img = img.resize((400, 300), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(img)
                canvas.delete("all")
                canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                canvas.image = imgtk
        lista.bind("<<ListboxSelect>>", mostrar)

        def excluir():
            seli = lista.curselection()
            if not seli:
                return
            idx = seli[0]
            img_id = imgs[idx][0]
            if not messagebox.askyesno("Confirm", "Excluir imagem?"):
                return
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM imagens WHERE id=?", (img_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Ok", "Excluída")
            jan.destroy()
        ttk.Button(frame, text="Excluir", command=excluir).pack(pady=6)

    # ---------- Operadores ----------
    def tela_operadores(self):
        self.limpar_tela()
        tk.Label(self.root, text="Operadores", font=("Arial", 14)).pack(pady=6)
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.lb_ops = tk.Listbox(frame)
        self.lb_ops.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = tk.Scrollbar(frame, command=self.lb_ops.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        self.lb_ops.config(yscrollcommand=sb.set)
        ttk.Button(self.root, text="Novo Operador",
                   command=self.novo_operador).pack(pady=6)
        ttk.Button(self.root, text="Voltar",
                   command=self.abrir_tela_principal).pack(pady=6)
        self.carregar_operadores()

    def carregar_operadores(self):
        self.lb_ops.delete(0, tk.END)
        for id, nome, mat, turno in db.listar_operadores():
            self.lb_ops.insert(tk.END, f"{id} - {nome} | {mat} | {turno}")

    def novo_operador(self):
        nome = simpledialog.askstring("Nome", "Nome:")
        if not nome:
            return
        mat = simpledialog.askstring("Matrícula", "Matrícula:")
        if not mat:
            return
        turnos = db.listar_turnos()
        turno = turnos[0] if turnos else ""
        db.garantir_operador(nome, mat, turno)
        show_info("Sucesso", "Operador cadastrado")
        self.carregar_operadores()

    # ---------- Resultados ----------
    def tela_resultados(self):
        self.limpar_tela()
        tk.Label(self.root, text="Resultados", font=("Arial", 14)).pack(pady=6)
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        cols = ("ID", "Operador", "Matr.", "Teste", "Avaliador",
                "Acertos", "Total", "%", "Data", "TempoTotal(s)")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for c in cols:
            tree.heading(c, text=c)
        tree.pack(fill=tk.BOTH, expand=True)
        resultados = db.listar_resultados()
        for r in resultados:
            tree.insert("", tk.END, values=(
                r[0], r[2], r[3], r[5], r[6], r[7], r[8], f"{r[9]:.2f}" if r[9] else "", r[10], r[11] or ""))
        ttk.Button(self.root, text="Voltar",
                   command=self.abrir_tela_principal).pack(pady=6)

    # ---------- Import / Export ----------
    def exportar_banco(self):
        destino = filedialog.asksaveasfilename(
            defaultextension=".db", filetypes=[("SQLite DB", "*.db")])
        if not destino:
            return
        try:
            db.exportar_banco(destino)
            show_info("Exportado", f"Banco exportado para:\n{destino}")
        except Exception as e:
            show_error("Erro", f"Falha exportar DB: {e}")

    def importar_banco(self):
        arquivo = filedialog.askopenfilename(filetypes=[("SQLite DB", "*.db")])
        if not arquivo:
            return
        try:
            db.importar_banco(arquivo, substituir=True)
            show_info(
                "Importado", "Banco importado com sucesso. Reinicie a aplicação.")
        except Exception as e:
            show_error("Erro", f"Falha ao importar DB: {e}")
