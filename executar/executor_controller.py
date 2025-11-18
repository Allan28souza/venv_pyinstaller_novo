# executor_controller.py
import database as db
import utils
from datetime import datetime, timedelta
from .executor_utils import gerar_sequencia_imagens


class TesteController:
    def __init__(self, teste_id, operador_id, avaliador, turno, num_questoes, num_ciclos):
        self.teste_id = teste_id
        self.operador_id = operador_id
        self.avaliador = avaliador
        self.turno = turno
        self.num_questoes = num_questoes
        self.num_ciclos = num_ciclos

        self.imagens = db.listar_imagens(teste_id)
        self.lista_ids = [img[0] for img in self.imagens]

        self.respostas_usuario = []
        self.ciclo_atual = 1
        self.indice_atual = 0
        self.sequencia = []

        self.inicio_total = None
        self.inicio_questao = None

    # ================================
    # Preparação do teste
    # ================================
    def iniciar(self):
        self.respostas_usuario = []
        self.ciclo_atual = 1
        self.inicio_total = datetime.now()
        self.novo_ciclo()

    def novo_ciclo(self):
        self.sequencia = gerar_sequencia_imagens(
            self.lista_ids, self.num_questoes)
        self.indice_atual = 0

    # ================================
    # Dados da imagem
    # ================================
    def get_info_imagem(self):
        imagem_id = self.sequencia[self.indice_atual]
        return next(img for img in self.imagens if img[0] == imagem_id)

    def avancar(self):
        self.indice_atual += 1

    def ciclo_finalizado(self):
        return self.indice_atual >= self.num_questoes

    def teste_finalizado(self):
        return self.ciclo_atual > self.num_ciclos

    # ================================
    # Registrar resposta
    # ================================
    def registrar_resposta(self, nome_arquivo, resp_user, resp_correta, tempo):
        self.respostas_usuario.append(
            (nome_arquivo, resp_user, resp_correta, tempo))

    # ================================
    # Finalização
    # ================================
    def calcular_resultados(self):
        total = len(self.respostas_usuario)
        acertos = sum(1 for _, u, c, _ in self.respostas_usuario if u == c)
        porcentagem = (acertos / total * 100) if total else 0
        tempo_total = int((datetime.now() - self.inicio_total).total_seconds())
        tempo_medio = tempo_total / total if total else 0
        return acertos, total, porcentagem, tempo_total, tempo_medio

    def salvar_no_banco(self):
        acertos, total, porcentagem, tempo_total, tempo_medio = self.calcular_resultados()

        db.salvar_resultado(
            operador_id=self.operador_id,
            teste_id=self.teste_id,
            avaliador=self.avaliador or "",
            acertos=acertos,
            total=total,
            porcentagem=porcentagem,
            tempo_total=tempo_total,
            tempo_medio=tempo_medio,
            respostas_list=self.respostas_usuario,
            repeticao=self.ciclo_atual
        )

        return acertos, total, porcentagem, tempo_total, tempo_medio

    def avancar_ciclo(self):
        self.ciclo_atual += 1
        self.novo_ciclo()
