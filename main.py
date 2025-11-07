import tkinter as tk
from admin import AdminApp
from executar_teste import TesteApp
from database import resource_path  # função para achar arquivos no exe

# Janela principal
root = tk.Tk()
root.title("Sistema de Testes com Imagens")
root.geometry("300x200")


def limpar_tela():
    """Remove todos os widgets da janela principal."""
    for widget in root.winfo_children():
        widget.destroy()


def abrir_tela_inicial():
    """Mostra a tela inicial com os botões Administração e Executar Teste."""
    limpar_tela()
    tk.Label(root, text="Sistema de Testes", font=("Arial", 14)).pack(pady=10)
    tk.Button(root, text="Administração", width=20,
              command=abrir_admin).pack(pady=5)
    tk.Button(root, text="Executar Teste", width=20,
              command=abrir_teste).pack(pady=5)


def abrir_admin():
    """Mostra a tela de administração no root."""
    limpar_tela()
    # Passa root e função de voltar para AdminApp
    AdminApp(root, voltar=abrir_tela_inicial)


def abrir_teste():
    """Mostra a tela de execução de teste no root."""
    limpar_tela()
    # Passa root e função de voltar para TesteApp
    TesteApp(root, voltar=abrir_tela_inicial)


# Inicializa com a tela principal
abrir_tela_inicial()
root.mainloop()
