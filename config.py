import os
import sys

# Caminho base considerando PyInstaller ou execução normal
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Caminho do banco de dados
DB_PATH = os.path.join(BASE_DIR, "banco.db")

# Pasta de imagens
IMAGES_DIR = os.path.join(BASE_DIR, "imagens")
os.makedirs(IMAGES_DIR, exist_ok=True)
