# executar_teste.py (compatível com banco interno)
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import pandas as pd
import os
import subprocess
import platform
from datetime import datetime
from io import BytesIO

from database import conectar, criar_tabelas

NUM_QUESTOES = 10  # Número de questões por teste


def gerar_pdf(nome_usuario, matricula, turno, acertos, porcentagem, erros_imagens, pasta_resultados=None, avaliador=None):
    """
    erros_imagens: lista de tuples (nome_arquivo, resposta_usuario, resposta_correta, imagem_blob_bytes)
    """
    if pasta_resultados is None:
        pasta_resultados = os.path.join(os.path.abspath("."), "resultados")
    os.makedirs(pasta_resultados, exist_ok=True)

    arquivo_pdf = os.path.join(
        pasta_resultados,
        f"resultado_{nome_usuario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    largura, altura = A4

    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, altura - 2 * cm, "Relatório do Teste de Imagens")

    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, altura - 3 * cm, f"Avaliador: {avaliador or ''}")
    c.drawString(2 * cm, altura - 3.7 * cm, f"Nome: {nome_usuario}")
    c.drawString(2 * cm, altura - 4.4 * cm, f"Matrícula: {matricula}")
    c.drawString(2 * cm, altura - 5.1 * cm, f"Turno: {turno}")
    c.drawString(2 * cm, altura - 5.8 * cm,
                 f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, altura - 7 * cm, f"Acertos: {acertos}")
    c.drawString(6 * cm, altura - 7 * cm, f"Porcentagem: {porcentagem:.2f}%")

    # Espaço antes da seção de erros
    y = altura - 8.5 * cm

    if not erros_imagens:
        c.setFont("Helvetica-Oblique", 11)
        c.drawString(2 * cm, y, "Nenhuma imagem errada. Excelente desempenho!")
        c.showPage()
        c.save()
        return arquivo_pdf

    c.setFont("Helvetica-Bold", 13)
    c.drawString(2 * cm, y, "Imagens incorretas")
    y -= 1 * cm

    # Para cada imagem errada, desenhar a miniatura e as legendas
    thumb_max_w = 6.5 * cm
    thumb_max_h = 5 * cm
    gap_y = 0.6 * cm

    for nome_arquivo, resposta_usuario, resposta_correta, imagem_blob in erros_imagens:
        # Se não houver espaço vertical suficiente, cria nova página
        if y < 4 * cm:
            c.showPage()
            y = altura - 2 * cm

        # Colocar miniatura à esquerda
        try:
            img_reader = ImageReader(BytesIO(imagem_blob))
            iw, ih = img_reader.getSize()
            scale = min(thumb_max_w / iw, thumb_max_h / ih, 1.0)
            w = iw * scale
            h = ih * scale

            x_img = 2 * cm
            c.drawImage(img_reader, x_img, y - h, width=w, height=h,
                        preserveAspectRatio=True, anchor='sw')
        except Exception as e:
            # Se falhar ao desenhar a imagem, apenas escreve o nome do arquivo
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(
                2 * cm, y, f"[Erro ao exibir miniatura] {nome_arquivo}")

        # Texto à direita da miniatura (ou abaixo, caso miniatura falhe)
        x_text = 2 * cm + thumb_max_w + 0.6 * cm
        c.setFont("Helvetica", 10)
        c.drawString(x_text, y - 0.5 * cm, f"Arquivo: {nome_arquivo}")
        c.drawString(x_text, y - 1.2 * cm,
                     f"Resposta do usuário: {resposta_usuario}")
        c.drawString(x_text, y - 1.9 * cm,
                     f"Resposta correta: {resposta_correta}")

        # desce o ponteiro vertical
        y -= (thumb_max_h + gap_y)

    c.showPage()
    c.save()
    return arquivo_pdf


class TesteApp:
    def __init__(self, root, voltar=None, avaliador=None):
        criar_tabelas()
        self.root = root
        self.voltar = voltar
        self.avaliador = avaliador  # <-- armazenando o avaliador
        self.root.title("Executar Teste")
        self.centralizar_janela(600, 500)

        self.nome_var = tk.StringVar()
        self.matricula_var = tk.StringVar()
        self.turno_var = tk.StringVar()

        self.teste_id = None
        self.questoes = []
        self.index = 0
        self.respostas_usuario = []

        self.tela_inicial()

    def centralizar_janela(self, largura, altura):
        self.root.update_idletasks()
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        x = (largura_tela // 2) - (largura // 2)
        y = (altura_tela // 2) - (altura // 2)
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")

    def tela_inicial(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Nome do Avaliado:").pack()
        tk.Entry(self.root, textvariable=self.nome_var).pack()

        tk.Label(self.root, text="Matrícula:").pack()
        tk.Entry(self.root, textvariable=self.matricula_var).pack()

        tk.Label(self.root, text="Turno:").pack()
        tk.Entry(self.root, textvariable=self.turno_var).pack()

        tk.Label(self.root, text="Selecione o teste:").pack()
        self.lista_testes = tk.Listbox(self.root)
        self.lista_testes.pack(fill=tk.BOTH, expand=True)
        self.carregar_testes()

        tk.Button(self.root, text="Iniciar Teste",
                  command=self.iniciar_teste).pack(pady=5)

        if self.voltar:
            tk.Button(self.root, text="Voltar",
                      command=self.voltar).pack(pady=5)

    def carregar_testes(self):
        self.lista_testes.delete(0, tk.END)
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM testes ORDER BY nome")
        for row in cursor.fetchall():
            self.lista_testes.insert(tk.END, f"{row[0]} - {row[1]}")
        conn.close()

    def iniciar_teste(self):
        selecao = self.lista_testes.curselection()
        if not selecao:
            messagebox.showerror("Erro", "Selecione um teste!")
            return

        item = self.lista_testes.get(selecao[0])
        self.teste_id, _ = item.split(" - ", 1)
        self.teste_id = int(self.teste_id)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nome_arquivo, imagem, resposta_correta FROM imagens WHERE teste_id=?", (self.teste_id,))
        imagens = cursor.fetchall()
        conn.close()

        if not imagens:
            messagebox.showerror("Erro", "Este teste não possui imagens!")
            return

        imgs_list = list(imagens)
        random.shuffle(imgs_list)

        # Monta as questões
        self.questoes = imgs_list[:NUM_QUESTOES] if len(
            imgs_list) >= NUM_QUESTOES else imgs_list * (NUM_QUESTOES // len(imgs_list) + 1)
        self.questoes = self.questoes[:NUM_QUESTOES]

        self.index = 0
        self.respostas_usuario = []
        self.tela_questao()

    def tela_questao(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        nome_arquivo, blob, _ = self.questoes[self.index]
        imagem = Image.open(BytesIO(blob))
        imagem = imagem.resize((400, 300), Image.LANCZOS)
        self.img_tk = ImageTk.PhotoImage(imagem)

        tk.Label(
            self.root, text=f"Questão {self.index+1} de {NUM_QUESTOES}").pack()
        tk.Label(self.root, image=self.img_tk).pack()

        frame_btn = tk.Frame(self.root)
        frame_btn.pack(pady=10)

        tk.Button(frame_btn, text="OK", width=15, command=lambda: self.responder(
            "OK")).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_btn, text="NOK", width=15, command=lambda: self.responder(
            "NOK")).pack(side=tk.LEFT, padx=5)

    def responder(self, resposta):
        nome_arquivo, _, _ = self.questoes[self.index]
        self.respostas_usuario.append((nome_arquivo, resposta))
        self.index += 1
        if self.index < NUM_QUESTOES:
            self.tela_questao()
        else:
            self.finalizar_teste()

    def finalizar_teste(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nome_arquivo, resposta_correta FROM imagens WHERE teste_id=?", (self.teste_id,))
        respostas_certas = dict(cursor.fetchall())
        conn.close()

        acertos = 0
        erros = []
        for nome_arquivo, resposta in self.respostas_usuario:
            if respostas_certas.get(nome_arquivo) == resposta:
                acertos += 1
            else:
                # armazena tupla (nome, resposta_usuario)
                erros.append((nome_arquivo, resposta))

        porcentagem = (acertos / NUM_QUESTOES) * 100

        resultados_dir = os.path.join(os.path.abspath("."), "resultados")
        os.makedirs(resultados_dir, exist_ok=True)
        data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nome_csv = os.path.join(
            resultados_dir, f"resultado_{self.nome_var.get()}_{data_hora}.csv")

        df = pd.DataFrame({
            "Avaliador": [self.avaliador]*len(self.respostas_usuario),
            "Imagem": [r[0] for r in self.respostas_usuario],
            "Resposta Usuario": [r[1] for r in self.respostas_usuario],
            "Resposta Correta": [respostas_certas[r[0]] for r in self.respostas_usuario]
        })
        df.to_csv(nome_csv, index=False, sep=';', encoding='utf-8-sig')

        # Monta lista com blobs das imagens erradas para o PDF
        erros_imagens = []
        if erros:
            conn = conectar()
            cursor = conn.cursor()
            for nome_arquivo, resposta_usuario in erros:
                cursor.execute("SELECT imagem, resposta_correta FROM imagens WHERE teste_id=? AND nome_arquivo=?",
                               (self.teste_id, nome_arquivo))
                row = cursor.fetchone()
                if row:
                    imagem_blob, resposta_correta = row  # observe que coluna imagem é o BLOB
                    erros_imagens.append(
                        (nome_arquivo, resposta_usuario, resposta_correta, imagem_blob))
            conn.close()

        arquivo_pdf = gerar_pdf(
            nome_usuario=self.nome_var.get(),
            matricula=self.matricula_var.get(),
            turno=self.turno_var.get(),
            acertos=acertos,
            porcentagem=porcentagem,
            erros_imagens=erros_imagens,
            pasta_resultados=resultados_dir,
            avaliador=self.avaliador
        )

        messagebox.showinfo(
            "Resultado",
            f"Acertos: {acertos}\nErros: {NUM_QUESTOES - acertos}\nPorcentagem: {porcentagem:.2f}%\n\n"
            f"CSV salvo em: {nome_csv}\nPDF salvo em: {arquivo_pdf}"
        )

        # abre a pasta com resultados (mesmo código que você já tinha)
        try:
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(resultados_dir)
            elif sistema == "Darwin":
                subprocess.Popen(["open", resultados_dir])
            else:
                subprocess.Popen(["xdg-open", resultados_dir])
        except Exception as e:
            messagebox.showwarning(
                "Aviso", f"Não foi possível abrir a pasta: {e}")

        self.tela_inicial()


if __name__ == "__main__":
    criar_tabelas()
    root = tk.Tk()
    app = TesteApp(root)
    root.mainloop()
