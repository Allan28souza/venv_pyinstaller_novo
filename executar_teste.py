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


def gerar_sequencia_imagens(lista_ids, quantidade=30):
    if not lista_ids:
        return []
    sequencia = []
    ultima = None
    for _ in range(quantidade):
        tentativa = random.choice(lista_ids)
        if len(lista_ids) > 1:
            max_tries = 50
            tries = 0
            while tentativa == ultima and tries < max_tries:
                tentativa = random.choice(lista_ids)
                tries += 1
        sequencia.append(tentativa)
        ultima = tentativa
    return sequencia


class TesteExecutor:
    def __init__(self, root, teste_id, nome_teste, operador_id=None, avaliador=None, turno=None):
        criar_tabelas_if_needed()
        self.root = root
        self.teste_id = teste_id
        self.nome_teste = nome_teste
        self.operador_id = operador_id
        self.avaliador = avaliador
        self.turno = turno

        try:
            cfg = utils.carregar_config()
        except Exception:
            cfg = {"num_questoes": 30, "num_ciclos": 3}
        self.num_questoes = int(cfg.get("num_questoes", 30))
        self.num_ciclos = int(cfg.get("num_ciclos", 3))

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
        # tuples (nome_arquivo, resposta_user, resposta_correta, tempo_s)
        self.respostas_usuario = []
        self.ciclo_atual = 0
        self.indice_atual = 0
        self.sequencia = []

        self._current_photo = None

        self.frame_teste = tk.Frame(root)
        self.frame_teste.pack(expand=True, fill="both")

        self.setup_tela_inicial()

    def setup_tela_inicial(self):
        for w in self.frame_teste.winfo_children():
            w.destroy()
        tk.Label(self.frame_teste, text=f"Teste: {self.nome_teste}", font=(
            "Arial", 16, "bold")).pack(pady=10)
        tk.Label(self.frame_teste, text=f"{self.num_questoes} imagens por ciclo | {self.num_ciclos} ciclos", font=(
            "Arial", 11)).pack(pady=5)

        ttk.Button(self.frame_teste, text="Iniciar Teste",
                   command=self.iniciar_primeiro_ciclo).pack(pady=10)
        if self.operador_id:
            ttk.Label(self.frame_teste,
                      text=f"Operador ID: {self.operador_id}").pack()

        # rodapé
        try:
            utils.criar_rodape(self.root)
        except:
            pass

    def iniciar_primeiro_ciclo(self):
        self.ciclo_atual = 1
        self.iniciar_ciclo()

    def iniciar_ciclo(self):
        self.sequencia = gerar_sequencia_imagens(
            self.lista_ids, quantidade=self.num_questoes)
        self.indice_atual = 0
        for w in self.frame_teste.winfo_children():
            w.destroy()
        self.exibir_imagem()

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
            utils.show_error("Erro", f"Imagem ID {imagem_id} não encontrada")
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

        try:
            img = Image.open(caminho)
            img = img.resize((500, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
        except Exception as e:
            utils.show_error("Erro", f"Erro ao abrir imagem: {e}")
            self.indice_atual += 1
            self.exibir_imagem()
            return

        lbl = tk.Label(self.frame_teste, image=photo)
        lbl.image = photo
        lbl.pack(pady=10)
        self._current_photo = photo

        tk.Label(self.frame_teste,
                 text=f"Imagem {self.indice_atual+1}/{self.num_questoes} | Ciclo {self.ciclo_atual}/{self.num_ciclos}", font=("Arial", 11)).pack(pady=5)

        btn_frame = tk.Frame(self.frame_teste)
        btn_frame.pack(pady=10)

        # start timer
        self.tempo_inicio = datetime.now()

        ttk.Button(btn_frame, text="OK", width=20, command=lambda: self.registrar_resposta(
            nome_arquivo, "OK", resposta_correta)).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="NOK", width=20, command=lambda: self.registrar_resposta(
            nome_arquivo, "NOK", resposta_correta)).pack(side="left", padx=8)

    def registrar_resposta(self, nome_arquivo, resposta_usuario, resposta_correta):
        tempo = int((datetime.now() - self.tempo_inicio).total_seconds())
        self.respostas_usuario.append(
            (nome_arquivo, resposta_usuario, resposta_correta, tempo))
        self.indice_atual += 1
        self.exibir_imagem()

    def finalizar_ciclo(self):
        if self.ciclo_atual < self.num_ciclos:
            self.ciclo_atual += 1
            self.iniciar_ciclo()
        else:
            self.finalizar_teste()

    def finalizar_teste(self):
        total = len(self.respostas_usuario)
        acertos = sum(1 for _, u, c, _ in self.respostas_usuario if u.strip(
        ).upper() == c.strip().upper())
        porcentagem = (acertos/total*100) if total > 0 else 0
        tempo_total = sum(r[3] for r in self.respostas_usuario)
        tempo_medio = (tempo_total/total) if total > 0 else 0

        # salva no DB
        operador_id = self.operador_id
        if not operador_id:
            operador_id = None

        try:
            resultado_id = db.salvar_resultado(
                operador_id=operador_id,
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
            utils.show_error("Erro", f"Falha ao salvar resultado no DB: {e}")
            resultado_id = None

        # prepara lista de erros (para PDF: precisa blob)
        erros_imagens = []
        if any(u.strip().upper() != c.strip().upper() for _, u, c, _ in self.respostas_usuario):
            for nome, u, c, t in self.respostas_usuario:
                if u.strip().upper() != c.strip().upper():
                    # pega blob
                    conn = db.conectar()
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT imagem FROM imagens WHERE nome_arquivo=? AND teste_id=?", (nome, self.teste_id))
                    row = cur.fetchone()
                    conn.close()
                    blob = row[0] if row else b""
                    erros_imagens.append((nome, u, c, blob))

        # gera PDF
        try:
            utils.gerar_relatorio_pdf(
                nome_usuario=db.listar_operadores()[0][1] if operador_id is None else (
                    next((o[1] for o in db.listar_operadores() if o[0] == operador_id), "") or ""),
                matricula="" if operador_id is None else (
                    next((o[2] for o in db.listar_operadores() if o[0] == operador_id), "") or ""),
                turno=self.turno or "",
                acertos=acertos,
                porcentagem=porcentagem,
                erros_imagens=erros_imagens,
                pasta_resultados=None,
                avaliador=self.avaliador,
                tempo_total=tempo_total,
                tempo_medio=tempo_medio
            )
        except Exception as e:
            utils.show_warning("Aviso", f"Erro ao gerar PDF: {e}")

        # mostra resumo
        utils.show_info(
            "Resultado", f"Acertos: {acertos}\nErros: {total-acertos}\nPorcentagem: {porcentagem:.2f}%\nTempo total: {tempo_total}s\nTempo médio: {tempo_medio:.2f}s")
        # volta para tela inicial do app
        self.setup_tela_inicial()


def criar_tabelas_if_needed():
    try:
        db.criar_tabelas()
    except:
        pass
