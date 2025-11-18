# executar_teste.py
"""
Launcher oficial do módulo de execução de testes.

Este arquivo existe apenas para fornecer uma interface simples para
iniciar a tela de execução de teste, agora totalmente separada em:

executar/
    executor_view.py
    executor_controller.py
    executor_utils.py
    executor_rr.py
"""

import tkinter as tk
from executar.executor_view import TesteExecutorView


def iniciar_teste(root, teste_id, nome_teste,
                  operador_id=None, avaliador=None,
                  turno=None, on_close=None):
    """
    Inicializa a execução de um teste RR em uma nova janela.

    Parâmetros:
        root         -> janela principal (Tk ou Toplevel)
        teste_id     -> ID do teste no banco
        nome_teste   -> nome exibido no título
        operador_id  -> ID do operador que está fazendo o teste
        avaliador    -> nome do avaliador
        turno        -> turno do operador
        on_close     -> callback chamado quando a janela fecha
    """
    TesteExecutorView(
        root=root,
        teste_id=teste_id,
        nome_teste=nome_teste,
        operador_id=operador_id,
        avaliador=avaliador,
        turno=turno,
        on_close=on_close
    )


# Execução direta (caso você abra este arquivo sozinho)
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # esconde janela principal

    # Exemplo de teste manual
    iniciar_teste(
        root=root,
        teste_id=1,
        nome_teste="Teste de Demonstração",
        operador_id=1,
        avaliador="Sistema",
        turno="1° Turno"
    )

    root.mainloop()
