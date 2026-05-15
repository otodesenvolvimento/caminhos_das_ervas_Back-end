import pandas as pd
import os
from db import get_db, create_tables

def sincronizar():
    create_tables()
    
    caminho_excel = 'produtos_loja.xlsx'
    if not os.path.exists(caminho_excel):
        print(f"Erro: Arquivo {caminho_excel} não encontrado.")
        return

    try:
        # Carrega o arquivo
        df = pd.read_excel(caminho_excel)
        
        # Remove linhas onde o NOME é nulo para evitar o erro de NOT NULL
        df = df.dropna(subset=['NOME'])
        
        db = get_db()
        cursor = db.cursor()

        for _, row in df.iterrows():
            nome = str(row['NOME']).strip()
            desc = str(row.get('DESCRICAO', ''))
            # Garante que quantidade e preço são números válidos
            qtd = int(row.get('QUANTIDADE', 0)) if pd.notnull(row.get('QUANTIDADE')) else 0
            preco = float(row.get('PRECO', 0.0)) if pd.notnull(row.get('PRECO')) else 0.0

            # Usa INSERT OR REPLACE para atualizar se o nome já existir
            cursor.execute('''
                INSERT OR REPLACE INTO products (name, description, quantity, price, image_path) 
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, desc, qtd, preco, 'assets/products/default.png'))
        
        db.commit()
        db.close()
        print("Sincronização concluída com sucesso!")
    except Exception as e:
        print(f"Erro na sincronização: {e}")

if __name__ == "_   _main__":
    sincronizar()