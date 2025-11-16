# executar_teste.py
import utils
import database as db
import os
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ============================================================
# FUNÇÃO: GERAR SEQUÊNCIA (SEM REPETIR CONSECUTIVA)
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
            while tentativa == ultima and tentativas < 30:
                tentativa = random.choice(lista_ids)
                tentativas += 1

        sequencia.append(tentativa)
        ultima = tentativa

    return sequencia


# ============================================================
# CLASSE PRINCIPAL DO TESTE
# ============================================================
class TesteExecutor:
    def __init__(self, root, teste_id, nome_teste,
                 operador_id=None, avaliador=None, turno=None, on_close=None):

        criar_tabelas_if_needed()

        # parâmetros recebidos
        self.root = root
        self.teste_id = teste_id
        self.nome_teste = nome_teste
        self.operador_id = operador_id
        self.avaliador = avaliador
        self.turno = turno
        self.on_close = on_close

        # configuração
        try:
            cfg = utils.carregar_config()
        except:
            cfg = {}

        self.num_questoes = int(cfg.get("num_questoes", 30))
        self.num_ciclos = int(cfg.get("num_ciclos", 3))

        # imagens do teste
        self.imagens = db.listar_imagens(teste_id)
        if not self.imagens:
            utils.show_warning(
                "Aviso", "Nenhuma imagem cadastrada neste teste.")
            try:
                self.root.destroy()
            except:
                pass
            return

        self.lista_ids = [img[0] for img in self.imagens]

        # estado
        self.respostas_usuario = []     # (nome, resp_user, resp_ok, tempo)
        self.ciclo_atual = 0
        self.indice_atual = 0
        self.sequencia = []

        # Interface base
        self.frame_teste = tk.Frame(self.root)
        self.frame_teste.pack(expand=True, fill="both")

        self.setup_tela_inicial()

    # ============================================================
    # TELA INICIAL
    # ============================================================
    def setup_tela_inicial(self):
        for w in self.frame_teste.winfo_children():
            w.destroy()

        tk.Label(self.frame_teste,
                 text=f"Teste: {self.nome_teste}",
                 font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(self.frame_teste,
                 text=f"{self.num_questoes} imagens por ciclo | {self.num_ciclos} ciclos",
                 font=("Arial", 12)).pack(pady=5)

        ttk.Button(self.frame_teste,
                   text="Iniciar Teste",
                   command=self.iniciar_primeiro_ciclo).pack(pady=12)

    # ============================================================
    # CICLOS
    # ============================================================
    def iniciar_primeiro_ciclo(self):
        self.ciclo_atual = 1
        self.iniciar_ciclo()

    def iniciar_ciclo(self):
        self.sequencia = gerar_sequencia_imagens(
            self.lista_ids, self.num_questoes)
        self.indice_atual = 0

        for w in self.frame_teste.winfo_children():
            w.destroy()

        self.exibir_imagem()

    # ============================================================
    # EXIBIR IMAGEM
    # ============================================================
    def exibir_imagem(self):
        for w in self.frame_teste.winfo_children():
            w.destroy()

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

        # carregar imagem
        try:
            img = Image.open(caminho)
            img = img.resize((500, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
        except Exception as e:
            utils.show_error("Erro", f"Erro ao carregar imagem: {e}")
            self.indice_atual += 1
            self.exibir_imagem()
            return

        lbl = tk.Label(self.frame_teste, image=photo)
        lbl.image = photo
        lbl.pack(pady=10)

        tk.Label(self.frame_teste,
                 text=f"Imagem {self.indice_atual+1}/{self.num_questoes} | Ciclo {self.ciclo_atual}/{self.num_ciclos}",
                 font=("Arial", 11)).pack(pady=5)

        self.tempo_inicio = datetime.now()

        bt_frame = tk.Frame(self.frame_teste)
        bt_frame.pack(pady=10)

        ttk.Button(bt_frame, text="OK", width=20,
                   command=lambda: self.registrar_resposta(nome_arquivo, "OK", resposta_correta)).pack(side="left", padx=8)

        ttk.Button(bt_frame, text="NOK", width=20,
                   command=lambda: self.registrar_resposta(nome_arquivo, "NOK", resposta_correta)).pack(side="left", padx=8)

    # ============================================================
    # REGISTRAR RESPOSTA
    # ============================================================
    def registrar_resposta(self, nome_arquivo, resposta_usuario, resposta_correta):
        tempo = int((datetime.now() - self.tempo_inicio).total_seconds())
        self.respostas_usuario.append(
            (nome_arquivo, resposta_usuario, resposta_correta, tempo))
        self.indice_atual += 1
        self.exibir_imagem()

    # ============================================================
    # FINALIZAR CICLO
    # ============================================================
    def finalizar_ciclo(self):
        if self.ciclo_atual < self.num_ciclos:
            self.ciclo_atual += 1
            self.iniciar_ciclo()
        else:
            self.finalizar_teste()

    # ============================================================
    # FINALIZAR TESTE
    # ============================================================
    def finalizar_teste(self):
        total = len(self.respostas_usuario)
        acertos = sum(1 for _, u, c, _ in self.respostas_usuario if u.upper(
        ).strip() == c.upper().strip())
        porcentagem = (acertos / total) * 100 if total > 0 else 0
        tempo_total = sum(r[3] for r in self.respostas_usuario)
        tempo_medio = tempo_total / total if total > 0 else 0

        # ============================
        # salvar no banco
        # ============================
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

        # ============================
        # coletar erros p/ PDF
        # ============================
        erros_imagens = []
        for nome, u, c, _ in self.respostas_usuario:
            if u.upper().strip() != c.upper().strip():
                blob = db.buscar_blob_imagem(nome, self.teste_id)
                erros_imagens.append((nome, u, c, blob))

        # ============================
        # obter dados do operador
        # ============================
        nome_operador, matricula_operador, turno_operador = db.obter_dados_operador(
            self.operador_id)

        # ============================
        # gerar PDF
        # ============================
        utils.gerar_relatorio_pdf(
            nome_usuario=nome_operador,
            matricula=matricula_operador,
            turno=turno_operador,
            acertos=acertos,
            porcentagem=porcentagem,
            erros_imagens=erros_imagens,
            avaliador=self.avaliador,
            tempo_total=tempo_total,
            tempo_medio=tempo_medio
        )

        utils.show_info(
            "Resultado",
            f"Acertos: {acertos}\n"
            f"Erros: {total - acertos}\n"
            f"Porcentagem: {porcentagem:.2f}%\n"
            f"Tempo total: {tempo_total}s\n"
            f"Tempo médio: {tempo_medio:.2f}s"
        )

        # VOLTAR À TELA PRINCIPAL
        if self.on_close:
            self.on_close()


# ============================================================
# GARANTIR CRIAÇÃO DAS TABELAS
# ============================================================
def criar_tabelas_if_needed():
    try:
        db.criar_tabelas()
    except:
        pass
