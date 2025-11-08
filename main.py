import tkinter as tk
from admin import AdminApp
from executar_teste import TesteApp
from database import resource_path  # função para achar arquivos no exe


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Testes com Imagens")
        self.root.geometry("300x200")
        self.abrir_tela_inicial()

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
        """Abre a tela de execução de testes."""
        self.limpar_tela()
        TesteApp(self.root, voltar=self.abrir_tela_inicial)


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
