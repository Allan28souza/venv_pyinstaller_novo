# admin.py (corrigido para resource_path)
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import shutil
import os
import sqlite3
import sys

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors

from database import conectar, criar_tabelas, resource_path, get_db_path

# Caminho da pasta de imagens, adaptável para executável
PASTA_IMAGENS = resource_path("imagens")


def centralizar_janela(janela, largura, altura):
    janela.update_idletasks()
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    janela.geometry(f"{largura}x{altura}+{x}+{y}")


class AdminApp:
    def __init__(self, root, voltar=None):
        criar_tabelas()
        self.root = root
        self.voltar = voltar
        centralizar_janela(root, 650, 500)

        # Widgets de cadastro de teste
        tk.Label(root, text="Nome do teste:").pack()
        self.entry_nome = tk.Entry(root)
        self.entry_nome.pack()

        tk.Label(root, text="Descrição:").pack()
        self.entry_desc = tk.Entry(root)
        self.entry_desc.pack()

        tk.Button(root, text="Salvar Teste",
                  command=self.salvar_teste).pack(pady=5)

        # Lista de testes
        tk.Label(root, text="Testes cadastrados:").pack()
        self.lista_testes = tk.Listbox(root)
        self.lista_testes.pack(fill=tk.BOTH, expand=True)

        # Botões de ação
        frame_botoes = tk.Frame(root)
        frame_botoes.pack(pady=5)

        self.btn_adicionar_img = tk.Button(
            frame_botoes, text="Adicionar Imagem", command=self.adicionar_imagem)
        self.btn_adicionar_img.grid(row=0, column=0, padx=5)

        self.btn_editar = tk.Button(
            frame_botoes, text="Editar Teste", command=self.editar_teste)
        self.btn_editar.grid(row=0, column=1, padx=5)

        self.btn_deletar = tk.Button(
            frame_botoes, text="Excluir Teste", command=self.deletar_teste)
        self.btn_deletar.grid(row=0, column=2, padx=5)

        self.btn_gerenciar_img = tk.Button(
            frame_botoes, text="Gerenciar Imagens", command=self.abrir_janela_gerenciar_imagens)
        self.btn_gerenciar_img.grid(row=0, column=3, padx=5)

        # Botão Voltar
        if self.voltar:
            tk.Button(root, text="Voltar", fg="red",
                      command=self.voltar).pack(pady=5)

        self.carregar_testes()

    def salvar_teste(self):
        nome = self.entry_nome.get().strip()
        descricao = self.entry_desc.get().strip()
        if not nome:
            messagebox.showerror("Erro", "O nome do teste é obrigatório!")
            return
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO testes (nome, descricao) VALUES (?, ?)", (nome, descricao))
            conn.commit()
            os.makedirs(os.path.join(PASTA_IMAGENS, nome), exist_ok=True)
            messagebox.showinfo("Sucesso", "Teste cadastrado!")
            self.entry_nome.delete(0, tk.END)
            self.entry_desc.delete(0, tk.END)
            self.carregar_testes()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Já existe um teste com esse nome!")
        finally:
            conn.close()

    def carregar_testes(self):
        self.lista_testes.delete(0, tk.END)
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, descricao FROM testes ORDER BY nome")
        for row in cursor.fetchall():
            self.lista_testes.insert(tk.END, f"{row[0]} - {row[1]} - {row[2]}")
        conn.close()

    def adicionar_imagem(self):
        selecao = self.lista_testes.curselection()
        if not selecao:
            messagebox.showerror("Erro", "Selecione um teste!")
            return
        item = self.lista_testes.get(selecao[0])
        teste_id, teste_nome, _ = item.split(" - ", 2)
        arquivo = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
        if not arquivo:
            return
        resp = messagebox.askquestion("Resposta Correta", "Essa imagem é OK?")
        resposta_correta = "OK" if resp == "yes" else "NOK"
        pasta_destino = os.path.join(PASTA_IMAGENS, teste_nome)
        os.makedirs(pasta_destino, exist_ok=True)
        destino = os.path.join(pasta_destino, os.path.basename(arquivo))
        try:
            shutil.copy(arquivo, destino)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao copiar a imagem: {e}")
            return
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO imagens (teste_id, caminho, resposta_correta) VALUES (?, ?, ?)",
                       (int(teste_id), destino, resposta_correta))
        conn.commit()
        conn.close()
        messagebox.showinfo("Sucesso", "Imagem adicionada!")

    def editar_teste(self):
        selecao = self.lista_testes.curselection()
        if not selecao:
            messagebox.showerror("Erro", "Selecione um teste para editar!")
            return
        item = self.lista_testes.get(selecao[0])
        teste_id, nome_atual, descricao_atual = item.split(" - ", 2)
        novo_nome = simpledialog.askstring(
            "Editar Nome", "Novo nome do teste:", initialvalue=nome_atual)
        if novo_nome is None or novo_nome.strip() == "":
            return
        nova_desc = simpledialog.askstring(
            "Editar Descrição", "Nova descrição do teste:", initialvalue=descricao_atual)
        if nova_desc is None:
            return
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE testes SET nome=?, descricao=? WHERE id=?",
                           (novo_nome, nova_desc, int(teste_id)))
            conn.commit()
            messagebox.showinfo("Sucesso", "Teste atualizado!")
            self.carregar_testes()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Já existe um teste com esse nome!")
        finally:
            conn.close()

    def deletar_teste(self):
        selecao = self.lista_testes.curselection()
        if not selecao:
            messagebox.showerror("Erro", "Selecione um teste para excluir!")
            return
        item = self.lista_testes.get(selecao[0])
        teste_id, nome_teste, _ = item.split(" - ", 2)
        confirmar = messagebox.askyesno(
            "Confirmar Exclusão", f"Deseja excluir o teste '{nome_teste}' e todas as imagens?")
        if not confirmar:
            return
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM imagens WHERE teste_id=?",
                       (int(teste_id),))
        cursor.execute("DELETE FROM testes WHERE id=?", (int(teste_id),))
        conn.commit()
        conn.close()
        pasta = os.path.join(PASTA_IMAGENS, nome_teste)
        if os.path.exists(pasta):
            try:
                shutil.rmtree(pasta)
            except Exception as e:
                messagebox.showwarning(
                    "Aviso", f"Erro ao apagar a pasta de imagens: {e}")
        messagebox.showinfo("Sucesso", "Teste excluído!")
        self.carregar_testes()

    def abrir_janela_gerenciar_imagens(self):
        selecao = self.lista_testes.curselection()
        if not selecao:
            messagebox.showerror(
                "Erro", "Selecione um teste para gerenciar as imagens!")
            return
        item = self.lista_testes.get(selecao[0])
        teste_id, teste_nome, _ = item.split(" - ", 2)
        janela_img = tk.Toplevel(self.root)
        janela_img.title(f"Gerenciar Imagens - {teste_nome}")
        centralizar_janela(janela_img, 700, 450)

        # Lista de imagens
        lista_img = tk.Listbox(janela_img)
        lista_img.pack(side=tk.LEFT, fill=tk.BOTH,
                       expand=True, padx=(10, 5), pady=10)

        frame_direita = tk.Frame(janela_img)
        frame_direita.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 10), pady=10)

        label_preview = tk.Label(frame_direita, text="Preview da Imagem")
        label_preview.pack()

        canvas_img = tk.Canvas(frame_direita, width=400,
                               height=300, bd=2, relief=tk.SUNKEN)
        canvas_img.pack(pady=10)
        imagens_tk = {}

        # Função para carregar imagens do banco
        def carregar_imagens():
            lista_img.delete(0, tk.END)
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, caminho, resposta_correta FROM imagens WHERE teste_id=?", (int(teste_id),))
            imgs = cursor.fetchall()
            conn.close()
            for img_id, caminho, resp in imgs:
                lista_img.insert(
                    tk.END, f"{img_id} - {os.path.basename(caminho)} - {resp}")
            return imgs

        imagens = carregar_imagens()

        # Preview da imagem selecionada
        def mostrar_preview(event=None):
            selecionado = lista_img.curselection()
            if not selecionado:
                canvas_img.delete("all")
                label_preview.config(text="Preview da Imagem")
                return
            index = selecionado[0]
            img_id, caminho, resp = imagens[index]
            try:
                img = Image.open(caminho)
                img = img.resize((400, 300), Image.LANCZOS)
                img_tk = ImageTk.PhotoImage(img)
                imagens_tk["img"] = img_tk
                canvas_img.delete("all")
                canvas_img.create_image(0, 0, anchor=tk.NW, image=img_tk)
                label_preview.config(text=f"Resposta correta: {resp}")
            except Exception as e:
                canvas_img.delete("all")
                label_preview.config(text=f"Erro ao carregar imagem: {e}")

        lista_img.bind("<<ListboxSelect>>", mostrar_preview)

        # Excluir imagem
        def excluir_imagem():
            nonlocal imagens
            selecionado = lista_img.curselection()
            if not selecionado:
                messagebox.showerror(
                    "Erro", "Selecione uma imagem para excluir!")
                return
            index = selecionado[0]
            img_id, caminho, _ = imagens[index]
            confirmar = messagebox.askyesno(
                "Confirmar Exclusão", "Deseja excluir esta imagem?")
            if not confirmar:
                return
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM imagens WHERE id=?", (img_id,))
            conn.commit()
            conn.close()
            if os.path.exists(caminho):
                os.remove(caminho)
            messagebox.showinfo("Sucesso", "Imagem excluída!")
            imagens = carregar_imagens()
            if imagens:
                novo_index = index if index < len(imagens) else len(imagens)-1
                lista_img.selection_set(novo_index)
                mostrar_preview()
            else:
                canvas_img.delete("all")
                label_preview.config(text="Preview da Imagem")

        # Editar resposta (OK/NOK)
        def editar_resposta():
            nonlocal imagens
            selecionado = lista_img.curselection()
            if not selecionado:
                messagebox.showerror(
                    "Erro", "Selecione uma imagem para editar!")
                return
            index = selecionado[0]
            img_id, caminho, resp_atual = imagens[index]
            nova = messagebox.askquestion(
                "Editar Resposta", "Definir resposta correta como OK? (Não = NOK)")
            nova_resp = "OK" if nova == "yes" else "NOK"
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("UPDATE imagens SET resposta_correta=? WHERE id=?",
                           (nova_resp, img_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Resposta atualizada!")
            imagens = carregar_imagens()
            lista_img.selection_set(index)
            mostrar_preview()

        # Botões
        btn_editar = tk.Button(
            frame_direita, text="Editar Resposta", width=20, command=editar_resposta)
        btn_editar.pack(pady=5)
        btn_excluir = tk.Button(
            frame_direita, text="Excluir Imagem", width=20, command=excluir_imagem)
        btn_excluir.pack(pady=5)
