# config.py
import os
import sys

# Número padrão de questões por teste
NUM_QUESTOES = 10

# Pasta onde os resultados CSV e PDF serão salvos
PASTA_RESULTADOS = os.path.join(os.path.abspath("."), "resultados")
os.makedirs(PASTA_RESULTADOS, exist_ok=True)

# Configuração de banco de dados


def get_db_path():
    """
    Retorna o caminho do banco de dados.
    Se estiver executando como .exe (PyInstaller), salva em APPDATA/TesteImagensApp.
    Caso contrário, salva na pasta atual.
    """
    if getattr(sys, 'frozen', False):  # Executável (PyInstaller)
        base_dir = os.path.join(os.environ.get(
            "APPDATA", os.path.expanduser("~")), "TesteImagensApp")
    else:
        base_dir = os.path.abspath(".")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "testes.db")


DB_PATH = get_db_path()

# Configurações de interface
JANELA_LARGURA = 600
JANELA_ALTURA = 500
IMAGEM_WIDTH = 400
IMAGEM_HEIGHT = 300

# Configurações de PDF
PDF_THUMB_MAX_W_CM = 6.5
PDF_THUMB_MAX_H_CM = 5
PDF_GAP_Y_CM = 0.6
