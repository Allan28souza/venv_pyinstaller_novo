from utils import AutocompleteCombobox
import tkinter as tk
from tkinter import ttk
from admin_views.admin import AdminApp
from executar_teste import TesteExecutor
import database as db
from utils import centralizar_janela, criar_rodape, show_error


class MainApp:
    def __init__(self, root):
        db.criar_tabelas()  # garante DB
        self.root = root
        self.root.title("Motherson Taubaté - Sistema de Testes com Imagens")
        self.root.geometry("420x320")
        centralizar_janela(self.root, 420, 320)

        self.rodape_frame = None
        self.hora_label = None

        self.abrir_tela_inicial()

    # ---------------------------------------------------
    def limpar_tela(self):
        for w in self.root.winfo_children():
            w.destroy()

    # ---------------------------------------------------
    # TELA PRINCIPAL
    # ---------------------------------------------------
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

    # ---------------------------------------------------
    def abrir_admin(self):
        self.limpar_tela()
        AdminApp(self.root, voltar=self.abrir_tela_inicial)

    # ---------------------------------------------------
    # TELA DE ENTRADA DO OPERADOR / AVALIADOR
    # ---------------------------------------------------
    def iniciar_teste(self):
        self.limpar_tela()

        # =======================
        # OPERADORES CADASTRADOS
        # =======================
        ops = db.listar_operadores()
        # ops = [(id, nome, matricula, turno)]

        nomes_list = [f"{op[1]} ({op[2]})" for op in ops]
        mats_list = [op[2] for op in ops]

        # =======================
        # CAMPO NOME (AUTOCOMPLETE)
        # =======================
        tk.Label(self.root, text="Operador:", font=("Arial", 11)).pack(pady=3)

        operador_cb = AutocompleteCombobox(self.root, width=35)
        operador_cb.set_completion_list(nomes_list)
        operador_cb.pack(pady=3)

        # =======================
        # CAMPO MATRÍCULA (AUTOCOMPLETE)
        # =======================
        tk.Label(self.root, text="Matrícula:", font=("Arial", 11)).pack(pady=3)

        mat_var = tk.StringVar()
        matricula_cb = AutocompleteCombobox(
            self.root, textvariable=mat_var, width=35)
        matricula_cb.set_completion_list(mats_list)
        matricula_cb.pack(pady=3)

        # =======================
        # TURNO
        # =======================
        tk.Label(self.root, text="Turno:", font=("Arial", 11)).pack(pady=3)
        turnos = db.listar_turnos()
        turno_cb = ttk.Combobox(self.root, values=turnos,
                                state="readonly", width=25)
        if turnos:
            turno_cb.current(0)
        turno_cb.pack()

        # =======================
        # AVALIADOR
        # =======================
        tk.Label(self.root, text="Avaliador:", font=("Arial", 11)).pack(pady=3)
        avaliadores = db.listar_avaliadores()
        avaliador_cb = ttk.Combobox(
            self.root, values=avaliadores, state="readonly", width=25)
        if avaliadores:
            avaliador_cb.current(0)
        avaliador_cb.pack()

        # ======================================================
        # FUNÇÕES DE SINCRONIZAÇÃO ENTRE NOME E MATRÍCULA
        # ======================================================

        def preencher_por_nome(event=None):
            texto = operador_cb.get().strip()
            if "(" in texto and texto.endswith(")"):
                nome = texto.split(" (")[0]
                mat = texto.split("(")[1].replace(")", "")

                for op in ops:
                    if op[1] == nome and op[2] == mat:
                        mat_var.set(op[2])
                        matricula_cb.set(op[2])
                        turno_cb.set(op[3])
                        return

        def preencher_por_matricula(event=None):
            mat = matricula_cb.get().strip()
            if not mat:
                return

            for op in ops:
                if op[2] == mat:
                    operador_cb.set(f"{op[1]} ({op[2]})")
                    turno_cb.set(op[3])
                    return

        operador_cb.bind("<<ComboboxSelected>>", preencher_por_nome)
        matricula_cb.bind("<<ComboboxSelected>>", preencher_por_matricula)
        matricula_cb.bind("<FocusOut>", preencher_por_matricula)

        # ======================================================
        # CONTINUAR → SELECIONAR TESTE
        # ======================================================
        def continuar():
            nome_txt = operador_cb.get().strip()
            mat_txt = matricula_cb.get().strip()
            turno = turno_cb.get().strip()
            avaliador = avaliador_cb.get().strip()

            nome = ""
            matricula = ""

            # caso tenha vindo do autocomplete por nome
            if "(" in nome_txt and nome_txt.endswith(")"):
                nome = nome_txt.split(" (")[0]
                matricula = nome_txt.split("(")[1].replace(")", "")
            else:
                nome = nome_txt
                matricula = mat_txt

            if not nome or not matricula:
                return show_error("Erro", "Informe nome e matrícula!")

            # cadastra se não existir
            op_id = db.garantir_operador(nome, matricula, turno)

            if avaliador:
                db.garantir_avaliador(avaliador)

            # buscar testes
            conn = db.conectar()
            cur = conn.cursor()
            cur.execute("SELECT id, nome FROM testes ORDER BY nome")
            testes = cur.fetchall()
            conn.close()

            if not testes:
                return show_error("Erro", "Nenhum teste cadastrado!")

            # janela de seleção
            sel_win = tk.Toplevel(self.root)
            sel_win.title("Selecione o Teste")
            sel_win.geometry("420x320")

            lb = tk.Listbox(sel_win)
            for t in testes:
                lb.insert(tk.END, f"{t[0]} - {t[1]}")
            lb.pack(fill="both", expand=True, padx=10, pady=10)

            def escolher():
                sel = lb.curselection()
                if not sel:
                    return show_error("Erro", "Selecione um teste!")

                item = lb.get(sel[0])
                teste_id = int(item.split(" - ", 1)[0])
                nome_teste = item.split(" - ", 1)[1]

                sel_win.destroy()
                self.abrir_executor(
                    teste_id, nome_teste, op_id, avaliador, turno
                )

            ttk.Button(sel_win, text="Selecionar",
                       command=escolher).pack(pady=10)

        ttk.Button(self.root, text="Continuar", width=25,
                   command=continuar).pack(pady=12)
        ttk.Button(self.root, text="Voltar", width=25,
                   command=self.abrir_tela_inicial).pack()

        self.rodape_frame, self.hora_label = criar_rodape(self.root)

    # ---------------------------------------------------
    # ABRIR A JANELA DO TESTE (SEM TELA BRANCA)
    # ---------------------------------------------------

    def abrir_executor(self, teste_id, nome_teste, operador_id, avaliador, turno):

        # Janela do teste criada pelo próprio TesteExecutor
        # Aqui será apenas criada uma janela PAI que é escondida
        win = tk.Toplevel(self.root)
        win.withdraw()   # janela oculta, pois o executor criará sua própria

        # Esconde a principal enquanto o teste roda
        self.root.withdraw()

        # Callback para quando o teste terminar
        def on_close():
            try:
                win.destroy()
            except:
                pass
            self.root.deiconify()  # volta a tela principal

        # Inicia o executor **corretamente passando self.root**
        TesteExecutor(
            root=self.root,
            teste_id=teste_id,
            nome_teste=nome_teste,
            operador_id=operador_id,
            avaliador=avaliador,
            turno=turno,
            on_close=on_close
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
