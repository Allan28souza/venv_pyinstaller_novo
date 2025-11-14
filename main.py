# main.py
import tkinter as tk
from tkinter import ttk
from admin import AdminApp
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
        # AdminApp cuida do rodapé

    def iniciar_teste(self):
        self.limpar_tela()
        # Form para operador / matricula / avaliador / turno
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
        # se não houver avaliadores cadastrados, deixa em branco para o usuário adicionar via Admin
        if avaliadores:
            avaliador_cb.current(0)
        avaliador_cb.pack()

        def continuar():
            nome = nome_var.get().strip()
            mat = mat_var.get().strip()
            turno = turno_cb.get().strip()
            avaliador = avaliador_cb.get().strip()
            if not nome or not mat:
                show_error("Erro", "Informe nome e matrícula do operador!")
                return
            # garante operador no DB
            op_id = db.garantir_operador(nome, mat, turno)
            # garante avaliador (se selecionado)
            if avaliador:
                db.garantir_avaliador(avaliador)
            # abre seleção de teste (simplificado: usa primeiro teste disponível)
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM testes ORDER BY nome")
            testes = cur.fetchall()
            conn.close()
            if not testes:
                show_error(
                    "Erro", "Nenhum teste cadastrado. Vá em Administração.")
                return
            # se houver muitos testes ideal abrir uma tela de seleção. Aqui pegamos o primeiro para demo.
            # melhor: abrir uma lista para o usuário escolher. Vou abrir uma janela de seleção:
            sel_win = tk.Toplevel(self.root)
            sel_win.title("Selecione o teste")
            from utils import centralizar_janela
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
                # inicia executor passando operador id e avaliador/turno
                TesteExecutor(self.root, teste_id, nome_teste,
                              operador_id=op_id, avaliador=avaliador, turno=turno)
            ttk.Button(sel_win, text="Selecionar",
                       command=escolher).pack(pady=8)

        ttk.Button(self.root, text="Continuar", width=20,
                   command=continuar).pack(pady=10)
        ttk.Button(self.root, text="Voltar", width=20,
                   command=self.abrir_tela_inicial).pack()
        # rodapé
        try:
            self.rodape_frame, self.hora_label = criar_rodape(self.root)
        except:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
