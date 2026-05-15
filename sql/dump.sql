CREATE TABLE products (
    id INTEGER PRIMARY  KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    quantity  INTEGER NOT NULL DEFAULT 0,
    price FLOAT NOT NULL

    

);
ALTER TABLE products ADD COLUMN image_path TEXT;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0 -- 0 para usuário comum, 1 para admin
);