CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    quantity INTEGER DEFAULT 0,
    price REAL NOT NULL,
    image_path TEXT DEFAULT 'assets/products/default.png',
    categoria TEXT -- ESTA LINHA É OBRIGATÓRIA
);
-- ALTER TABLE products ADD COLUMN image_path TEXT;

-- ALTER TABLE products ADD COLUMN categoria TEXT;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0 -- 0 para usuário comum, 1 para admin
);