# main.py
import tkinter as tk
from tkinter import ttk
from admin_views.admin import AdminApp
from executar_teste import TesteExecutor
import database as db
from utils import centralizar_janela, criar_rodape, show_error


class MainApp:
    def __init__(self, root):
        db.criar_tabelas()
        self.root = root
        self.root.title("Motherson Taubaté - Sistema de Testes com Imagens")
        self.root.geometry("420x320")
        centralizar_janela(self.root, 420, 320)

        self.rodape_frame = None
        self.hora_label = None

        self.abrir_tela_inicial()

    def limpar_tela(self):
        for w in self.root.winfo_children():
            w.destroy()

    def abrir_tela_inicial(self):
        self.limpar_tela()

        tk.Label(self.root, text="Sistema de Testes",
                 font=("Arial", 14)).pack(pady=8)

        tk.Button(self.root, text="Administração", width=28,
                  command=self.abrir_admin).pack(pady=6)
        tk.Button(self.root, text="Executar Teste", width=28,
                  command=self.iniciar_teste).pack(pady=6)

        if self.rodape_frame:
            try:
                self.rodape_frame.destroy()
            except:
                pass

        self.rodape_frame, self.hora_label = criar_rodape(self.root)

    def abrir_admin(self):
        self.limpar_tela()
        AdminApp(self.root, voltar=self.abrir_tela_inicial)

    # ---------------------------------------------------
    # TELA DE ENTRADA DO OPERADOR / AVALIADOR
    # ---------------------------------------------------
    def iniciar_teste(self):
        self.limpar_tela()

        tk.Label(self.root, text="Nome do Operador:").pack(pady=3)
        nome_var = tk.StringVar()
        tk.Entry(self.root, textvariable=nome_var).pack()

        tk.Label(self.root, text="Matrícula:").pack(pady=3)
        mat_var = tk.StringVar()
        tk.Entry(self.root, textvariable=mat_var).pack()

        tk.Label(self.root, text="Turno:").pack(pady=3)
        turnos = db.listar_turnos()
        turno_cb = ttk.Combobox(self.root, values=turnos, state="readonly")
        if turnos:
            turno_cb.current(0)
        turno_cb.pack()

        tk.Label(self.root, text="Avaliador:").pack(pady=3)
        avaliadores = db.listar_avaliadores()
        avaliador_cb = ttk.Combobox(
            self.root, values=avaliadores, state="readonly")
        if avaliadores:
            avaliador_cb.current(0)
        avaliador_cb.pack()

        # -------------------------
        # Continuar → selecionar teste
        # -------------------------
        def continuar():
            nome = nome_var.get().strip()
            mat = mat_var.get().strip()
            turno = turno_cb.get().strip()
            avaliador = avaliador_cb.get().strip()

            if not nome or not mat:
                show_error("Erro", "Informe nome e matrícula do operador!")
                return

            # garante operador
            op_id = db.garantir_operador(nome, mat, turno)

            # garante avaliador, se selecionado
            if avaliador:
                db.garantir_avaliador(avaliador)

            # Buscar testes cadastrados
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM testes ORDER BY nome")
            testes = cur.fetchall()
            conn.close()

            if not testes:
                show_error(
                    "Erro", "Nenhum teste cadastrado. Vá em Administração.")
                return

            # -------------------------
            # Abrir janela de seleção de teste
            # -------------------------
            sel_win = tk.Toplevel(self.root)
            sel_win.title("Selecione o teste")
            centralizar_janela(sel_win, 400, 300)

            lb = tk.Listbox(sel_win)
            for t in testes:
                lb.insert(tk.END, f"{t[0]} - {t[1]}")
            lb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            def escolher():
                sel = lb.curselection()
                if not sel:
                    show_error("Erro", "Selecione um teste!")
                    return

                item = lb.get(sel[0])
                teste_id = int(item.split(" - ", 1)[0])
                nome_teste = item.split(" - ", 1)[1]

                sel_win.destroy()
                self.abrir_executor(
                    teste_id, nome_teste, op_id, avaliador, turno)

            ttk.Button(sel_win, text="Selecionar",
                       command=escolher).pack(pady=8)

        ttk.Button(self.root, text="Continuar", width=20,
                   command=continuar).pack(pady=10)
        ttk.Button(self.root, text="Voltar", width=20,
                   command=self.abrir_tela_inicial).pack()

        self.rodape_frame, self.hora_label = criar_rodape(self.root)

    # ---------------------------------------------------
    # ABRIR NOVA JANELA DO TESTE (Toplevel maximizada)
    # ---------------------------------------------------
    def abrir_executor(self, teste_id, nome_teste, operador_id, avaliador, turno):

        # nova janela
        win = tk.Toplevel(self.root)
        win.title(f"Executando Teste - {nome_teste}")

        # maximizar cross-platform
        try:
            win.state("zoomed")      # Windows
        except:
            try:
                win.attributes('-zoomed', True)  # Linux
            except:
                # fallback full screen geometry
                w = win.winfo_screenwidth()
                h = win.winfo_screenheight()
                win.geometry(f"{w}x{h}+0+0")

        # esconder janela principal
        self.root.withdraw()

        # callback ao fechar o Toplevel
        def on_close():
            try:
                win.destroy()
            except:
                pass
            self.root.deiconify()  # mostra janela principal de novo

        win.protocol("WM_DELETE_WINDOW", on_close)

        # inicializa executor com callback
        TesteExecutor(
            win,
            teste_id,
            nome_teste,
            operador_id=operador_id,
            avaliador=avaliador,
            turno=turno,
            on_close=on_close
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
