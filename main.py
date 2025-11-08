import tkinter as tk
from admin import AdminApp
from executar_teste import TesteApp
from database import resource_path  # função para achar arquivos no exe


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Testes com Imagens")
        self.root.geometry("300x200")
        self.centralizar_janela(300, 200)
        self.abrir_tela_inicial()

    def centralizar_janela(self, largura, altura):
        """Centraliza a janela na tela."""
        self.root.update_idletasks()
        largura_tela = self.root.winfo_screenwidth()
        altura_tela = self.root.winfo_screenheight()
        x = (largura_tela // 2) - (largura // 2)
        y = (altura_tela // 2) - (altura // 2)
        self.root.geometry(f"{largura}x{altura}+{x}+{y}")

    def limpar_tela(self):
        """Remove todos os widgets da janela principal."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def abrir_tela_inicial(self):
        """Mostra a tela inicial com os botões Administração e Executar Teste."""
        self.limpar_tela()
        tk.Label(self.root, text="Sistema de Testes",
                 font=("Arial", 14)).pack(pady=10)
        tk.Button(self.root, text="Administração", width=20,
                  command=self.abrir_admin).pack(pady=5)
        tk.Button(self.root, text="Executar Teste", width=20,
                  command=self.iniciar_teste).pack(pady=5)

    def abrir_admin(self):
        """Abre a tela de administração."""
        self.limpar_tela()
        AdminApp(self.root, voltar=self.abrir_tela_inicial)

    def iniciar_teste(self):
        """Abre a tela de execução de testes, pedindo o nome do avaliador."""
        self.limpar_tela()

        tk.Label(self.root, text="Avaliador:").pack(pady=5)
        self.avaliador_var = tk.StringVar()
        tk.Entry(self.root, textvariable=self.avaliador_var).pack(pady=5)

        # Botão para iniciar o teste, passando o avaliador
        tk.Button(self.root, text="Continuar", width=20,
                  command=lambda: self.abrir_teste()).pack(pady=10)

        # Voltar à tela inicial
        tk.Button(self.root, text="Voltar", fg="red",
                  command=self.abrir_tela_inicial).pack(pady=5)

    def abrir_teste(self):
        avaliador = self.avaliador_var.get().strip()
        if not avaliador:
            tk.messagebox.showerror("Erro", "Informe o nome do avaliador!")
            return
        TesteApp(self.root, voltar=self.abrir_tela_inicial, avaliador=avaliador)


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
