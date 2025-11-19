# admin_views/imagens_admin.py
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import shutil

import database as db
from utils import centralizar_janela, show_info, show_error


class ImagensAdmin:
    """
    Janela para gerenciar imagens de um teste.
    """

    def __init__(self, root, teste_id, nome_teste, callback_voltar=None):
        self.root = root
        self.teste_id = teste_id
        self.nome_teste = nome_teste
        self.callback_voltar = callback_voltar

        # --- cria janela ---
        self.jan = tk.Toplevel(self.root)
        self.jan.title(f"Gerenciar imagens - {self.nome_teste}")
        centralizar_janela(self.jan, 820, 520)
        self.jan.transient(self.root)
        self.jan.grab_set()

        # dados
        self.imagens = []
        self._preview_imgtk = None

        # montar UI
        self._build_ui()
        self._carregar_imagens()

        # fechar corretamente
        self.jan.protocol("WM_DELETE_WINDOW", self._on_close)

    # --------------------------------------------------
    # interface gráfica
    # --------------------------------------------------
    def _build_ui(self):
        left = tk.Frame(self.jan)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)

        right = tk.Frame(self.jan)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=6, pady=6)

        # lista
        self.lista = tk.Listbox(left)
        self.lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(left, command=self.lista.yview)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        self.lista.config(yscrollcommand=sb.set)

        # preview
        self.canvas = tk.Canvas(
            right, width=420, height=320, bd=2, relief=tk.SUNKEN)
        self.canvas.pack()

        # botões
        btns = tk.Frame(right)
        btns.pack(pady=6, fill=tk.X)

        ttk.Button(btns, text="Atualizar lista",
                   command=self._carregar_imagens).pack(fill=tk.X, pady=3)

        ttk.Button(btns, text="Editar resposta",
                   command=self._editar_resposta).pack(fill=tk.X, pady=3)

        ttk.Button(btns, text="Excluir imagem",
                   command=self._excluir_imagem).pack(fill=tk.X, pady=3)

        ttk.Button(btns, text="Apagar TODAS",
                   command=self.apagar_todas_imagens).pack(fill=tk.X, pady=3)

        ttk.Button(btns, text="Renomear TODAS (Automático)",
                   command=self._renomear_todas_automatico).pack(fill=tk.X, pady=8)

        ttk.Button(btns, text="Fechar",
                   command=self._on_close).pack(fill=tk.X, pady=10)

        # evento ao clicar
        self.lista.bind("<<ListboxSelect>>", self._mostrar_imagem)

    # --------------------------------------------------
    def _carregar_imagens(self):
        self.lista.delete(0, tk.END)
        try:
            self.imagens = db.listar_imagens(self.teste_id)
        except Exception as e:
            show_error("Erro", f"Falha ao listar imagens: {e}")
            self.imagens = []

        for img in self.imagens:
            self.lista.insert(tk.END, f"{img[0]} - {img[1]} - {img[2]}")

        self.canvas.delete("all")
        self._preview_imgtk = None

    # --------------------------------------------------
    def _mostrar_imagem(self, event=None):
        sel = self.lista.curselection()
        if not sel:
            return

        idx = sel[0]
        row = self.imagens[idx]
        img_id = row[0]

        caminho = db.extrair_imagem_temp(img_id)
        if not caminho or not os.path.exists(caminho):
            show_error("Erro", f"Imagem não encontrada: {row[1]}")
            return

        try:
            img = Image.open(caminho)
            max_w, max_h = 420, 320
            w, h = img.size
            scale = min(max_w / w, max_h / h)
            img = img.resize((int(w * scale), int(h * scale)),
                             Image.Resampling.LANCZOS)

            imgtk = ImageTk.PhotoImage(img)
            self._preview_imgtk = imgtk
            self.canvas.delete("all")
            self.canvas.create_image(10, 10, anchor=tk.NW, image=imgtk)

        except Exception as e:
            show_error("Erro", f"Falha ao abrir imagem: {e}")

    # --------------------------------------------------
    def _editar_resposta(self):
        sel = self.lista.curselection()
        if not sel:
            show_error("Erro", "Selecione uma imagem!")
            return

        idx = sel[0]
        img_id, nome_arquivo, resposta_atual = self.imagens[idx]

        nova = messagebox.askquestion(
            "Resposta correta",
            f"Definir como OK? (Não = NOK)\nAtual: {resposta_atual}",
            parent=self.jan
        )
        nova_resp = "OK" if nova == "yes" else "NOK"

        try:
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute(
                "UPDATE imagens SET resposta_correta=? WHERE id=?",
                (nova_resp, img_id)
            )
            conn.commit()
            conn.close()

            show_info("Sucesso", "Resposta atualizada")
            self._carregar_imagens()

        except Exception as e:
            show_error("Erro", f"Erro ao atualizar: {e}")

    # --------------------------------------------------
    def _excluir_imagem(self):
        sel = self.lista.curselection()
        if not sel:
            show_error("Erro", "Selecione uma imagem!")
            return

        idx = sel[0]
        img_id, nome_arquivo, _ = self.imagens[idx]

        if not messagebox.askyesno(
            "Confirmar",
            f"Excluir imagem '{nome_arquivo}'?",
            parent=self.jan
        ):
            return

        try:
            # apagar DB
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM imagens WHERE id=?", (img_id,))
            conn.commit()
            conn.close()

            # apagar arquivo físico
            pasta = os.path.join("testes", str(self.teste_id))
            caminho = os.path.join(pasta, nome_arquivo)
            if os.path.exists(caminho):
                os.remove(caminho)

            show_info("OK", "Imagem excluída")
            self._carregar_imagens()

        except Exception as e:
            show_error("Erro", f"Falha ao excluir: {e}")

    # --------------------------------------------------
    def apagar_todas_imagens(self):
        if not messagebox.askyesno(
            "Confirmar",
            "Apagar TODAS as imagens deste teste?\n"
            "Atenção: isso remove também os arquivos do disco!"
        ):
            return

        try:
            # apagar DB
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("DELETE FROM imagens WHERE teste_id=?",
                        (self.teste_id,))
            conn.commit()
            conn.close()

            # apagar pasta do teste
            pasta = os.path.join("testes", str(self.teste_id))
            if os.path.exists(pasta):
                shutil.rmtree(pasta)

            show_info("Pronto", "Todas as imagens foram apagadas.")
            self._carregar_imagens()

        except Exception as e:
            show_error("Erro", f"Falha ao apagar imagens: {e}")

    # --------------------------------------------------
    def _renomear_todas_automatico(self):
        if not messagebox.askyesno(
            "Renomear Todas",
            "Deseja renomear TODAS as imagens automaticamente?\n"
            "O nome antigo será perdido."
        ):
            return

        pasta = os.path.join("testes", str(self.teste_id))
        os.makedirs(pasta, exist_ok=True)

        try:
            imagens = db.listar_imagens(self.teste_id)

            for img_id, nome_antigo, resp in imagens:
                ext = os.path.splitext(nome_antigo)[1].lower() or ".png"
                resp_txt = "OK" if resp.upper() == "OK" else "NOK"

                nome_teste_limpo = (
                    self.nome_teste.replace(" ", "_")
                    .replace("/", "_")
                    .replace("\\", "_")
                )

                novo_nome = f"{img_id}_IMG_{nome_teste_limpo}_{resp_txt}{ext}"

                old_path = os.path.join(pasta, nome_antigo)
                new_path = os.path.join(pasta, novo_nome)

                if os.path.exists(old_path):
                    os.rename(old_path, new_path)

                conn = db.conectar()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE imagens SET nome_arquivo=? WHERE id=?", (novo_nome, img_id))
                conn.commit()
                conn.close()

            show_info(
                "Sucesso", "Todas as imagens foram renomeadas automaticamente!")
            self._carregar_imagens()

        except Exception as e:
            show_error("Erro", f"Falha ao renomear imagens: {e}")

    # --------------------------------------------------
    def _on_close(self):
        try:
            self.jan.grab_release()
        except:
            pass

        try:
            self.jan.destroy()
        except:
            pass

        if callable(self.callback_voltar):
            self.callback_voltar()
