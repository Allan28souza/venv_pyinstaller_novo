# executor_rr_view.py
# executor_rr_view.py
# RRView completo com 7 abas (Dashboard Profissional)

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os

from executar.rr_graficos import (
    plot_repetibilidade,
    plot_reprodutibilidade,
    plot_itens_confusos,
    plot_ok_nok_por_imagem,
    plot_heatmap_concordancia,
    plot_tendencia_operador,
)
# função que retorna dados textuais resumidos
from executar.rr_analise import analisar_rr
import utils


class RRView:
    def __init__(self, root):
        self.root = root
        self.win = tk.Toplevel(root)
        self.win.title(
            "Análises RR — Estudo de Repetibilidade e Reprodutibilidade")
        self.win.geometry("1280x720")

        self._build_layout()

    # --------------------------------------------------------
    def _build_layout(self):
        titulo = tk.Label(
            self.win, text="Estudo RR — MSA Atributivo", font=("Segoe UI", 18, "bold"))
        titulo.pack(pady=10)

        self.frame_top = tk.Frame(self.win)
        self.frame_top.pack(fill="x", pady=5)

        tk.Label(self.frame_top, text="ID do Teste:", font=(
            "Segoe UI", 11)).pack(side="left", padx=8)
        self.entry_teste = ttk.Entry(self.frame_top, width=10)
        self.entry_teste.pack(side="left")

        ttk.Button(self.frame_top, text="Analisar",
                   command=self._executar_analise).pack(side="left", padx=10)

        ttk.Button(self.frame_top, text="Gerar PDF",
                   command=self.gerar_pdf_rr).pack(side="right", padx=10)

        self.notebook = ttk.Notebook(self.win)
        self.notebook.pack(expand=True, fill="both")

        # abas
        self.aba_resumo = ttk.Frame(self.notebook)
        self.aba_rep = ttk.Frame(self.notebook)
        self.aba_reprod = ttk.Frame(self.notebook)
        self.aba_confusos = ttk.Frame(self.notebook)
        self.aba_oknok = ttk.Frame(self.notebook)
        self.aba_tendencia = ttk.Frame(self.notebook)
        self.aba_heatmap = ttk.Frame(self.notebook)

        self.notebook.add(self.aba_resumo, text="Resumo Geral")
        self.notebook.add(self.aba_rep, text="Repetibilidade")
        self.notebook.add(self.aba_reprod, text="Reprodutibilidade")
        self.notebook.add(self.aba_confusos, text="Itens Confusos")
        self.notebook.add(self.aba_oknok, text="OK/NOK por Imagem")
        self.notebook.add(self.aba_tendencia, text="Tendência por Operador")
        self.notebook.add(self.aba_heatmap, text="Heatmap")

    # --------------------------------------------------------
    def _limpar_aba(self, aba):
        for w in aba.winfo_children():
            w.destroy()

    def _carregar_imagem(self, aba, caminho, title=""):
        if not os.path.exists(caminho):
            tk.Label(aba, text="Imagem não encontrada", fg="red").pack()
            return

        img = Image.open(caminho)
        img = img.resize((900, 550), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)

        tk.Label(aba, text=title, font=("Segoe UI", 14, "bold")).pack(pady=5)
        lbl = tk.Label(aba, image=photo)
        lbl.image = photo
        lbl.pack(pady=10)

    # --------------------------------------------------------
    def _executar_analise(self):
        teste_id_txt = self.entry_teste.get().strip()
        if not teste_id_txt.isdigit():
            return utils.show_error("Erro", "Digite um ID de teste válido.")

        teste_id = int(teste_id_txt)

        # 1 — gerar dados textuais
        resumo = analisar_rr(teste_id)

        # limpar abas
        for aba in [self.aba_resumo, self.aba_rep, self.aba_reprod,
                    self.aba_confusos, self.aba_oknok, self.aba_tendencia, self.aba_heatmap]:
            self._limpar_aba(aba)

        # mostrar resumo
        tk.Label(self.aba_resumo, text="Resumo do Estudo RR",
                 font=("Segoe UI", 16, "bold")).pack(pady=10)
        caixa = tk.Text(self.aba_resumo, font=(
            "Segoe UI", 11), width=120, height=25)
        caixa.pack(padx=10, pady=10)
        caixa.insert("end", resumo)
        caixa.config(state="disabled")

        # 2 — gerar gráficos
        try:
            rep_path = plot_repetibilidade(teste_id)
            self._carregar_imagem(self.aba_rep, rep_path,
                                  "Repetibilidade por Operador")
        except Exception as e:
            tk.Label(self.aba_rep, text=f"Erro: {e}").pack()

        try:
            reprod_path = plot_reprodutibilidade(teste_id)
            self._carregar_imagem(
                self.aba_reprod, reprod_path, "Reprodutibilidade vs Consenso")
        except Exception as e:
            tk.Label(self.aba_reprod, text=f"Erro: {e}").pack()

        try:
            conf_path = plot_itens_confusos(teste_id)
            self._carregar_imagem(
                self.aba_confusos, conf_path, "Itens mais Confusos")
        except Exception as e:
            tk.Label(self.aba_confusos, text=f"Erro: {e}").pack()

        try:
            oknok_path = plot_ok_nok_por_imagem(teste_id)
            self._carregar_imagem(
                self.aba_oknok, oknok_path, "OK/NOK por Imagem")
        except Exception as e:
            tk.Label(self.aba_oknok, text=f"Erro: {e}").pack()

        try:
            tend_path = plot_tendencia_operador(teste_id)
            self._carregar_imagem(self.aba_tendencia,
                                  tend_path, "Tendência por Operador")
        except Exception as e:
            tk.Label(self.aba_tendencia, text=f"Erro: {e}").pack()

        try:
            heat_path = plot_heatmap_concordancia(teste_id)
            self._carregar_imagem(
                self.aba_heatmap, heat_path, "Heatmap de Concordância")
        except Exception as e:
            tk.Label(self.aba_heatmap, text=f"Erro: {e}").pack()

    # --------------------------------------------------------
    # GERAR PDF DO ESTUDO RR
    # --------------------------------------------------------
    def gerar_pdf_rr(self):
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.utils import ImageReader
        import os
        from datetime import datetime
        from executar.rr_graficos import gerar_todos_graficos

        teste_id_txt = self.entry_teste.get().strip()

        if not teste_id_txt.isdigit():
            return utils.show_error("Erro", "Informe um ID de teste válido.")

        teste_id = int(teste_id_txt)

        # gera todos os gráficos novamente
        try:
            paths = gerar_todos_graficos(teste_id)
        except Exception as e:
            return utils.show_error("Erro", f"Não foi possível gerar gráficos:\n{e}")

        pasta = "resultados/rr_pdf"
        os.makedirs(pasta, exist_ok=True)

        nome_pdf = os.path.join(
            pasta,
            f"RR_{teste_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        c = canvas.Canvas(nome_pdf, pagesize=A4)
        w, h = A4

        # --------------------------------------------------------
        # PÁGINA 1 – Cabeçalho do Relatório
        # --------------------------------------------------------
        c.setFont("Helvetica-Bold", 20)
        c.drawString(2*cm, h - 2*cm, "Relatório de RR – MSA Atributivo")

        c.setFont("Helvetica", 12)
        c.drawString(2*cm, h - 3*cm,
                     f"Teste analisado: {teste_id}")
        c.drawString(2*cm, h - 4*cm,
                     f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        # insere resumo textual
        c.setFont("Helvetica", 10)
        resumo = analisar_rr(teste_id).split("\n")

        y = h - 5*cm
        for linha in resumo:
            if y < 2*cm:
                c.showPage()
                y = h - 2*cm
            c.drawString(2*cm, y, linha)
            y -= 0.5*cm

        c.showPage()

        # --------------------------------------------------------
        # Demais páginas – gráficos
        # --------------------------------------------------------
        for titulo, path in paths.items():
            if not path or not os.path.exists(path):
                continue

            c.setFont("Helvetica-Bold", 16)
            c.drawString(2*cm, h - 2*cm, titulo.replace("_", " ").title())

            try:
                img = ImageReader(path)
                c.drawImage(
                    img,
                    2*cm,
                    3.5*cm,
                    width=w - 4*cm,
                    height=h - 7*cm,
                    preserveAspectRatio=True,
                )
            except Exception as e:
                c.setFont("Helvetica", 12)
                c.drawString(2*cm, h - 5*cm, f"[Erro ao carregar imagem: {e}]")

            c.showPage()

        c.save()

        # tenta abrir automaticamente (Windows)
        try:
            os.startfile(nome_pdf)
        except:
            pass

        utils.show_info("PDF Gerado",
                        f"Relatório salvo em:\n{nome_pdf}")
