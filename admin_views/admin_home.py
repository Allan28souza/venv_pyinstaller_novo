import tkinter as tk
from tkinter import ttk
from utils import centralizar_janela, criar_rodape
import database as db

# Importação dos módulos divididos
from admin_views.testes_admin import TestesAdmin
from admin_views.operadores_admin import OperadoresAdmin
from admin_views.avaliadores_admin import AvaliadoresAdmin
from admin_views.resultados_admin import ResultadosAdmin


class AdminApp:
    def __init__(self, root, voltar=None):
        db.criar_tabelas()
        self.root = root
        self.voltar = voltar

        self.root.title("Motherson Taubaté - Administração")
        centralizar_janela(self.root, 800, 600)

        self.rodape = None
        self.abrir_tela_principal()

    # --------------------------------------------------------
    def limpar_tela(self):
        for w in self.root.winfo_children():
            if self.rodape and w == self.rodape:
                continue
            w.destroy()

    # --------------------------------------------------------
    # TELA PRINCIPAL DO ADMIN
    # --------------------------------------------------------
    def abrir_tela_principal(self):
        self.limpar_tela()

        tk.Label(self.root, text="Painel de Administração",
                 font=("Arial", 16, "bold")).pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        ttk.Button(frame, text="Gerenciar Testes", width=22,
                   command=lambda: TestesAdmin(self)).grid(row=0, column=0, padx=6, pady=6)

        ttk.Button(frame, text="Gerenciar Operadores", width=22,
                   command=lambda: OperadoresAdmin(self)).grid(row=0, column=1, padx=6, pady=6)

        ttk.Button(frame, text="Gerenciar Avaliadores", width=22,
                   command=lambda: AvaliadoresAdmin(self)).grid(row=1, column=0, padx=6, pady=6)

        ttk.Button(frame, text="Resultados", width=22,
                   command=lambda: ResultadosAdmin(self)).grid(row=1, column=1, padx=6, pady=6)

        if self.voltar:
            ttk.Button(self.root, text="Voltar",
                       command=self.voltar).pack(pady=10)

        # rodapé
        if self.rodape:
            try:
                self.rodape.destroy()
            except:
                pass
        self.rodape, _ = criar_rodape(self.root)
