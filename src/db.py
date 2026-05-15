import sqlite3
import os

def get_base_path():
    # Obtém o caminho da pasta 'src' e sobe um nível para a raiz do projeto
    src_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(src_path)

def get_db():
    # Define o caminho para a pasta 'sql' que está fora da 'src'
    root_path = get_base_path()
    db_folder = os.path.join(root_path, "sql")
    db_path = os.path.join(db_folder, "database.db")
    
    # Cria a pasta 'sql' na raiz se ela não existir
    if not os.path.exists(db_folder):
        os.makedirs(db_folder)
        
    return sqlite3.connect(db_path)

def create_tables():
    root_path = get_base_path()
    caminho_sql = os.path.join(root_path, "sql", "dump.sql")

    if not os.path.exists(caminho_sql):
        print(f"ERRO: Ficheiro '{caminho_sql}' não encontrado na raiz.")
        return

    try:
        with open(caminho_sql, "r", encoding='utf-8') as file:
            sql = file.read()
        
        db = get_db()
        cursor = db.cursor()
        cursor.executescript(sql)
        db.commit()
        db.close()
        print("Estrutura do banco de dados verificada na pasta raiz.")
    except Exception as e:
        if "already exists" not in str(e):
            print(f"Erro ao criar tabelas: {e}")
            