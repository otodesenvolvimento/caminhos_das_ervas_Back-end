from typing import Optional
from dataclasses import dataclass



# No ficheiro src/models.py
@dataclass
class Product:
    id: int
    name: str
    description: Optional[str]
    quantity: int
    price: float
    image_path: Optional[str] = None
    categoria: Optional[str] = None  # Adicione esta linha