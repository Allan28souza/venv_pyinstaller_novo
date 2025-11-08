# executar_teste.py (com rodapé)
from reportlab.lib import colors
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
import platform
import subprocess
from datetime import datetime
from io import BytesIO

from database import conectar, criar_tabelas
from utils import centralizar_janela, criar_rodape, show_error, show_info, abrir_pasta

NUM_QUESTOES = 10  # Número de questões por teste


def gerar_pdf(nome_usuario, matricula, turno, acertos, porcentagem,
              erros_imagens, pasta_resultados=None, avaliador=None,
              tempo_total=None, tempo_medio=None):
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
    c.setFillColor(colors.lightgrey)
    c.rect(1.5*cm, altura-4*cm, largura-3*cm, 3.5*cm, fill=True, stroke=False)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, altura - 2.2*cm, "Relatório do Teste de Imagens")
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, altura - 2.8*cm, f"Avaliador: {avaliador or ''}")
    c.drawString(2*cm, altura - 3.4*cm, f"Nome: {nome_usuario}")
    c.drawString(2*cm, altura - 4.0*cm, f"Matrícula: {matricula}")
    c.drawString(10*cm, altura - 2.8*cm, f"Turno: {turno}")
    c.drawString(10*cm, altura - 3.4*cm,
                 f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Resultados
    c.setFillColor(colors.whitesmoke)
    c.rect(1.5*cm, altura-6.5*cm, largura-3 *
           cm, 1.5*cm, fill=True, stroke=False)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, altura - 6.0*cm, f"Acertos: {acertos}")
    c.drawString(6*cm, altura - 6.0*cm, f"Porcentagem: {porcentagem:.2f}%")
    if tempo_total is not None and tempo_medio is not None:
        c.drawString(2*cm, altura - 6.7*cm, f"Tempo total: {tempo_total}s")
        c.drawString(6*cm, altura - 6.7*cm, f"Tempo médio: {tempo_medio:.2f}s")

    # Separador
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.line(1.5*cm, altura-7.5*cm, largura-1.5*cm, altura-7.5*cm)

    y = altura - 8.0*cm

    if not erros_imagens:
        c.setFont("Helvetica-Oblique", 11)
        c.drawString(2*cm, y, "Nenhuma imagem errada. Excelente desempenho!")
        c.showPage()
        c.save()
        return arquivo_pdf

    # Imagens incorretas
    c.setFont("Helvetica-Bold", 13)
    c.drawString(2*cm, y, "Imagens incorretas")
    y -= 1*cm

    thumb_max_w = 6.5*cm
    thumb_max_h = 5*cm
    gap_y = 0.6*cm

    for nome_arquivo, resposta_usuario, resposta_correta, imagem_blob in erros_imagens:
        if y < 4*cm:
            c.showPage()
            y = altura - 2*cm
        try:
            img_reader = ImageReader(BytesIO(imagem_blob))
            iw, ih = img_reader.getSize()
            scale = min(thumb_max_w / iw, thumb_max_h / ih, 1.0)
            w, h = iw * scale, ih * scale
            c.drawImage(img_reader, 2*cm, y-h, width=w, height=h,
                        preserveAspectRatio=True, anchor='sw')
        except:
            c.setFont("Helvetica-Oblique", 10)
            c.drawString(2*cm, y, f"[Erro ao exibir miniatura] {nome_arquivo}")
        x_text = 2*cm + thumb_max_w + 0.6*cm
        c.setFont("Helvetica", 10)
        c.drawString(x_text, y-0.5*cm, f"Arquivo: {nome_arquivo}")
        c.drawString(x_text, y-1.2*cm,
                     f"Resposta do usuário: {resposta_usuario}")
        c.drawString(x_text, y-1.9*cm, f"Resposta correta: {resposta_correta}")
        y -= (thumb_max_h + gap_y)

    c.showPage()
    c.save()
    return arquivo_pdf


class TesteApp:
    def __init__(self, root, voltar=None, avaliador=None):
        criar_tabelas()
        self.root = root
        self.voltar = voltar
        self.avaliador = avaliador
        self.rodape_frame = None
        self.root.title("Motherson Taubaté - Executar Teste")
        centralizar_janela(self.root, 600, 500)

        self.nome_var = tk.StringVar()
        self.matricula_var = tk.StringVar()
        self.turno_var = tk.StringVar()

        self.teste_id = None
        self.questoes = []
        self.index = 0
        self.respostas_usuario = []

        self.tela_inicial()

    def atualizar_tempo(self):
        tempo_corrente = (datetime.now() - self.tempo_inicio).seconds
        if hasattr(self, "tempo_label"):
            self.tempo_label.config(text=f"Tempo: {tempo_corrente}s")
            self.tempo_job = self.root.after(1000, self.atualizar_tempo)

    def limpar_tela(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        if self.rodape_frame:
            # Se for tupla ou lista, destrói cada item
            if isinstance(self.rodape_frame, (tuple, list)):
                for w in self.rodape_frame:
                    w.destroy()
            else:
                self.rodape_frame.destroy()

    def tela_inicial(self):
        self.limpar_tela()

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

        self.rodape_frame = criar_rodape(self.root)

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
            show_error("Erro", "Selecione um teste!")
            return
        item = self.lista_testes.get(selecao[0])
        self.teste_id = int(item.split(" - ", 1)[0])

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nome_arquivo, imagem, resposta_correta FROM imagens WHERE teste_id=?", (self.teste_id,))
        imagens = cursor.fetchall()
        conn.close()

        if not imagens:
            show_error("Erro", "Este teste não possui imagens!")
            return

        imgs_list = list(imagens)
        random.shuffle(imgs_list)
        self.questoes = (imgs_list[:NUM_QUESTOES]
                         if len(imgs_list) >= NUM_QUESTOES
                         else imgs_list * (NUM_QUESTOES // len(imgs_list) + 1))
        self.questoes = self.questoes[:NUM_QUESTOES]

        self.index = 0
        self.respostas_usuario = []
        self.tela_questao()

    def tela_questao(self):
        self.limpar_tela()

        nome_arquivo, blob, _ = self.questoes[self.index]
        imagem = Image.open(BytesIO(blob))
        imagem = imagem.resize((400, 300), Image.LANCZOS)
        self.img_tk = ImageTk.PhotoImage(imagem)

        tk.Label(
            self.root, text=f"Questão {self.index+1} de {NUM_QUESTOES}").pack()
        tk.Label(self.root, image=self.img_tk).pack()

        # Label do tempo
        self.tempo_label = tk.Label(
            self.root, text="Tempo: 0s", font=("Arial", 12))
        self.tempo_label.pack(pady=5)
        self.tempo_inicio = datetime.now()
        self.atualizar_tempo()

        frame_btn = tk.Frame(self.root)
        frame_btn.pack(pady=10)
        tk.Button(frame_btn, text="OK", width=15,
                  command=lambda: self.responder("OK")).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_btn, text="NOK", width=15,
                  command=lambda: self.responder("NOK")).pack(side=tk.LEFT, padx=5)

        self.rodape_frame = criar_rodape(self.root)

    def responder(self, resposta):
        if hasattr(self, "tempo_job"):
            self.root.after_cancel(self.tempo_job)
        tempo_gasto = (datetime.now() - self.tempo_inicio).seconds

        nome_arquivo, _, _ = self.questoes[self.index]
        self.respostas_usuario.append((nome_arquivo, resposta, tempo_gasto))
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

        for nome_arquivo, resposta_usuario, tempo_gasto in self.respostas_usuario:
            resposta_correta = respostas_certas.get(nome_arquivo)
            if resposta_correta and resposta_correta.strip().upper() == resposta_usuario.strip().upper():
                acertos += 1
            else:
                erros.append((nome_arquivo, resposta_usuario))

        porcentagem = (acertos / NUM_QUESTOES) * 100

        resultados_dir = os.path.join(os.path.abspath("."), "resultados")
        os.makedirs(resultados_dir, exist_ok=True)
        data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nome_csv = os.path.join(
            resultados_dir, f"resultado_{self.nome_var.get()}_{data_hora}.csv")

        df = pd.DataFrame({
            "Imagem": [r[0] for r in self.respostas_usuario],
            "Resposta Usuário": [r[1] for r in self.respostas_usuario],
            "Tempo (s)": [r[2] for r in self.respostas_usuario],
            "Resposta Correta": [respostas_certas[r[0]] for r in self.respostas_usuario]
        })

        df.to_csv(nome_csv, index=False, sep=';', encoding='utf-8-sig')

        # Monta lista com blobs das imagens erradas para o PDF
        erros_imagens = []
        if erros:
            conn = conectar()
            cursor = conn.cursor()
            for nome_arquivo, resposta_usuario in erros:
                cursor.execute(
                    "SELECT imagem, resposta_correta FROM imagens WHERE teste_id=? AND nome_arquivo=?",
                    (self.teste_id, nome_arquivo)
                )
                row = cursor.fetchone()
                if row:
                    imagem_blob, resposta_correta = row
                    erros_imagens.append(
                        (nome_arquivo, resposta_usuario, resposta_correta, imagem_blob))
            conn.close()

        # Calcula tempos
        tempo_total = sum(r[2] for r in self.respostas_usuario)
        tempo_medio = tempo_total / NUM_QUESTOES

        arquivo_pdf = gerar_pdf(
            nome_usuario=self.nome_var.get(),
            matricula=self.matricula_var.get(),
            turno=self.turno_var.get(),
            acertos=acertos,
            porcentagem=porcentagem,
            erros_imagens=erros_imagens,
            pasta_resultados=resultados_dir,
            avaliador=self.avaliador,
            tempo_total=tempo_total,
            tempo_medio=tempo_medio
        )

        resultado_texto = (
            f"Acertos: {acertos}\n"
            f"Erros: {NUM_QUESTOES - acertos}\n"
            f"Porcentagem: {porcentagem:.2f}%\n"
            f"Tempo total: {tempo_total}s\n"
            f"Tempo médio por questão: {tempo_medio:.2f}s\n\n"
        )

        show_info("Resultado do Teste", resultado_texto)
        abrir_pasta(resultados_dir)
        self.tela_inicial()


if __name__ == "__main__":
    criar_tabelas()
    root = tk.Tk()
    app = TesteApp(root)
    root.mainloop()
