import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_FOLDER = os.path.join(BASE_DIR, "sql")
DB_PATH = os.path.join(DB_FOLDER, "database.db")

def get_db():

    if not os.path.exists(DB_FOLDER):
        os.makedirs(DB_FOLDER)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn

def create_tables():

    caminho_sql = os.path.join(DB_FOLDER, "dump.sql")

    if not os.path.exists(caminho_sql):
        print(f"Arquivo SQL não encontrado: {caminho_sql}")
        return

    try:

        with open(caminho_sql, "r", encoding="utf-8") as file:
            sql = file.read()

        db = get_db()

        cursor = db.cursor()

        cursor.executescript(sql)

        db.commit()
        db.close()

        print("Banco inicializado com sucesso.")

    except Exception as e:

        print(f"Erro ao criar tabelas: {e}")
