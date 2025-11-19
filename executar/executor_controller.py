import database as db
import utils
import random
from datetime import datetime, timedelta


# ============================================================
# NOVA LÓGICA RR — DISTRIBUIÇÃO EQUILIBRADA POR CICLO
# ============================================================
def gerar_ciclo_sem_repeticao_equilibrado(lista_ids, tamanho_ciclo=30):
    """
    Regra RR:
    - Nunca repetir imagem dentro do ciclo se houver ≥ tamanho_ciclo imagens.
    - Se houver menos, repetir de forma equilibrada.
    """
    total = len(lista_ids)

    if total == 0:
        return []

    # Caso 1: tem imagens suficientes → sem repetição
    if total >= tamanho_ciclo:
        return random.sample(lista_ids, tamanho_ciclo)

    # Caso 2: menos imagens → repetir equilibrado
    vezes = tamanho_ciclo // total
    faltantes = tamanho_ciclo % total

    ciclo = []

    # cada imagem aparece "vezes" vezes
    for img in lista_ids:
        ciclo.extend([img] * vezes)

    # adicionar repetição extra equilibrada
    extras = random.sample(lista_ids, faltantes)
    ciclo.extend(extras)

    # embaralha ciclo
    random.shuffle(ciclo)
    return ciclo


# ============================================================
# CONTROLLER DO TESTE
# ============================================================
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

    # ===============================================
    # INÍCIO DO TESTE
    # ===============================================
    def iniciar(self):
        self.respostas_usuario = []
        self.ciclo_atual = 1
        self.inicio_total = datetime.now()
        self.novo_ciclo()

    def novo_ciclo(self):
        self.sequencia = gerar_ciclo_sem_repeticao_equilibrado(
            self.lista_ids, self.num_questoes
        )
        self.indice_atual = 0

    # ===============================================
    # DADOS DA IMAGEM
    # ===============================================
    def get_info_imagem(self):
        imagem_id = self.sequencia[self.indice_atual]
        return next(img for img in self.imagens if img[0] == imagem_id)

    def avancar(self):
        self.indice_atual += 1

    def ciclo_finalizado(self):
        return self.indice_atual >= self.num_questoes

    def teste_finalizado(self):
        return self.ciclo_atual > self.num_ciclos

    # ===============================================
    # REGISTRAR RESPOSTA
    # ===============================================
    def registrar_resposta(self, nome_arquivo, resp_user, resp_correta, tempo):
        self.respostas_usuario.append(
            (nome_arquivo, resp_user, resp_correta, tempo))

    # ===============================================
    # FINALIZAÇÃO
    # ===============================================
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
