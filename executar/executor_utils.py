# executor_utils.py
import random
from datetime import datetime


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


# Tempo format HH:MM:SS
def formatar_timedelta(td):
    total = int(td.total_seconds())
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def agora():
    return datetime.now()
