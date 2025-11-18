import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
from datetime import datetime
from .executor_utils import formatar_timedelta
import database as db
import utils
from .executor_controller import TesteController


class TesteExecutorView:
    def __init__(self, root, teste_id, nome_teste,
                 operador_id=None, avaliador=None,
                 turno=None, on_close=None):

        self.root = root
        self.nome_teste = nome_teste
        self.on_close = on_close

        # carregar config
        try:
            cfg = utils.carregar_config()
        except:
            cfg = {}

        num_questoes = int(cfg.get("num_questoes", 30))
        num_ciclos = int(cfg.get("num_ciclos", 3))

        self.ctrl = TesteController(
            teste_id=teste_id,
            operador_id=operador_id,
            avaliador=avaliador,
            turno=turno,
            num_questoes=num_questoes,
            num_ciclos=num_ciclos
        )

        if not self.ctrl.imagens:
            utils.show_warning(
                "Aviso", "Nenhuma imagem cadastrada neste teste.")
            return

        # Criar janela moderna
        self.win = tk.Toplevel(self.root)
        self.win.title(f"Executar Teste - {self.nome_teste}")

        try:
            self.win.state("zoomed")
        except:
            self.win.geometry("1280x720")

        self._question_job = None
        self._total_job = None

        self._build_header()
        self._build_body_initial()
        self._build_footer()

        self.win.protocol("WM_DELETE_WINDOW", self._cancelar)

    # -----------------------------------------
    def _build_header(self):
        header = tk.Frame(self.win, bg="#2e3f4f", height=60)
        header.pack(fill="x")

        tk.Label(
            header,
            text="MOTHERSON TAUBATÉ",
            bg="#2e3f4f",
            fg="white",
            font=("Segoe UI", 16, "bold")
        ).pack(side="left", padx=20)

        tk.Label(
            header,
            text=self.nome_teste,
            bg="#2e3f4f",
            fg="#d3dce6",
            font=("Segoe UI", 12)
        ).pack(side="left", padx=10)

        timer_frame = tk.Frame(header, bg="#2e3f4f")
        timer_frame.pack(side="right", padx=25)

        self.lbl_total = tk.Label(
            timer_frame,
            text="Tempo total: 00:00:00",
            bg="#2e3f4f",
            fg="white",
            font=("Segoe UI", 11)
        )
        self.lbl_total.pack(anchor="e")

        self.lbl_questao = tk.Label(
            timer_frame,
            text="Tempo questão: 0s",
            bg="#2e3f4f",
            fg="#cfd8dc",
            font=("Segoe UI", 10)
        )
        self.lbl_questao.pack(anchor="e")

    # -----------------------------------------
    def _build_body_initial(self):
        self.frame_body = tk.Frame(self.win, bg="#f4f6f8")
        self.frame_body.pack(expand=True, fill="both")

        tk.Label(
            self.frame_body,
            text=f"Teste: {self.nome_teste}",
            font=("Segoe UI", 20, "bold"),
            bg="#f4f6f8",
            fg="#333"
        ).pack(pady=40)

        tk.Label(
            self.frame_body,
            text=f"{self.ctrl.num_questoes} imagens por ciclo — {self.ctrl.num_ciclos} ciclos",
            font=("Segoe UI", 13),
            bg="#f4f6f8"
        ).pack(pady=10)

        ttk.Button(
            self.frame_body,
            text="Iniciar Teste",
            command=self.iniciar
        ).pack(pady=40)

    # -----------------------------------------
    def _build_body_test(self):
        for w in self.frame_body.winfo_children():
            w.destroy()

        self.frame_body.configure(bg="#eaeef2")

        # frame principal dividido em 2 colunas
        self.frame_left = tk.Frame(self.frame_body, bg="#eaeef2")
        self.frame_left.pack(side="left", expand=True,
                             fill="both", padx=20, pady=20)

        self.frame_right = tk.Frame(self.frame_body, bg="#eaeef2", width=350)
        self.frame_right.pack(side="right", fill="y", padx=20, pady=20)

    # -----------------------------------------
    def _build_footer(self):
        footer = tk.Frame(self.win, bg="#2e3f4f", height=50)
        footer.pack(fill="x")

        ttk.Button(
            footer, text="Cancelar Teste",
            command=self._cancelar
        ).pack(side="left", padx=20, pady=10)

        ttk.Button(
            footer, text="Fechar",
            command=self._cancelar
        ).pack(side="right", padx=20, pady=10)

    # -----------------------------------------
    def iniciar(self):
        self.ctrl.iniciar()
        self._start_total_timer()
        self._build_body_test()
        self._exibir()

    # -----------------------------------------
    def _exibir(self):
        # limpar esquerda e direita
        for w in self.frame_left.winfo_children():
            w.destroy()
        for w in self.frame_right.winfo_children():
            w.destroy()

        if self.ctrl.ciclo_finalizado():
            self._finalizar_ciclo()
            return

        img_id, nome_arquivo, resposta_correta = self.ctrl.get_info_imagem()

        caminho = db.extrair_imagem_temp(img_id)
        if not caminho or not os.path.exists(caminho):
            messagebox.showerror(
                "Erro", f"Arquivo não encontrado: {nome_arquivo}")
            self.ctrl.avancar()
            self._exibir()
            return

        # TAMANHO PADRÃO CONTROLADO
        TAM_IMAGEM = (700, 480)

        img = Image.open(caminho).resize(TAM_IMAGEM)
        photo = ImageTk.PhotoImage(img)

        img_frame = tk.Frame(self.frame_left, bg="#dfe3e6")
        img_frame.pack(expand=True, pady=10)

        lbl = tk.Label(img_frame, image=photo, bg="#dfe3e6")
        lbl.image = photo
        lbl.pack()

        # -----------------------------------
        # LADO DIREITO — informações + botões
        # -----------------------------------

        tk.Label(
            self.frame_right,
            text=f"Imagem {self.ctrl.indice_atual+1}/{self.ctrl.num_questoes}",
            font=("Segoe UI", 13),
            bg="#eaeef2",
            fg="#333"
        ).pack(pady=8)

        tk.Label(
            self.frame_right,
            text=f"Ciclo {self.ctrl.ciclo_atual}/{self.ctrl.num_ciclos}",
            font=("Segoe UI", 13),
            bg="#eaeef2",
            fg="#333"
        ).pack(pady=8)

        # Botões grandes
        style = ttk.Style()
        style.configure("Big.TButton", font=("Segoe UI", 14), padding=12)

        ttk.Button(
            self.frame_right, text="OK", style="Big.TButton",
            command=lambda: self._responder(
                nome_arquivo, "OK", resposta_correta)
        ).pack(pady=20, fill="x")

        ttk.Button(
            self.frame_right, text="NOK", style="Big.TButton",
            command=lambda: self._responder(
                nome_arquivo, "NOK", resposta_correta)
        ).pack(pady=5, fill="x")

        # timer questão
        self.inicio_questao = datetime.now()
        self._start_question_timer()

    # -----------------------------------------
    def _responder(self, nome_arquivo, resp_user, resp_correta):
        tempo = int((datetime.now() - self.inicio_questao).total_seconds())
        self.ctrl.registrar_resposta(
            nome_arquivo, resp_user, resp_correta, tempo)

        self.ctrl.avancar()
        self._exibir()

    # -----------------------------------------
    def _finalizar_ciclo(self):
        self.ctrl.avancar_ciclo()
        if self.ctrl.teste_finalizado():
            self._finalizar_teste()
        else:
            self._build_body_test()
            self._exibir()

    # =========================================
    # FINALIZAR TESTE
    # =========================================
    def _finalizar_teste(self):
        self._stop_timers()

        acertos, total, porcentagem, tempo_total, tempo_medio = self.ctrl.salvar_no_banco()

        # ------------------------------
        # DADOS DO OPERADOR
        # ------------------------------
        nome_operador = ""
        matricula_operador = ""
        turno_operador = self.ctrl.turno or ""

        try:
            dados_op = db.obter_dados_operador(self.ctrl.operador_id)
            if dados_op:
                if len(dados_op) == 3:
                    nome_operador, matricula_operador, turno_operador = dados_op
                elif len(dados_op) == 4:
                    _, nome_operador, matricula_operador, turno_operador = dados_op
        except:
            pass

        # ------------------------------
        # ERROS PARA O PDF
        # ------------------------------
        erros_imagens = []
        for nome_arq, resp_u, resp_c, _ in self.ctrl.respostas_usuario:
            if resp_u.upper().strip() != resp_c.upper().strip():
                try:
                    blob_img = db.buscar_blob_imagem(
                        nome_arq, self.ctrl.teste_id)
                except:
                    blob_img = b""
                erros_imagens.append((nome_arq, resp_u, resp_c, blob_img))

        # ------------------------------
        # GERAR PDF
        # ------------------------------
        try:
            caminho_pdf = utils.gerar_relatorio_pdf(
                nome_usuario=nome_operador,
                matricula=matricula_operador,
                turno=turno_operador,
                acertos=acertos,
                porcentagem=porcentagem,
                erros_imagens=erros_imagens,
                avaliador=self.ctrl.avaliador or "",
                tempo_total=tempo_total,
                tempo_medio=tempo_medio,
                titulo_teste=self.nome_teste
            )

            try:
                os.startfile(caminho_pdf)
            except:
                pass

        except Exception as e:
            utils.show_warning("Aviso", f"Erro ao gerar PDF: {e}")

        # Popup resumo
        utils.show_info(
            "Resultado",
            f"Acertos: {acertos}\n"
            f"Erros: {total - acertos}\n"
            f"Porcentagem: {porcentagem:.2f}%\n"
            f"Tempo total: {tempo_total}s\n"
            f"Tempo médio: {tempo_medio:.2f}s"
        )

        # Fechar executor sem perguntar
        self._cancelar(perguntar=False)

    # =========================================
    # TIMERS
    # =========================================
    def _start_total_timer(self):
        try:
            elapsed = datetime.now() - self.ctrl.inicio_total
            self.lbl_total.config(
                text=f"Tempo total: {formatar_timedelta(elapsed)}")
            self._total_job = self.win.after(1000, self._start_total_timer)
        except:
            pass

    def _start_question_timer(self):
        try:
            elapsed = int(
                (datetime.now() - self.inicio_questao).total_seconds())
            self.lbl_questao.config(text=f"Tempo questão: {elapsed}s")
            self._question_job = self.win.after(
                500, self._start_question_timer)
        except:
            pass

    def _stop_timers(self):
        try:
            if hasattr(self, "_total_job") and self._total_job:
                self.win.after_cancel(self._total_job)
        except:
            pass

        try:
            if hasattr(self, "_question_job") and self._question_job:
                self.win.after_cancel(self._question_job)
        except:
            pass

    # =========================================
    # CANCELAR / FECHAR JANELA
    # =========================================
    def _cancelar(self, perguntar=True):
        if perguntar:
            if not messagebox.askyesno(
                    "Cancelar", "Tem certeza que deseja cancelar o teste?"):
                return

        self._stop_timers()
        self.win.destroy()

        if callable(self.on_close):
            self.on_close()
