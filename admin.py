import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk

from database import conectar, criar_tabelas, adicionar_imagem, listar_imagens, extrair_imagem_temp
from utils import centralizar_janela, criar_rodape, show_error, show_info


class AdminApp:
    def __init__(self, root, voltar=None):
        criar_tabelas()
        self.root = root
        self.voltar = voltar
        self.rodape_frame = None  # Controle do rodapé
        self.root.title("Motherson Taubaté - Administração")
        centralizar_janela(root, 700, 500)
        self.abrir_tela_admin()

    def limpar_tela(self):
        for widget in self.root.winfo_children():
            if widget != self.rodape_frame:  # mantém o rodapé
                widget.destroy()

    import tkinter as tk


class AdminApp:
    def __init__(self, root, voltar=None):
        criar_tabelas()
        self.root = root
        self.voltar = voltar
        self.root.title("Motherson Taubaté - Administração")
        centralizar_janela(root, 700, 500)

        # Cria o rodapé uma única vez
        self.rodape_frame = criar_rodape(self.root)

        # Abre a tela admin
        self.abrir_tela_admin()

    def limpar_tela(self):
        # Remove todos os widgets, exceto o rodapé
        for widget in self.root.winfo_children():
            if widget != self.rodape_frame:
                widget.destroy()

    def abrir_tela_admin(self):
        self.limpar_tela()

        # Campos para cadastro de teste
        tk.Label(self.root, text="Nome do teste:").pack()
        self.entry_nome = tk.Entry(self.root)
        self.entry_nome.pack()

        tk.Label(self.root, text="Descrição:").pack()
        self.entry_desc = tk.Entry(self.root)
        self.entry_desc.pack()

        tk.Button(self.root, text="Salvar Teste",
                  command=self.salvar_teste).pack(pady=5)

        # Lista de testes
        tk.Label(self.root, text="Testes cadastrados:").pack()
        self.lista_testes = tk.Listbox(self.root)
        self.lista_testes.pack(fill=tk.BOTH, expand=True)

        # Botões de ação
        frame_botoes = tk.Frame(self.root)
        frame_botoes.pack(pady=5)

        tk.Button(frame_botoes, text="Adicionar Imagem",
                  command=self.adicionar_imagem).grid(row=0, column=0, padx=5)
        tk.Button(frame_botoes, text="Gerenciar Imagens",
                  command=self.abrir_janela_gerenciar_imagens).grid(row=0, column=1, padx=5)
        tk.Button(frame_botoes, text="Editar Teste",
                  command=self.editar_teste).grid(row=0, column=2, padx=5)
        tk.Button(frame_botoes, text="Excluir Teste",
                  command=self.deletar_teste).grid(row=0, column=3, padx=5)

        if self.voltar:
            tk.Button(self.root, text="Voltar", fg="red",
                      command=self.voltar).pack(pady=5)

        self.carregar_testes()

        # Cria rodapé se ainda não existir
        if self.rodape_frame is None:
            self.rodape_frame = criar_rodape(self.root)

    def salvar_teste(self):
        nome = self.entry_nome.get().strip()
        descricao = self.entry_desc.get().strip()
        if not nome:
            show_error("Erro", "O nome do teste é obrigatório!")
            return
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO testes (nome, descricao) VALUES (?, ?)", (nome, descricao))
            conn.commit()
            show_info("Sucesso", "Teste cadastrado!")
            self.entry_nome.delete(0, tk.END)
            self.entry_desc.delete(0, tk.END)
            self.carregar_testes()
        except Exception:
            show_error("Erro", "Já existe um teste com esse nome!")
        finally:
            conn.close()

    def carregar_testes(self):
        self.lista_testes.delete(0, tk.END)
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, descricao FROM testes ORDER BY nome")
        for row in cursor.fetchall():
            self.lista_testes.insert(
                tk.END, f"{row[0]} - {row[1]} - {row[2] or ''}")
        conn.close()

    def adicionar_imagem(self):
        selecao = self.lista_testes.curselection()
        if not selecao:
            show_error("Erro", "Selecione um teste!")
            return

        item = self.lista_testes.get(selecao[0])
        teste_id = int(item.split(" - ", 1)[0])

        arquivo = filedialog.askopenfilename(
            title="Selecione uma imagem", filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
        if not arquivo:
            return

        resp = messagebox.askquestion("Resposta Correta", "Essa imagem é OK?")
        resposta_correta = "OK" if resp == "yes" else "NOK"

        try:
            adicionar_imagem(teste_id, arquivo, resposta_correta)
            show_info("Sucesso", "Imagem adicionada ao banco!")
        except Exception as e:
            show_error("Erro", f"Erro ao salvar imagem: {e}")

    def editar_teste(self):
        selecao = self.lista_testes.curselection()
        if not selecao:
            show_error("Erro", "Selecione um teste para editar!")
            return

        item = self.lista_testes.get(selecao[0])
        teste_id, nome_atual, desc_atual = item.split(" - ", 2)
        novo_nome = simpledialog.askstring(
            "Editar Nome", "Novo nome do teste:", initialvalue=nome_atual)
        if not novo_nome:
            return
        nova_desc = simpledialog.askstring(
            "Editar Descrição", "Nova descrição:", initialvalue=desc_atual)
        if nova_desc is None:
            return

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE testes SET nome=?, descricao=? WHERE id=?",
                           (novo_nome, nova_desc, int(teste_id)))
            conn.commit()
            show_info("Sucesso", "Teste atualizado!")
            self.carregar_testes()
        except Exception:
            show_error("Erro", "Já existe um teste com esse nome!")
        finally:
            conn.close()

    def deletar_teste(self):
        selecao = self.lista_testes.curselection()
        if not selecao:
            show_error("Erro", "Selecione um teste!")
            return

        item = self.lista_testes.get(selecao[0])
        teste_id, nome_teste, _ = item.split(" - ", 2)
        confirmar = messagebox.askyesno(
            "Confirmar Exclusão", f"Deseja excluir o teste '{nome_teste}' e suas imagens?")
        if not confirmar:
            return

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM testes WHERE id=?", (int(teste_id),))
        conn.commit()
        conn.close()
        show_info("Sucesso", "Teste excluído!")
        self.carregar_testes()

    def abrir_janela_gerenciar_imagens(self):
        selecao = self.lista_testes.curselection()
        if not selecao:
            show_error("Erro", "Selecione um teste para gerenciar imagens!")
            return

        item = self.lista_testes.get(selecao[0])
        teste_id, teste_nome, _ = item.split(" - ", 2)

        janela = tk.Toplevel(self.root)
        janela.title(f"Gerenciar Imagens - {teste_nome}")
        centralizar_janela(janela, 750, 500)

        lista = tk.Listbox(janela)
        lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        frame = tk.Frame(janela)
        frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        canvas = tk.Canvas(frame, width=400, height=300,
                           bd=2, relief=tk.SUNKEN)
        canvas.pack(pady=10)
        imagens_cache = {}

        def carregar():
            lista.delete(0, tk.END)
            imagens = listar_imagens(int(teste_id))
            for img_id, nome, resp in imagens:
                lista.insert(tk.END, f"{img_id} - {nome} - {resp}")
            return imagens

        imagens = carregar()

        def mostrar_preview(event=None):
            selecionado = lista.curselection()
            if not selecionado:
                return
            index = selecionado[0]
            img_id, nome, resp = imagens[index]
            caminho_temp = extrair_imagem_temp(img_id)
            if not caminho_temp:
                return
            img = Image.open(caminho_temp)
            img = img.resize((400, 300), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            imagens_cache["preview"] = img_tk
            canvas.delete("all")
            canvas.create_image(0, 0, anchor=tk.NW, image=img_tk)
            canvas.image = img_tk

        lista.bind("<<ListboxSelect>>", mostrar_preview)

        def excluir():
            selecionado = lista.curselection()
            if not selecionado:
                show_error("Erro", "Selecione uma imagem!")
                return
            index = selecionado[0]
            img_id, _, _ = imagens[index]
            if not messagebox.askyesno("Confirmação", "Excluir esta imagem?"):
                return
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM imagens WHERE id=?", (img_id,))
            conn.commit()
            conn.close()
            show_info("Sucesso", "Imagem excluída!")
            imagens[:] = carregar()

        def editar_resposta():
            selecionado = lista.curselection()
            if not selecionado:
                show_error("Erro", "Selecione uma imagem!")
                return
            index = selecionado[0]
            img_id, _, resp_atual = imagens[index]
            nova_resp = "OK" if messagebox.askyesno(
                "Editar", "Definir resposta como OK? (Não = NOK)") else "NOK"
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE imagens SET resposta_correta=? WHERE id=?", (nova_resp, img_id))
            conn.commit()
            conn.close()
            show_info("Sucesso", "Resposta atualizada!")
            imagens[:] = carregar()

        tk.Button(frame, text="Editar Resposta",
                  command=editar_resposta).pack(pady=5)
        tk.Button(frame, text="Excluir Imagem", command=excluir).pack(pady=5)
