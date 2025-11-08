# utils.py
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import os
import platform
import subprocess

VERSAO = "v1.0"
PRODUTOR = "Allan Fonseca"

# ----------------------------
# Centralizar janela
# ----------------------------


def centralizar_janela(root, largura, altura):
    """Centraliza a janela na tela."""
    root.update_idletasks()
    largura_tela = root.winfo_screenwidth()
    altura_tela = root.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    root.geometry(f"{largura}x{altura}+{x}+{y}")


# ----------------------------
# Criar rodapé padronizado
# ----------------------------
def criar_rodape(root):
    """
    Cria um rodapé com Motherson SAS à esquerda e versão/hora à direita.
    Retorna o frame e o label da hora (para atualizar ou destruir depois).
    """
    rodape_frame = tk.Frame(root, height=25, bg="#f0f0f0")
    rodape_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # esquerda
    tk.Label(
        rodape_frame,
        text=f"Motherson SAS - {PRODUTOR}",
        font=("Arial", 8),
        bg="#f0f0f0"
    ).pack(side=tk.LEFT, padx=5)

    # direita
    hora_label = tk.Label(
        rodape_frame,
        text=f"{VERSAO} - {datetime.now().strftime('%H:%M:%S')}",
        font=("Arial", 8),
        bg="#f0f0f0"
    )
    hora_label.pack(side=tk.RIGHT, padx=5)

    def atualizar_hora():
        # só atualiza se o label ainda existir
        if hora_label.winfo_exists():
            hora_label.config(
                text=f"{VERSAO} - {datetime.now().strftime('%H:%M:%S')}"
            )
            root.after(1000, atualizar_hora)

    atualizar_hora()
    return rodape_frame, hora_label


# ----------------------------
# MessageBoxes padronizados
# ----------------------------
def show_info(titulo, mensagem):
    messagebox.showinfo(f"Motherson Taubaté - {titulo}", mensagem)


def show_error(titulo, mensagem):
    messagebox.showerror(f"Motherson Taubaté - {titulo}", mensagem)


def show_warning(titulo, mensagem):
    messagebox.showwarning(f"Motherson Taubaté - {titulo}", mensagem)


# ----------------------------
# Abrir pasta cross-platform
# ----------------------------
def abrir_pasta(path):
    try:
        sistema = platform.system()
        if sistema == "Windows":
            os.startfile(path)
        elif sistema == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        show_warning("Aviso", f"Não foi possível abrir a pasta: {e}")
