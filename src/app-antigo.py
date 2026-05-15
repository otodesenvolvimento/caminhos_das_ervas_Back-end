
from flask_cors import CORS
from flask import send_from_directory, abort
from flask import request
from werkzeug.utils import secure_filename
import os
from http  import HTTPStatus
from apiflask import APIFlask, HTTPError
from db import get_db, create_tables
from  models import Product
from schemas import ProductIn, ProductFilter,ProductOut, UserIn, UserOut   
from flask_httpauth import HTTPBasicAuth # 1. Importe a biblioteca

app  = APIFlask(__name__, title='Produtos API ')
app.secret_key = 'chave_secreta_do_oto' # Escolha uma frase segura  

from flask_cors import CORS

# Esta configuração diz ao Flask para aceitar TUDO o que o Angular precisa
CORS(app, 
     resources={r"/*": {"origins": "http://localhost:4200"}}, 
     supports_credentials=True, 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], # DELETE deve estar aqui!
     allow_headers=["Content-Type", "Authorization", "Access-Control-Allow-Credentials"])
# CORS(app,
#      supports_credentials=True,
#      # Adicionamos o localhost:4200 (Angular) nesta lista
#      origins=["http://localhost:4200", "http://127.0.0.1:5500", "http://localhost:5500",  "http://127.0.0.1:4200"],
#      allow_headers=["Content-Type", "Authorization"])


app.json.sort_keys = False
# Rota para servir as imagens do produto
@app.route('/images/<path:filename>')
def serve_image(filename):
    # 1. Define o caminho absoluto da pasta
    pasta_imagens = os.path.join(app.root_path, 'assets', 'products')
    
    # 2. Verifica se o arquivo realmente existe na pasta
    caminho_completo = os.path.join(pasta_imagens, filename)
    
    if not os.path.exists(caminho_completo):
        # Se a imagem não for encontrada, retorna o erro 404 em vez de "None"
        abort(404)
        
    # 3. O RETURN é obrigatório aqui para enviar o arquivo ao navegador
    return send_from_directory(pasta_imagens, filename)
# Configuração de onde as fotos serão salvas
UPLOAD_FOLDER = os.path.join(app.root_path, 'assets', 'products')

@app.post('/upload')
def upload_file():
    if 'file' not in request.files:
        return {"message": "Nenhum arquivo enviado"}, 400
    
    file = request.files['file']
    if file.filename == '':
        return {"message": "Nome do arquivo vazio"}, 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    # Retornamos o caminho que será salvo no banco de dados
    return {"image_path": f"assets/products/{filename}"}, 200

app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=False, # Use True apenas se tiver HTTPS
    SESSION_COOKIE_HTTPONLY=True
)
app.json.sort_keys = False

from flask import session # Usaremos sessions para o login simples

# --- Rota de Cadastro ---
@app.post('/register')
@app.input(UserIn,arg_name='data'  )
def register(data):
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)",
            (data['username'], data['password'], data['is_admin'])
        )
        db.commit()
        return {"message": "Usuário criado com sucesso!"}, HTTPStatus.CREATED
    except:
        raise HTTPError(400, message="Usuário já existe.")
    finally:
        db.close()

# --- Rota de Login ---
@app.post('/login')
@app.input(UserIn, arg_name='data')
@app.output(UserOut)
def login(data):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, username, is_admin FROM users WHERE username = ? AND password = ?",
        (data['username'], data['password'])
    )
    user = cursor.fetchone()
    db.close()

    if user:
        user_data = {"id": user[0], "username": user[1], "is_admin": user[2]}
        session['user'] = user_data  # Salva na sessão
        return user_data
    
    # Se não encontrar o usuário, levanta o erro explicitamente
    raise HTTPError(401, message="Credenciais inválidas")   

# --- Middleware/Função de Proteção para Admin ---
def check_admin():
    user = session.get('user')
    print(f"DEBUG: Usuário na sessão: {user}")
    if not user or user.get('is_admin') != 1:
        raise HTTPError(403, message="Acesso restrito a administradores.")






@app.get("/")
def index():
    return " <h1>API CAMINHO DAS ERVAS</h1>"

@app.get('/assets/<path:filename>')
def serve_assets(filename):
    # Retorna o arquivo da pasta assets
    return send_from_directory(os.path.join(app.root_path, 'assets'), filename)


@app.get("/products")
@app.input(ProductFilter,location="query",arg_name='filter')
@app.output(ProductOut(many=True))
def find_all_products(filter: dict):
    print(filter )
    db= get_db()
    cursor = db.cursor()

    parameters =   [] 
    query = '''  SELECT id, name, description, quantity, price, image_path
       FROM products WHERE 1 = 1
       '''
    if filter.get('search'):
         query+=' AND name LIKE ? '
         parameters.append(f"%{filter.get('search')}%")

    if filter.get('min_price'):
         query+=" AND price >= ? "
         parameters.append(filter.get("min_price"))

    if filter.get('max_price'):
         query+=" AND price <= ? "
         parameters.append(filter.get("max_price"))


    cursor.execute(query, parameters)
    rows = cursor.fetchall()

    cursor.close()
    db.close()
   
    products = [Product(*row) for row in rows]
    return products


 
@app.get("/product/<int:id>")
@app.output(ProductOut)
def  find_product_by_id(id: int):
     db = get_db()
     cursor = db.cursor()

     query = """
       SELECT id, name, description, quantity, price
       FROM products WHERE id = ?

    """
     cursor.execute(query, (id,))
     data = cursor.fetchone()


     if data is None:
          raise HTTPError(message="Produto nao encontrado", status_code=HTTPStatus.NOT_FOUND
                           )



     print(data)

     cursor.close()
     db.close()
     return Product(*data)
     #return { 'message': "kkk..."}



@app.post('/products')
@app.input(ProductIn, arg_name='product_in')
@app.output(ProductOut, status_code=HTTPStatus.CREATED)
def create_products(product_in:dict):
    check_admin() # 🛡️ Bloqueia se não for admin logado
    db= get_db()
    cursor = db.cursor() 

    parameters =(
         product_in.get("name"),
         product_in.get("description"),
         product_in.get("quantity"),
         product_in.get("price"),
         product_in.get("image_path") # Novo parâmetro
         )    

    query = '''
    INSERT INTO products(name, description, quantity, price, image_path)
    VALUES(?,?,?,?,?)
    '''
    #  query = '''INSERT INTO products(name, description, quantity,price,image_path)
    #      VALUES(?,?,?,?,?) RETURNING id   

    #  '''
    # # # #  parameters =(  
    # # # #      product_in.get("name"),
    # # # #      product_in.get("description"),
    # # # #      product_in.get("quantity"),
    # # # #      product_in.get("price")
    # # # #      )   
    cursor.execute(query, parameters) 
     
    id = cursor.lastrowid
     #id: int = cursor.fetchone()[0]
    db.commit()
    cursor.close()
    db.close()
     
    product = Product(id,*parameters)
    return (product, HTTPStatus.CREATED)

@app.put("/product/<int:id>")
@app.output(ProductOut)
@app.input(ProductIn, arg_name='product_in')
def update_product(id: int, product_in:dict):
     check_admin() # 🛡️ Bloqueia se não for admin logado
     db= get_db()
     cursor = db.cursor() 

    #  parameters =(
    #      product_in.get("name"),
    #      product_in.get("description"),
    #      product_in.get("quantity"),
    #      product_in.get("price")
    #      )    


     query = '''UPDATE products
                SET name = ?, description = ?, quantity = ?,price = ? , image_path = ?
                WHERE id  = ?

     '''
     parameters =(
         product_in.get("name"),
         product_in.get("description"),
         product_in.get("quantity"),
         product_in.get("price"),
         product_in.get("image_path"), # Novo parâmetro
         id,
         )   
     cursor.execute(query, parameters) 
     
     db.commit()
     cursor.close()
     db.close()
     
     product = Product(id,*parameters[:-1])
     return product


auth = HTTPBasicAuth() # 2. Instancie o objeto 'auth' aqui!

# 3. Defina como o Flask verifica a senha (exemplo simples)
@auth.verify_password
def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user
    return None

# 4. Defina as funções/cargos (roles) se estiver usando
@auth.get_user_roles
def get_user_roles(user):
    return 'admin' if user.is_admin else 'user'


@app.delete("/product/<int:id>") 
@auth.login_required(role='admin') # Garante que só o admin logado apague
def delete_product_by_id(id: int):
    db = get_db()
    cursor = db.cursor()

    query= """
        DELETE FROM products
        where id = ?

"""
    cursor.execute(query, (id,))
    db.commit()
    cursor.close()
    db.close()

    return {"message": "Produto excluido com sucesso."}



if __name__== "__main__":
    create_tables()
    app.run(debug=True)
  