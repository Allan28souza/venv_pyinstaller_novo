# admin.py modernizado com layout mais moderno
import tkinter as tk
from tkinter import ttk
from utils import centralizar_janela, criar_rodape
import database as db
from executar.executor_rr_view import RRView

# Importações dos módulos
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
        centralizar_janela(self.root, 900, 650)

        # Tema moderno (azure)
        try:
            self.root.tk.call("source", "azure.tcl")
            self.root.tk.call("set_theme", "light")
        except Exception:
            pass

        self.rodape = None
        self.abrir_tela_principal()

    # -------------------------------------------
    def limpar_tela(self):
        for w in self.root.winfo_children():
            if self.rodape and w == self.rodape:
                continue
            w.destroy()

    # -------------------------------------------
    def abrir_tela_principal(self):
        self.limpar_tela()

        header = tk.Frame(self.root, bg="#2e3f4f", height=70)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Painel de Administração",
            bg="#2e3f4f",
            fg="white",
            font=("Segoe UI", 20, "bold")
        ).pack(side="left", padx=25, pady=10)

        # Container principal com fundo suave
        container = tk.Frame(self.root, bg="#eef1f5")
        container.pack(expand=True, fill="both", padx=20, pady=20)

        # Grade moderna de botões tipo "cards"
        style = ttk.Style()
        style.configure(
            "Card.TButton",
            font=("Segoe UI", 12, "bold"),
            padding=8
        )

        botoes = [
            ("Gerenciar Testes", self.abrir_testes),
            ("Gerenciar Operadores", self.abrir_operadores),
            ("Gerenciar Avaliadores", self.abrir_avaliadores),
            ("Resultados", self.abrir_resultados),
            ("Importar Banco (.db)", self.importar_banco),
            ("Exportar Banco (.db)", self.exportar_banco),
            ("Análises RR (R&R)", self.abrir_rr)
        ]

        grid = tk.Frame(container, bg="#eef1f5")
        grid.pack(pady=20)

        # Criar cards em grade 3xN
        col = 0
        row = 0
        for texto, func in botoes:
            card = tk.Frame(grid, bg="white", bd=1, relief="solid")
            card.grid(row=row, column=col, padx=12, pady=12, ipadx=2, ipady=2)

            ttk.Button(card, text=texto, width=18, style="Card.TButton",
                       command=func).pack(padx=10, pady=12)

            col += 1
            if col > 2:
                col = 0
                row += 1

        # Botão voltar
        if self.voltar:
            ttk.Button(self.root, text="Voltar", width=20,
                       command=self.voltar).pack(pady=10)

        # rodapé
        if self.rodape:
            try:
                self.rodape.destroy()
            except:
                pass
        self.rodape, _ = criar_rodape(self.root)

    # -------------------------------------------
    def abrir_testes(self):
        TestesAdmin(self.root, self.abrir_tela_principal)

    def abrir_operadores(self):
        OperadoresAdmin(self.root, self.abrir_tela_principal)

    def abrir_avaliadores(self):
        AvaliadoresAdmin(self.root, self.abrir_tela_principal)

    def abrir_resultados(self):
        ResultadosAdmin(self.root, self.abrir_tela_principal)

    # -------------------------------------------
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

    # -------------------------------------------
    def abrir_rr(self):
        RRView(self.root)
