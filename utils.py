# utils.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os
import platform
import subprocess
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from io import BytesIO

VERSAO = "v1.0"
PRODUTOR = "Allan Fonseca"
CONFIG_PATH = "config.json"


def carregar_config():
    if not os.path.exists(CONFIG_PATH):
        cfg = {"num_questoes": 30, "num_ciclos": 3, "pasta_testes": "testes"}
        salvar_config(cfg)
        return cfg
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)


def centralizar_janela(root, largura, altura):
    root.update_idletasks()
    largura_tela = root.winfo_screenwidth()
    altura_tela = root.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    root.geometry(f"{largura}x{altura}+{x}+{y}")


def criar_rodape(root):
    rodape_frame = tk.Frame(root, height=25, bg="#f0f0f0")
    rodape_frame.pack(side=tk.BOTTOM, fill=tk.X)
    tk.Label(rodape_frame, text=f"Motherson SAS - {PRODUTOR}", font=(
        "Arial", 8), bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
    hora_label = tk.Label(
        rodape_frame, text=f"{VERSAO} - {datetime.now().strftime('%H:%M:%S')}", font=("Arial", 8), bg="#f0f0f0")
    hora_label.pack(side=tk.RIGHT, padx=5)

    def atualizar_hora():
        if hora_label.winfo_exists():
            hora_label.config(
                text=f"{VERSAO} - {datetime.now().strftime('%H:%M:%S')}")
            root.after(1000, atualizar_hora)
    atualizar_hora()
    return rodape_frame, hora_label


def show_info(titulo, mensagem):
    messagebox.showinfo(f"Motherson Taubaté - {titulo}", mensagem)


def show_error(titulo, mensagem):
    messagebox.showerror(f"Motherson Taubaté - {titulo}", mensagem)


def show_warning(titulo, mensagem):
    messagebox.showwarning(f"Motherson Taubaté - {titulo}", mensagem)


def abrir_pasta(path):
    try:
        sistema = platform.system()
        if sistema == "Windows":
            os.startfile(path)
        elif sistema == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        show_warning("Aviso", f"Não foi possível abrir a pasta: {e}")

# gerar_relatorio_pdf: mantém assinatura usada pelo executar_teste.py


def gerar_relatorio_pdf(nome_usuario, matricula, turno, acertos, porcentagem, erros_imagens, pasta_resultados=None, avaliador=None, tempo_total=None, tempo_medio=None):
    """
    erros_imagens: lista de tuples -> (nome_arquivo, resposta_usuario, resposta_correta, imagem_blob_bytes)
    """
    if pasta_resultados is None:
        pasta_resultados = os.path.join(os.path.abspath("."), "resultados")
    os.makedirs(pasta_resultados, exist_ok=True)

    arquivo_pdf = os.path.join(
        pasta_resultados, f"resultado_{nome_usuario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    c = canvas.Canvas(arquivo_pdf, pagesize=A4)
    largura, altura = A4

    # CABEÇALHO COM FUNDO CLARO
    c.setFillColorRGB(0.94, 0.94, 0.94)
    c.rect(1.5*cm, altura-4*cm, largura-3*cm, 3.5*cm, fill=True, stroke=False)
    c.setFillColorRGB(0, 0, 0)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, altura - 2.2*cm, "Relatório do Teste de Imagens")
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, altura - 2.8*cm, f"Avaliador: {avaliador or ''}")
    c.drawString(2*cm, altura - 3.4*cm, f"Nome: {nome_usuario}")
    c.drawString(2*cm, altura - 4.0*cm, f"Matrícula: {matricula}")
    c.drawString(10*cm, altura - 2.8*cm, f"Turno: {turno}")
    c.drawString(10*cm, altura - 3.4*cm,
                 f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    c.setFillColorRGB(0.96, 0.96, 0.96)
    c.rect(1.5*cm, altura-6.5*cm, largura-3 *
           cm, 1.5*cm, fill=True, stroke=False)
    c.setFillColorRGB(0, 0, 0)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, altura - 6.0*cm, f"Acertos: {acertos}")
    c.drawString(6*cm, altura - 6.0*cm, f"Porcentagem: {porcentagem:.2f}%")
    if tempo_total is not None and tempo_medio is not None:
        c.drawString(2*cm, altura - 6.7*cm, f"Tempo total: {tempo_total}s")
        c.drawString(6*cm, altura - 6.7*cm, f"Tempo médio: {tempo_medio:.2f}s")

    # separador
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(0.5)
    c.line(1.5*cm, altura-7.5*cm, largura-1.5*cm, altura-7.5*cm)

    y = altura - 8.0*cm

    if not erros_imagens:
        c.setFont("Helvetica-Oblique", 11)
        c.drawString(2*cm, y, "Nenhuma imagem errada. Excelente desempenho!")
        c.showPage()
        c.save()
        show_info("Relatório Gerado", f"Relatório salvo em:\n{arquivo_pdf}")
        abrir_pasta(pasta_resultados)
        return arquivo_pdf

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
            w = iw * scale
            h = ih * scale
            x_img = 2*cm
            c.drawImage(img_reader, x_img, y-h, width=w, height=h,
                        preserveAspectRatio=True, anchor='sw')
        except Exception:
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
    show_info("Relatório Gerado", f"Relatório salvo em:\n{arquivo_pdf}")
    abrir_pasta(pasta_resultados)
    return arquivo_pdf
