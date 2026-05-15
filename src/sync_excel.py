import pandas as pd
import os
from db import get_db, create_tables

def sincronizar():
    # Garante que a pasta sql e a tabela existam antes de começar
    create_tables()
    
    caminho_excel = 'produtos_loja.xlsx'
    
    if not os.path.exists(caminho_excel):
        print(f"Erro: Arquivo {caminho_excel} não encontrado.")
        return

    try:
        # Carrega o arquivo Excel
        df = pd.read_excel(caminho_excel)
        
        # Remove linhas onde o NOME é nulo para evitar erro de banco de dados
        df = df.dropna(subset=['NOME'])
        
        db = get_db()
        cursor = db.cursor()

        print(f"Iniciando sincronização de {len(df)} produtos...")

        for _, row in df.iterrows():
            # Extração e limpeza dos dados
            nome = str(row['NOME']).strip()
            desc = str(row.get('DESCRICAO', '')).strip()
            
            # Conversão segura de números
            qtd = int(row['QUANTIDADE']) if pd.notnull(row.get('QUANTIDADE')) else 0
            preco = float(row['PRECO']) if pd.notnull(row.get('PRECO')) else 0.0
            
            # Captura da CATEGORIA (crucial para o seu filtro no Angular)
            categoria = str(row.get('CATEGORIA', 'banho')).strip().lower()
            
            # Captura da IMAGEM (usa o caminho do excel ou o padrão do sistema)
            imagem = str(row.get('IMAGEM', 'assets/products/default.png')).strip()

            # Execução do comando SQL
            cursor.execute('''
                INSERT OR REPLACE INTO products (name, description, quantity, price, image_path, categoria) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nome, desc, qtd, preco, imagem, categoria))
        
        db.commit()
        db.close()
        print("Sincronização concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro na sincronização: {e}")

# Correção da execução principal (sem espaços e com os underscores corretos)
if __name__ == "__main__":
    sincronizar()