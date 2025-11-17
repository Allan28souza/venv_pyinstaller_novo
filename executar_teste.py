# executar_teste.py
import utils
import database as db
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ============================================================
# GERAR SEQUÊNCIA (SEM REPETIÇÃO CONSECUTIVA)
# ============================================================
def gerar_sequencia_imagens(lista_ids, quantidade=30):
    if not lista_ids:
        return []

    sequencia = []
    ultima = None

    for _ in range(quantidade):
        tentativa = random.choice(lista_ids)

        if len(lista_ids) > 1:
            tentativas = 0
            while tentativa == ultima and tentativas < 50:
                tentativa = random.choice(lista_ids)
                tentativas += 1

        sequencia.append(tentativa)
        ultima = tentativa

    return sequencia


# ============================================================
# CLASSE PRINCIPAL DO TESTE
# - abre uma janela Toplevel separada
# - cabeçalho, cronômetro total e por questão
# - botão cancelar
# - salva tempos por questão no DB
# ============================================================
class TesteExecutor:
    def __init__(self, root, teste_id, nome_teste,
                 operador_id=None, avaliador=None, turno=None, on_close=None):

        criar_tabelas_if_needed()

        # parâmetros
        self.root = root
        self.teste_id = teste_id
        self.nome_teste = nome_teste
        self.operador_id = operador_id
        self.avaliador = avaliador
        self.turno = turno
        self.on_close = on_close

        # carregar config (fallbacks se utils.carregar_config não existir)
        try:
            cfg = utils.carregar_config()
        except Exception:
            cfg = {}
        self.num_questoes = int(cfg.get("num_questoes", 30))
        self.num_ciclos = int(cfg.get("num_ciclos", 3))

        # carregar imagens do DB (tuplas: id, nome_arquivo, resposta_correta)
        self.imagens = db.listar_imagens(teste_id)
        if not self.imagens:
            utils.show_warning(
                "Aviso", "Nenhuma imagem cadastrada neste teste.")
            return

        self.lista_ids = [img[0] for img in self.imagens]

        # estado do teste
        # respostas_usuario: list of tuples (nome_arquivo, resposta_usuario, resposta_correta, tempo_s)
        self.respostas_usuario = []
        self.ciclo_atual = 0
        self.indice_atual = 0
        self.sequencia = []

        # referências para imagens (evitar garbage collection)
        self._current_photo = None

        # criar janela própria (Toplevel) para o teste
        self.win = tk.Toplevel(self.root)
        self.win.title(f"Executar Teste - {self.nome_teste}")

        # === MAXIMIZAR JANELA DO TESTE ===
        try:
            self.win.state("zoomed")  # Windows
        except:
            try:
                self.win.attributes("-zoomed", True)  # Linux
            except:
                w = self.win.winfo_screenwidth()
                h = self.win.winfo_screenheight()
                self.win.geometry(f"{w}x{h}+0+0")

        # cabeçalho (modelo simples e limpo)
        self.header_frame = tk.Frame(self.win, bd=1, relief=tk.FLAT, pady=6)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(self.header_frame, text="Motherson Taubaté",
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=8)
        tk.Label(self.header_frame, text=self.nome_teste,
                 font=("Arial", 11)).pack(side=tk.LEFT, padx=12)

        # cronômetros (total e questão)
        self.timers_frame = tk.Frame(self.win)
        self.timers_frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=4)
        self.total_time_label = tk.Label(
            self.timers_frame, text="Tempo total: 00:00:00", font=("Arial", 10))
        self.total_time_label.pack(side=tk.LEFT, padx=8)
        self.question_time_label = tk.Label(
            self.timers_frame, text="Tempo questão: 0s", font=("Arial", 10))
        self.question_time_label.pack(side=tk.LEFT, padx=12)

        # área principal do teste
        self.frame_teste = tk.Frame(self.win)
        self.frame_teste.pack(expand=True, fill="both", padx=8, pady=8)

        # barra de ações inferiores
        self.footer_frame = tk.Frame(self.win)
        self.footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=6)
        ttk.Button(self.footer_frame, text="Cancelar Teste",
                   command=self._cancelar_teste).pack(side=tk.LEFT, padx=8)
        ttk.Button(self.footer_frame, text="Fechar",
                   command=self._fechar_sem_salvar).pack(side=tk.RIGHT, padx=8)

        # controle dos timers
        self._total_start = None
        self._question_start = None
        self._timer_job = None
        self._total_job = None

        # iniciar tela inicial do teste
        self.setup_tela_inicial()

        # fechar janela limpa timers e chama on_close
        self.win.protocol("WM_DELETE_WINDOW", self._on_window_close)

    # -------------------------
    # Tela inicial
    # -------------------------
    def setup_tela_inicial(self):
        for w in self.frame_teste.winfo_children():
            w.destroy()

        tk.Label(self.frame_teste, text=f"Teste: {self.nome_teste}", font=(
            "Arial", 16, "bold")).pack(pady=8)
        tk.Label(self.frame_teste, text=f"{self.num_questoes} imagens por ciclo | {self.num_ciclos} ciclos", font=(
            "Arial", 11)).pack(pady=4)

        start_btn = ttk.Button(
            self.frame_teste, text="Iniciar Teste", command=self.iniciar_primeiro_ciclo)
        start_btn.pack(pady=12)

        # info operador/avaliador/turno
        info = f"Operador ID: {self.operador_id or '-'}   Avaliador: {self.avaliador or '-'}   Turno: {self.turno or '-'}"
        tk.Label(self.frame_teste, text=info, font=(
            "Arial", 9, "italic")).pack(pady=6)

    # -------------------------
    # Ciclos do teste
    # -------------------------
    def iniciar_primeiro_ciclo(self):
        self.ciclo_atual = 1
        self.respostas_usuario = []
        # start total timer
        self._total_start = datetime.now()
        self._start_total_timer()
        self.iniciar_ciclo()

    def iniciar_ciclo(self):
        # gera sequência para o ciclo atual
        self.sequencia = gerar_sequencia_imagens(
            self.lista_ids, self.num_questoes)
        self.indice_atual = 0
        for w in self.frame_teste.winfo_children():
            w.destroy()
        self.exibir_imagem()

    # -------------------------
    # Exibir imagem e controls
    # -------------------------
    def exibir_imagem(self):
        # limpa área
        for w in self.frame_teste.winfo_children():
            w.destroy()

        # se acabou o ciclo atual
        if self.indice_atual >= self.num_questoes:
            self.finalizar_ciclo()
            return

        imagem_id = self.sequencia[self.indice_atual]
        dados = next(
            (img for img in self.imagens if img[0] == imagem_id), None)
        if not dados:
            utils.show_error("Erro", "Imagem não encontrada no banco!")
            self.indice_atual += 1
            self.exibir_imagem()
            return

        _, nome_arquivo, resposta_correta = dados
        caminho = db.extrair_imagem_temp(imagem_id)
        if not caminho or not os.path.exists(caminho):
            utils.show_error("Erro", f"Arquivo não encontrado: {nome_arquivo}")
            self.indice_atual += 1
            self.exibir_imagem()
            return

        # carregar imagem (tratamento de erro)
        try:
            img = Image.open(caminho)
            img = img.resize((640, 480), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
        except Exception as e:
            utils.show_error("Erro", f"Erro ao carregar imagem: {e}")
            self.indice_atual += 1
            self.exibir_imagem()
            return

        # exibir
        lbl_img = tk.Label(self.frame_teste, image=photo)
        lbl_img.image = photo  # referência para evitar GC
        lbl_img.pack(pady=6)
        self._current_photo = photo

        tk.Label(self.frame_teste,
                 text=f"Imagem {self.indice_atual+1}/{self.num_questoes}   |   Ciclo {self.ciclo_atual}/{self.num_ciclos}", font=("Arial", 11)).pack(pady=6)

        # botões OK / NOK
        btn_frame = tk.Frame(self.frame_teste)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="OK", width=20, command=lambda: self.registrar_resposta(
            nome_arquivo, "OK", resposta_correta)).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="NOK", width=20, command=lambda: self.registrar_resposta(
            nome_arquivo, "NOK", resposta_correta)).pack(side="left", padx=8)

        # começar cronômetro da questão
        self._question_start = datetime.now()
        self._start_question_timer()

    # -------------------------
    # Timer helpers
    # -------------------------
    def _start_question_timer(self):
        # atualiza label de questão a cada 0.5s
        if hasattr(self, "_question_start") and self._question_start:
            elapsed = int(
                (datetime.now() - self._question_start).total_seconds())
            self.question_time_label.config(text=f"Tempo questão: {elapsed}s")
            # salva job id para cancelar quando necessário
            self._timer_job = self.win.after(500, self._start_question_timer)

    def _start_total_timer(self):
        if self._total_start:
            elapsed = datetime.now() - self._total_start
            # format HH:MM:SS
            total_str = str(timedelta(seconds=int(elapsed.total_seconds())))
            self.total_time_label.config(text=f"Tempo total: {total_str}")
            self._total_job = self.win.after(1000, self._start_total_timer)

    def _stop_timers(self):
        if getattr(self, "_timer_job", None):
            try:
                self.win.after_cancel(self._timer_job)
            except Exception:
                pass
            self._timer_job = None
        if getattr(self, "_total_job", None):
            try:
                self.win.after_cancel(self._total_job)
            except Exception:
                pass
            self._total_job = None

    # -------------------------
    # Registrar resposta
    # -------------------------
    def registrar_resposta(self, nome_arquivo, resposta_usuario, resposta_correta):
        # para o timer da questão e calcula tempo
        if self._question_start:
            tempo = int(
                (datetime.now() - self._question_start).total_seconds())
        else:
            tempo = 0

        # registra (nome, resp_user, resp_ok, tempo_s)
        self.respostas_usuario.append(
            (nome_arquivo, resposta_usuario, resposta_correta, tempo))

        # cancela job do timer atual (será reiniciado na próxima questão)
        if getattr(self, "_timer_job", None):
            try:
                self.win.after_cancel(self._timer_job)
            except Exception:
                pass
            self._timer_job = None
        self._question_start = None
        self.question_time_label.config(text="Tempo questão: 0s")

        self.indice_atual += 1
        # mostrar próxima imagem
        self.exibir_imagem()

    # -------------------------
    # Finalizar ciclo / teste
    # -------------------------
    def finalizar_ciclo(self):
        if self.ciclo_atual < self.num_ciclos:
            self.ciclo_atual += 1
            self.iniciar_ciclo()
        else:
            self.finalizar_teste()

    def finalizar_teste(self):
        # para timers
        self._stop_timers()

        total = len(self.respostas_usuario)
        acertos = sum(1 for _, u, c, _ in self.respostas_usuario if u.upper(
        ).strip() == c.upper().strip())
        porcentagem = (acertos / total) * 100 if total > 0 else 0
        tempo_total = int((datetime.now() - self._total_start).total_seconds()
                          ) if self._total_start else sum(r[3] for r in self.respostas_usuario)
        tempo_medio = (tempo_total / total) if total > 0 else 0

        # salvar no DB (tratando exceções)
        try:
            db.salvar_resultado(
                operador_id=self.operador_id,
                teste_id=self.teste_id,
                avaliador=self.avaliador or "",
                acertos=acertos,
                total=total,
                porcentagem=porcentagem,
                tempo_total=tempo_total,
                tempo_medio=tempo_medio,
                respostas_list=self.respostas_usuario
            )
        except Exception as e:
            utils.show_warning("Aviso", f"Falha ao salvar resultado: {e}")

        # preparar lista de erros com blobs para o PDF
        erros_imagens = []
        for nome, u, c, _ in self.respostas_usuario:
            if u.upper().strip() != c.upper().strip():
                try:
                    blob = db.buscar_blob_imagem(nome, self.teste_id)
                except Exception:
                    blob = b""
                erros_imagens.append((nome, u, c, blob))

        # obter dados do operador com fallback se função não existir ou retornar formatos variados
        nome_operador = ""
        matricula_operador = ""
        turno_operador = self.turno or ""
        try:
            dados_op = db.obter_dados_operador(self.operador_id)
            if dados_op:
                # aceitar tuplas (id, nome, matricula, turno) ou (nome, matricula, turno)
                if len(dados_op) == 4:
                    _, nome_operador, matricula_operador, turno_operador = dados_op
                elif len(dados_op) == 3:
                    nome_operador, matricula_operador, turno_operador = dados_op
                else:
                    # pegues os dois primeiros se possível
                    nome_operador = str(dados_op[0])
                    matricula_operador = str(
                        dados_op[1]) if len(dados_op) > 1 else ""
        except Exception:
            pass

        # gerar PDF (captura exceções)
        try:
            utils.gerar_relatorio_pdf(
                nome_usuario=nome_operador or "",
                matricula=matricula_operador or "",
                turno=turno_operador or "",
                acertos=acertos,
                porcentagem=porcentagem,
                erros_imagens=erros_imagens,
                avaliador=self.avaliador or "",
                tempo_total=tempo_total,
                tempo_medio=tempo_medio
            )
        except Exception as e:
            utils.show_warning("Aviso", f"Erro ao gerar PDF: {e}")

        # resumo na UI
        utils.show_info(
            "Resultado",
            f"Acertos: {acertos}\n"
            f"Erros: {total - acertos}\n"
            f"Porcentagem: {porcentagem:.2f}%\n"
            f"Tempo total: {tempo_total}s\n"
            f"Tempo médio: {tempo_medio:.2f}s"
        )

        # fecha janela e chama callback on_close
        try:
            self.win.destroy()
        except Exception:
            pass
        if callable(self.on_close):
            try:
                self.on_close()
            except Exception:
                pass

    # -------------------------
    # Cancel / fechar sem salvar
    # -------------------------
    def _cancelar_teste(self):
        if not messagebox.askyesno("Confirmar", "Deseja cancelar o teste? Os dados não salvos serão descartados.", parent=self.win):
            return
        # parar timers e fechar (não salva)
        self._stop_timers()
        try:
            self.win.destroy()
        except Exception:
            pass
        if callable(self.on_close):
            try:
                self.on_close()
            except Exception:
                pass

    def _fechar_sem_salvar(self):
        # mesmo comportamento de cancelar
        self._cancelar_teste()

    def _on_window_close(self):
        # intercepta fechar janela (equivalente a cancelar)
        self._cancelar_teste()


# ============================================================
# garantir criação de tabelas
# ============================================================
def criar_tabelas_if_needed():
    try:
        db.criar_tabelas()
    except Exception:
        # não fazer nada: supõe que DB já esteja ok
        pass
