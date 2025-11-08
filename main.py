import tkinter as tk
from admin import AdminApp
from executar_teste import TesteApp
from utils import centralizar_janela, criar_rodape, show_error


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Motherson Taubaté - Sistema de Testes com Imagens")
        self.root.geometry("400x250")
        centralizar_janela(self.root, 350, 250)

        self.avaliador_var = tk.StringVar()
        self.rodape_frame = None  # armazenará o frame
        self.hora_label = None    # armazenará o label da hora

        self.abrir_tela_inicial()

    def limpar_tela(self):
        """Remove todos os widgets da tela e o rodapé antigo."""
        for widget in self.root.winfo_children():
            widget.destroy()
        if self.rodape_frame:
            self.rodape_frame.destroy()
            self.rodape_frame = None
            self.hora_label = None

    def abrir_tela_inicial(self):
        self.limpar_tela()
        tk.Label(self.root, text="Sistema de Testes",
                 font=("Arial", 14)).pack(pady=10)
        tk.Button(self.root, text="Administração", width=25,
                  command=self.abrir_admin).pack(pady=5)
        tk.Button(self.root, text="Executar Teste", width=25,
                  command=self.iniciar_teste).pack(pady=5)
        self.rodape_frame, self.hora_label = criar_rodape(self.root)

    def abrir_admin(self):
        self.limpar_tela()
        AdminApp(self.root, voltar=self.abrir_tela_inicial)
        self.rodape_frame, self.hora_label = criar_rodape(self.root)

    def iniciar_teste(self):
        self.limpar_tela()
        tk.Label(self.root, text="Avaliador:").pack(pady=5)
        tk.Entry(self.root, textvariable=self.avaliador_var).pack(pady=5)
        tk.Button(self.root, text="Continuar", width=25,
                  command=self.abrir_teste).pack(pady=10)
        tk.Button(self.root, text="Voltar", fg="red",
                  command=self.abrir_tela_inicial).pack(pady=5)
        self.rodape_frame, self.hora_label = criar_rodape(self.root)

    def abrir_teste(self):
        avaliador = self.avaliador_var.get().strip()
        if not avaliador:
            show_error("Erro", "Informe o nome do avaliador!")
            return
        TesteApp(self.root, voltar=self.abrir_tela_inicial, avaliador=avaliador)


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
