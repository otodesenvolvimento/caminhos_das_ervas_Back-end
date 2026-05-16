print("APP INICIANDO...")
from flask_cors import CORS
from flask import send_from_directory, request, session
from werkzeug.utils import secure_filename
import os
from http import HTTPStatus
from apiflask import APIFlask, HTTPError
import pandas as pd
#from db import get_db, create_tables
print("IMPORTANDO DB...")
from src.db import get_db, create_tables
#from models import Product
print("IMPORTANDO MODELS...")
from src.models import Product
print("APP INICIANDO...")
print("IMPORTANDO SCHEMAS...")
from src.schemas import (
    ProductIn,
    ProductFilter,
    ProductOut,
    UserIn,
    UserOut
)
print("IMPORTS OK")
# from schemas import (
#     ProductIn,
#     ProductFilter,
#     ProductOut,
#     UserIn,
#     UserOut
# )

# =========================================
# CONFIGURAÇÃO APP
# =========================================
print("CRIANDO APP...")
app = APIFlask(__name__, title='Produtos API')
print("APP CRIADO")
app.secret_key = 'chave_secreta_do_oto'

app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True
)

app.json.sort_keys = False

# =========================================
# CORS
# =========================================
CORS(app, resources={r"/*": {"origins": "https://agent-6a07924719adb8bc57f54758--caminhodaservas.netlify.app/"}}, supports_credentials=True)
# CORS(app, supports_credentials=True, resources={ r"/*": {"origins": ["http://localhost:4200"] } )

# =========================================
# PASTA UPLOAD
# =========================================

UPLOAD_FOLDER = os.path.join(app.root_path, 'assets', 'products')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# =========================================
# MIDDLEWARE ADMIN
# =========================================

def check_admin():

    user = session.get('user')

    if not user:
        raise HTTPError(
            401,
            message='Usuário não autenticado'
        )

    if not bool(user.get('is_admin')):
        raise HTTPError(
            403,
            message='Acesso restrito a administradores'
        )

# =========================================
# ARQUIVOS
# =========================================
@app.get("/")
def home():
    return {"status": "online"}

@app.post('/products/upload-excel')
def upload_excel():
    if 'file' not in request.files:
        raise HTTPError(400, message="Nenhum arquivo enviado")
    
    file = request.files['file']
    
    try:
        # Lê o Excel e remove linhas sem nome
        df = pd.read_excel(file)
        if 'NOME' not in df.columns:
            raise HTTPError(400, message="A planilha deve conter a coluna 'NOME'")
            
        df = df.dropna(subset=['NOME'])
        
        db = get_db()
        cursor = db.cursor()

        for _, row in df.iterrows():
            nome = str(row['NOME']).strip()
            desc = str(row.get('DESCRICAO', ''))
            qtd = int(row.get('QUANTIDADE', 0)) if pd.notnull(row.get('QUANTIDADE')) else 0
            preco = float(row.get('PRECO', 0.0)) if pd.notnull(row.get('PRECO')) else 0.0

            cursor.execute('''
                INSERT OR REPLACE INTO products (name, description, quantity, price, image_path) 
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, desc, qtd, preco, 'assets/products/default.png'))
        
        db.commit()
        db.close()
        return {'message': 'Estoque atualizado com sucesso via Excel!'}
    except Exception as e:
        raise HTTPError(500, message=str(e))


@app.get('/assets/<path:filename>')
def serve_assets(filename):

    return send_from_directory(
        os.path.join(app.root_path, 'assets'),
        filename
    )

# =========================================
# UPLOAD
# =========================================

@app.post('/upload')
def upload_file():

    check_admin()

    if 'file' not in request.files:
        return {'message': 'Nenhum arquivo enviado'}, 400

    file = request.files['file']

    if file.filename == '':
        return {'message': 'Nome do arquivo vazio'}, 400

    filename = secure_filename(file.filename)

    file.save(
        os.path.join(UPLOAD_FOLDER, filename)
    )

    return {
        'image_path': f'assets/products/{filename}'
    }, 200

# =========================================
# REGISTER
# =========================================

@app.post('/register')
@app.input(UserIn, arg_name='data')
def register(data):

    db = get_db()
    cursor = db.cursor()

    try:

        cursor.execute(
            '''
            INSERT INTO users (
                username,
                password,
                is_admin
            )
            VALUES (?, ?, ?)
            ''',
            (
                data['username'],
                data['password'],
                data['is_admin']
            )
        )

        db.commit()

        return {
            'message': 'Usuário criado com sucesso'
        }, HTTPStatus.CREATED

    except:
        raise HTTPError(
            400,
            message='Usuário já existe'
        )

    finally:
        db.close()

# =========================================
# LOGIN
# =========================================

@app.post('/login')
@app.input(UserIn, arg_name='data')
@app.output(UserOut)
def login(data):

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        '''
        SELECT
            id,
            username,
            is_admin
        FROM users
        WHERE username = ?
        AND password = ?
        ''',
        (
            data['username'],
            data['password']
        )
    )

    user = cursor.fetchone()

    db.close()

    if not user:
        raise HTTPError(
            401,
            message='Credenciais inválidas'
        )

    user_data = {
        'id': user[0],
        'username': user[1],
        'is_admin': user[2]
    }

    session['user'] = user_data

    return user_data

# =========================================
# USUÁRIO ATUAL
# =========================================

@app.get('/me')
@app.output(UserOut)
def get_current_user():

    user = session.get('user')

    if not user:
        raise HTTPError(
            401,
            message='Não logado'
        )

    return user

# =========================================
# LISTAR PRODUTOS
# =========================================

@app.get('/products')
@app.input(ProductFilter, location='query', arg_name='filter')
@app.output(ProductOut(many=True))
def find_all_products(filter: dict):

    db = get_db()
    cursor = db.cursor()

    parameters = []

    query = '''
        SELECT
            id,
            name,
            description,
            quantity,
            price,
            image_path,
            categoria   
        FROM products
        WHERE 1 = 1
    '''

    if filter.get('search'):

        query += ' AND name LIKE ? '

        parameters.append(
            f"%{filter.get('search')}%"
        )

    if filter.get('min_price'):

        query += ' AND price >= ? '

        parameters.append(
            filter.get('min_price')
        )

    if filter.get('max_price'):

        query += ' AND price <= ? '

        parameters.append(
            filter.get('max_price')
        )

    cursor.execute(query, parameters)

    rows = cursor.fetchall()

    db.close()

    return [Produto(*row) for row in rows]

# =========================================
# PRODUTO POR ID
# =========================================

@app.get('/products/<int:id>')
def get_product(id):

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        '''
        SELECT
            id,
            name,
            description,
            quantity,
            price,
            image_path,
            categoria
        FROM products
        WHERE id = ?
        ''',
        (id,)
    )

    row = cursor.fetchone()

    db.close()

    if not row:
        raise HTTPError(
            404,
            message='Produto não encontrado'
        )

    return {
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'quantity': row[3],
        'price': row[4],
        'image_path': row[5],
        'categoria': row[6]
    }

# =========================================
# CRIAR PRODUTO
# =========================================

@app.post('/products')
@app.input(ProductIn, arg_name='product_in')
@app.output(ProductOut, status_code=HTTPStatus.CREATED)
def create_products(product_in: dict):

    check_admin()

    db = get_db()
    cursor = db.cursor()

    parameters = (
        product_in.get('name'),
        product_in.get('description'),
        product_in.get('quantity'),
        product_in.get('price'),
        product_in.get('image_path'),
        product_in.get('categoria')
    )

    cursor.execute(
        '''
        INSERT INTO products (
            name,
            description,
            quantity,
            price,
            image_path,
            categoria
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ''',
        parameters
    )

    id = cursor.lastrowid

    db.commit()
    db.close()

    return Product(id, *parameters)

# =========================================
# UPDATE PRODUTO
# =========================================

@app.put('/products/<int:id>')
@app.input(ProductIn, arg_name='product_in')
def update_product(id: int, product_in: dict):

    check_admin()

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
       '''
        UPDATE products
        SET name = ?, description = ?, quantity = ?, price = ?, image_path = ?, categoria = ?
        WHERE id = ?
    ''',
        (
            product_in.get('name'),
            product_in.get('description'),
            product_in.get('quantity'),
            product_in.get('price'),
            product_in.get('image_path'),
            product_in.get('categoria'),
            id
        )
    )

    db.commit()
    db.close()

    return {
        'message': 'Produto atualizado com sucesso'
    }, 200

# =========================================
# DELETE PRODUTO
# =========================================

@app.delete('/products/<int:id>')
def delete_product(id):

    check_admin()

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        'DELETE FROM products WHERE id = ?',
        (id,)
    )

    db.commit()
    db.close()

    return {
        'message': 'Produto excluído com sucesso'
    }, 200

# =========================================
# MAIN
# =========================================
#with app.app_context():
#    create_tables()

if __name__ == '__main__':
    app.run(debug=True)


   

  
