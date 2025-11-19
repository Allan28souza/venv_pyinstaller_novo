import sqlite3

conn = sqlite3.connect("testes.db")
cur = conn.cursor()

# Para cada resposta antiga que só tem nome_arquivo, tentar localizar o id correto
cur.execute("""
    SELECT resp.id, resp.nome_arquivo, r.teste_id
    FROM respostas resp
    JOIN resultados r ON r.id = resp.resultado_id
""")
rows = cur.fetchall()

for resp_id, nome_arquivo, teste_id in rows:
    cur.execute("""
        SELECT id FROM imagens
        WHERE nome_arquivo=? AND teste_id=?
        LIMIT 1
    """, (nome_arquivo, teste_id))
    r = cur.fetchone()

    if r:
        imagem_id = r[0]
        cur.execute("UPDATE respostas SET imagem_id=? WHERE id=?",
                    (imagem_id, resp_id))

conn.commit()
conn.close()
print("MIGRAÇÃO CONCLUÍDA")
