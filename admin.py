# admin.py
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from PIL import Image, ImageTk
import os
import database as db
from utils import centralizar_janela, criar_rodape, show_error, show_info


class AdminApp:
    def __init__(self, root, voltar=None):
        db.criar_tabelas()
        self.root = root
        self.voltar = voltar
        self.root.title("Motherson Taubaté - Administração")
        centralizar_janela(root, 800, 600)
        self.rodape = None
        self.abrir_tela_principal()

    # ---------------------------------------------------------
    def limpar_tela(self):
        for w in self.root.winfo_children():
            if self.rodape and w == self.rodape:
                continue
            w.destroy()

    # ---------------------------------------------------------
    # TELA PRINCIPAL
    # ---------------------------------------------------------
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

        ttk.Button(btn_frame, text="Gerenciar Avaliadores", width=20,
                   command=self.tela_avaliadores).grid(row=0, column=2, padx=6, pady=6)

        ttk.Button(btn_frame, text="Resultados", width=20,
                   command=self.tela_resultados).grid(row=1, column=0, padx=6, pady=6)

        ttk.Button(btn_frame, text="Importar Banco (.db)", width=20,
                   command=self.importar_banco).grid(row=1, column=1, padx=6, pady=6)

        ttk.Button(btn_frame, text="Exportar Banco (.db)", width=20,
                   command=self.exportar_banco).grid(row=1, column=2, padx=6, pady=6)

        if self.voltar:
            ttk.Button(self.root, text="Voltar",
                       command=self.voltar).pack(pady=8)

        if self.rodape:
            try:
                self.rodape.destroy()
            except:
                pass
        self.rodape, _ = criar_rodape(self.root)

    # ---------------------------------------------------------
    # CRUD TESTES (agora com Editar / Excluir)
    # ---------------------------------------------------------
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
        ttk.Button(btns, text="Editar Teste", command=self.editar_teste).grid(
            row=0, column=3, padx=6)
        ttk.Button(btns, text="Excluir Teste", command=self.excluir_teste).grid(
            row=0, column=4, padx=6)
        ttk.Button(btns, text="Voltar", command=self.abrir_tela_principal).grid(
            row=0, column=5, padx=6)

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
        nome = simpledialog.askstring(
            "Nome do Teste", "Nome:", parent=self.root)
        self.root.update()
        if not nome:
            return
        desc = simpledialog.askstring(
            "Descrição", "Descrição (opcional):", parent=self.root)
        self.root.update()
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

    def editar_teste(self):
        sel = self.lista_testes.curselection()
        if not sel:
            show_error("Erro", "Selecione um teste!", parent=self.root)
            return
        item = self.lista_testes.get(sel[0])
        teste_id = int(item.split(" - ", 1)[0])

        # buscar dados atuais
        conn = db.conectar()
        cur = conn.cursor()
        cur.execute(
            "SELECT nome, descricao FROM testes WHERE id=?", (teste_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            show_error("Erro", "Teste não encontrado.", parent=self.root)
            return
        nome_atual, desc_atual = row

        novo_nome = simpledialog.askstring(
            "Editar Nome", "Nome:", initialvalue=nome_atual, parent=self.root)
        self.root.update()
        if not novo_nome:
            return
        nova_desc = simpledialog.askstring(
            "Editar Descrição", "Descrição:", initialvalue=desc_atual or "", parent=self.root)
        self.root.update()
        conn = db.conectar()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE testes SET nome=?, descricao=? WHERE id=?",
                        (novo_nome, nova_desc, teste_id))
            conn.commit()
            show_info("Sucesso", "Teste atualizado")
            self.carregar_testes()
        except Exception as e:
            show_error("Erro", f"Falha ao atualizar: {e}")
        finally:
            conn.close()

    def excluir_teste(self):
        sel = self.lista_testes.curselection()
        if not sel:
            show_error("Erro", "Selecione um teste!", parent=self.root)
            return
        item = self.lista_testes.get(sel[0])
        teste_id = int(item.split(" - ", 1)[0])
        if not messagebox.askyesno("Confirmar", "Excluir teste e todas as imagens?", parent=self.root):
            return
        conn = db.conectar()
        cur = conn.cursor()
        cur.execute("DELETE FROM testes WHERE id=?", (teste_id,))
        conn.commit()
        conn.close()
        show_info("OK", "Teste excluído")
        self.carregar_testes()

    def adicionar_imagem(self):
        sel = self.lista_testes.curselection()
        if not sel:
            show_error("Erro", "Selecione um teste!", parent=self.root)
            return
        item = self.lista_testes.get(sel[0])
        teste_id = int(item.split(" - ", 1)[0])

        arquivo = filedialog.askopenfilename(title="Selecione imagem", filetypes=[
                                             ("Imagens", "*.png;*.jpg;*.jpeg")], parent=self.root)
        if not arquivo:
            return
        resp = messagebox.askquestion(
            "Resposta correta", "Esta imagem é OK?", parent=self.root)
        resposta = "OK" if resp == "yes" else "NOK"
        try:
            db.adicionar_imagem(teste_id, arquivo, resposta)
            show_info("Sucesso", "Imagem adicionada")
        except Exception as e:
            show_error("Erro", f"Falha ao adicionar imagem: {e}")

    def gerenciar_imagens(self):
        sel = self.lista_testes.curselection()
        if not sel:
            show_error("Erro", "Selecione um teste!", parent=self.root)
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
            if not messagebox.askyesno("Confirmar", "Excluir imagem?", parent=jan):
                return
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM imagens WHERE id=?", (img_id,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Ok", "Excluída", parent=jan)
            jan.destroy()

        ttk.Button(frame, text="Excluir", command=excluir).pack(pady=6)

    # ---------------------------------------------------------
    # CRUD OPERADORES (COM FIX NO FOCUS)
    # ---------------------------------------------------------
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

        btns = tk.Frame(self.root)
        btns.pack(pady=10)

        ttk.Button(btns, text="Novo Operador", command=self.novo_operador).grid(
            row=0, column=0, padx=6)
        ttk.Button(btns, text="Editar", command=self.editar_operador).grid(
            row=0, column=1, padx=6)
        ttk.Button(btns, text="Excluir", command=self.excluir_operador).grid(
            row=0, column=2, padx=6)
        ttk.Button(btns, text="Voltar", command=self.abrir_tela_principal).grid(
            row=0, column=3, padx=6)

        self.carregar_operadores()

    def carregar_operadores(self):
        self.lb_ops.delete(0, tk.END)
        for id, nome, mat, turno in db.listar_operadores():
            self.lb_ops.insert(tk.END, f"{id} - {nome} | {mat} | {turno}")

    def novo_operador(self):
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
        turno = simpledialog.askstring("Turno", f"Informe o turno ({', '.join(turnos)}):", parent=self.root) if turnos else simpledialog.askstring(
            "Turno", "Turno:", parent=self.root)
        self.root.update()
        if not turno:
            return
        db.garantir_operador(nome, mat, turno)
        show_info("Sucesso", "Operador cadastrado")
        self.carregar_operadores()

    def editar_operador(self):
        sel = self.lb_ops.curselection()
        if not sel:
            show_error("Erro", "Selecione um operador!", parent=self.root)
            return

        item = self.lb_ops.get(sel[0])
        op_id = int(item.split(" - ")[0])

        # obter dados do DB com tolerância ao formato retornado
        dados = db.obter_dados_operador(op_id)
        # dados pode ser (nome, matricula, turno) ou (id, nome, matricula, turno)
        if not dados:
            show_error("Erro", "Operador não encontrado.", parent=self.root)
            return
        if len(dados) == 3:
            nome_atual, mat_atual, turno_atual = dados
        elif len(dados) == 4:
            _, nome_atual, mat_atual, turno_atual = dados
        else:
            # fallback
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
        novo_turno = simpledialog.askstring("Editar Turno", f"Informe o turno ({', '.join(turnos)}):", initialvalue=turno_atual, parent=self.root) if turnos else simpledialog.askstring(
            "Editar Turno", "Turno:", initialvalue=turno_atual, parent=self.root)
        self.root.update()

        conn = db.conectar()
        cur = conn.cursor()
        cur.execute("UPDATE operadores SET nome=?, matricula=?, turno=? WHERE id=?",
                    (novo_nome, nova_mat, novo_turno, op_id))
        conn.commit()
        conn.close()

        show_info("Sucesso", "Operador atualizado")
        self.carregar_operadores()

    def excluir_operador(self):
        sel = self.lb_ops.curselection()
        if not sel:
            show_error("Erro", "Selecione um operador!", parent=self.root)
            return

        item = self.lb_ops.get(sel[0])
        op_id = int(item.split(" - ")[0])

        if not messagebox.askyesno("Confirmar", "Excluir operador?", parent=self.root):
            return

        conn = db.conectar()
        cur = conn.cursor()
        cur.execute("DELETE FROM operadores WHERE id=?", (op_id,))
        conn.commit()
        conn.close()

        show_info("OK", "Operador excluído")
        self.carregar_operadores()

    # ---------------------------------------------------------
    # CRUD AVALIADORES
    # ---------------------------------------------------------
    def tela_avaliadores(self):
        self.limpar_tela()

        tk.Label(self.root, text="Avaliadores",
                 font=("Arial", 14)).pack(pady=6)

        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.lb_avals = tk.Listbox(frame)
        self.lb_avals.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(frame, command=self.lb_avals.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        self.lb_avals.config(yscrollcommand=sb.set)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Novo Avaliador",
                   command=self.novo_avaliador).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text="Editar", command=self.editar_avaliador).grid(
            row=0, column=1, padx=6)
        ttk.Button(btn_frame, text="Excluir", command=self.excluir_avaliador).grid(
            row=0, column=2, padx=6)
        ttk.Button(btn_frame, text="Voltar", command=self.abrir_tela_principal).grid(
            row=0, column=3, padx=6)

        self.carregar_avaliadores()

    def carregar_avaliadores(self):
        self.lb_avals.delete(0, tk.END)
        for a in db.listar_avaliadores():
            self.lb_avals.insert(tk.END, a)

    def novo_avaliador(self):
        nome = simpledialog.askstring(
            "Novo Avaliador", "Nome:", parent=self.root)
        self.root.update()
        if not nome:
            return
        db.garantir_avaliador(nome)
        show_info("OK", "Avaliador cadastrado")
        self.carregar_avaliadores()

    def editar_avaliador(self):
        sel = self.lb_avals.curselection()
        if not sel:
            show_error("Erro", "Selecione um avaliador!", parent=self.root)
            return

        nome_atual = self.lb_avals.get(sel[0])
        novo_nome = simpledialog.askstring(
            "Editar Avaliador", "Nome:", initialvalue=nome_atual, parent=self.root)
        self.root.update()
        if not novo_nome:
            return

        conn = db.conectar()
        cur = conn.cursor()
        cur.execute("UPDATE avaliadores SET nome=? WHERE nome=?",
                    (novo_nome, nome_atual))
        conn.commit()
        conn.close()

        show_info("Sucesso", "Avaliador atualizado")
        self.carregar_avaliadores()

    def excluir_avaliador(self):
        sel = self.lb_avals.curselection()
        if not sel:
            show_error("Erro", "Selecione um avaliador!", parent=self.root)
            return

        nome = self.lb_avals.get(sel[0])
        if not messagebox.askyesno("Confirmar", "Excluir avaliador?", parent=self.root):
            return

        conn = db.conectar()
        cur = conn.cursor()
        cur.execute("DELETE FROM avaliadores WHERE nome=?", (nome,))
        conn.commit()
        conn.close()

        show_info("OK", "Avaliador excluído")
        self.carregar_avaliadores()

    # ---------------------------------------------------------
    # RESULTADOS
    # ---------------------------------------------------------
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
            # r should be consistent with your DB schema; adjust if needed
            tree.insert("", tk.END, values=(
                r[0], r[2], r[3], r[5], r[6], r[7], r[8], f"{r[9]:.2f}" if r[9] is not None else "", r[10], r[11]))

        ttk.Button(self.root, text="Voltar",
                   command=self.abrir_tela_principal).pack(pady=6)

    # ---------------------------------------------------------
    # IMPORT / EXPORT DB
    # ---------------------------------------------------------
    def exportar_banco(self):
        destino = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[
                                               ("SQLite DB", "*.db")], parent=self.root)
        if not destino:
            return
        try:
            db.exportar_banco(destino)
            show_info("Exportado", f"Banco exportado para:\n{destino}")
        except Exception as e:
            show_error("Erro", f"Falha ao exportar: {e}")

    def importar_banco(self):
        arquivo = filedialog.askopenfilename(
            filetypes=[("SQLite DB", "*.db")], parent=self.root)
        if not arquivo:
            return
        try:
            db.importar_banco(arquivo, substituir=True)
            show_info("Importado", "Banco importado. Reinicie o programa.")
        except Exception as e:
            show_error("Erro", f"Falha: {e}")
