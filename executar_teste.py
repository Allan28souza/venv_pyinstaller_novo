import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import pandas as pd
import os
import subprocess
import platform
from datetime import datetime

from database import conectar, criar_tabelas

NUM_QUESTOES = 90  # Número de questões por teste


def gerar_pdf(nome_usuario, matricula, turno, acertos, erros, porcentagem, erros_lista, pasta_resultados=None):
    if pasta_resultados is None:
        pasta_resultados = os.path.join(os.path.abspath("."), "resultados")
    os.makedirs(pasta_resultados, exist_ok=True)

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import cm

    arquivo_pdf = os.path.join(
        pasta_resultados,
        f"resultado_{nome_usuario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    largura, altura = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, altura - 2*cm, "Relatório do Teste de Imagens")

    c.setFont("Helvetica", 12)
    c.drawString(2*cm, altura - 3*cm, f"Nome: {nome_usuario}")
    c.drawString(2*cm, altura - 3.7*cm, f"Matrícula: {matricula}")
    c.drawString(2*cm, altura - 4.4*cm, f"Turno: {turno}")

    c.drawString(2*cm, altura - 5.2*cm, f"Acertos: {acertos}")
    c.drawString(2*cm, altura - 5.9*cm, f"Erros: {len(erros_lista)}")
    c.drawString(2*cm, altura - 6.6*cm,
                 f"Porcentagem de Acerto: {porcentagem:.2f}%")

    c.drawString(2*cm, altura - 7.5*cm, "Lista de imagens erradas:")

    y = altura - 8.3*cm
    c.setFont("Helvetica-Oblique", 10)
    for img_path in erros_lista:
        nome_arquivo = os.path.basename(img_path)
        c.drawString(3*cm, y, nome_arquivo)
        y -= 0.5*cm
        if y < 2*cm:
            c.showPage()
            y = altura - 2*cm
            c.setFont("Helvetica-Oblique", 10)

    c.save()
    return arquivo_pdf


class TesteApp:
    def __init__(self, root, voltar=None):
        criar_tabelas()
        self.root = root
        self.voltar = voltar
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

        tk.Label(self.root, text="Nome:").pack()
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
        cursor.execute("SELECT id, nome FROM testes")
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
            "SELECT caminho, resposta_correta FROM imagens WHERE teste_id=?", (self.teste_id,))
        imagens = cursor.fetchall()
        conn.close()

        if not imagens:
            messagebox.showerror("Erro", "Este teste não possui imagens!")
            return

        imgs_list = list(imagens)
        self.questoes = []

        ultima = None
        while len(self.questoes) < NUM_QUESTOES:
            random.shuffle(imgs_list)
            for img in imgs_list:
                if img != ultima:
                    self.questoes.append(img)
                    ultima = img
                    if len(self.questoes) >= NUM_QUESTOES:
                        break

        self.index = 0
        self.respostas_usuario = []
        self.tela_questao()

    def tela_questao(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        caminho_img, _ = self.questoes[self.index]
        img = Image.open(caminho_img)
        img = img.resize((400, 300), Image.LANCZOS)
        self.img_tk = ImageTk.PhotoImage(img)

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
        self.respostas_usuario.append((self.questoes[self.index][0], resposta))
        self.index += 1
        if self.index < NUM_QUESTOES:
            self.tela_questao()
        else:
            self.finalizar_teste()

    def finalizar_teste(self):
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT caminho, resposta_correta FROM imagens WHERE teste_id=?", (self.teste_id,))
        respostas_certas = dict(cursor.fetchall())
        conn.close()

        acertos = 0
        erros = []
        for caminho, resposta in self.respostas_usuario:
            if respostas_certas.get(caminho) == resposta:
                acertos += 1
            else:
                erros.append(caminho)

        porcentagem = (acertos / NUM_QUESTOES) * 100

        resultados_dir = os.path.join(os.path.abspath("."), "resultados")
        os.makedirs(resultados_dir, exist_ok=True)
        data_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nome_csv = os.path.join(
            resultados_dir, f"resultado_{self.nome_var.get()}_{data_hora}.csv")

        df = pd.DataFrame({
            "Imagem": [r[0] for r in self.respostas_usuario],
            "Resposta Usuário": [r[1] for r in self.respostas_usuario],
            "Resposta Correta": [respostas_certas[r[0]] for r in self.respostas_usuario]
        })
        df.to_csv(nome_csv, index=False, sep=';', encoding='utf-8-sig')

        arquivo_pdf = gerar_pdf(
            nome_usuario=self.nome_var.get(),
            matricula=self.matricula_var.get(),
            turno=self.turno_var.get(),
            acertos=acertos,
            erros=erros,
            porcentagem=porcentagem,
            erros_lista=erros,
            pasta_resultados=resultados_dir
        )

        messagebox.showinfo(
            "Resultado",
            f"Acertos: {acertos}\nErros: {NUM_QUESTOES - acertos}\nPorcentagem: {porcentagem:.2f}%\n\n"
            f"CSV salvo em: {nome_csv}\nPDF salvo em: {arquivo_pdf}"
        )

        # abre a pasta com resultados
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
