# admin.py
import tkinter as tk
from tkinter import ttk
from utils import centralizar_janela, criar_rodape
import database as db

# Importação dos módulos separados
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

        centralizar_janela(self.root, 850, 620)

        self.rodape = None

        self.abrir_tela_principal()

    # ---------------------------------------------------------
    def limpar_tela(self):
        for w in self.root.winfo_children():
            if self.rodape and w == self.rodape:
                continue
            w.destroy()

    # ---------------------------------------------------------
    # TELA PRINCIPAL DO ADMIN
    # ---------------------------------------------------------
    def abrir_tela_principal(self):
        self.limpar_tela()

        tk.Label(self.root, text="Painel de Administração",
                 font=("Arial", 18, "bold")).pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack(pady=20)

        ttk.Button(frame, text="Gerenciar Testes", width=25,
                   command=self.abrir_testes).grid(row=0, column=0, padx=10, pady=10)

        ttk.Button(frame, text="Gerenciar Operadores", width=25,
                   command=self.abrir_operadores).grid(row=0, column=1, padx=10, pady=10)

        ttk.Button(frame, text="Gerenciar Avaliadores", width=25,
                   command=self.abrir_avaliadores).grid(row=1, column=0, padx=10, pady=10)

        ttk.Button(frame, text="Resultados", width=25,
                   command=self.abrir_resultados).grid(row=1, column=1, padx=10, pady=10)

        ttk.Button(frame, text="Importar Banco (.db)", width=25,
                   command=self.importar_banco).grid(row=2, column=0, padx=10, pady=10)

        ttk.Button(frame, text="Exportar Banco (.db)", width=25,
                   command=self.exportar_banco).grid(row=2, column=1, padx=10, pady=10)

        if self.voltar:
            ttk.Button(self.root, text="Voltar", width=20,
                       command=self.voltar).pack(pady=10)

        if self.rodape:
            try:
                self.rodape.destroy()
            except:
                pass
        self.rodape, _ = criar_rodape(self.root)

    # ---------------------------------------------------------
    # ABERTURA DAS TELAS MODULARES
    # ---------------------------------------------------------
    def abrir_testes(self):
        TestesAdmin(self.root, self.abrir_tela_principal)

    def abrir_operadores(self):
        OperadoresAdmin(self.root, self.abrir_tela_principal)

    def abrir_avaliadores(self):
        AvaliadoresAdmin(self.root, self.abrir_tela_principal)

    def abrir_resultados(self):
        ResultadosAdmin(self.root, self.abrir_tela_principal)

    # ---------------------------------------------------------
    # IMPORTAÇÃO / EXPORTAÇÃO DE BANCO
    # ---------------------------------------------------------
    def exportar_banco(self):
        from tkinter import filedialog
        from utils import show_error, show_info

        destino = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite DB", "*.db")],
            parent=self.root
        )
        if not destino:
            return

        try:
            db.exportar_banco(destino)
            show_info("Exportado", f"Banco exportado para:\n{destino}")
        except Exception as e:
            show_error("Erro", f"Falha ao exportar banco:\n{e}")

    def importar_banco(self):
        from tkinter import filedialog
        from utils import show_error, show_info

        arquivo = filedialog.askopenfilename(
            filetypes=[("SQLite DB", "*.db")], parent=self.root)

        if not arquivo:
            return

        try:
            db.importar_banco_mesclar(arquivo, ignorar_duplicados=True)
            show_info("Importado", "Banco mesclado com sucesso!")
        except Exception as e:
            show_error("Erro", f"Falha ao importar: {e}")
