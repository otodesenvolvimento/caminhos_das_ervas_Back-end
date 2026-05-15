from apiflask import Schema
from apiflask.fields import Integer, String, Float
from apiflask.validators import Length, Range
from flask import session

class ProductIn(Schema):
    name = String(required=True)
    description = String(validate=[Length(max=2550)])
    quantity = Integer( validate=[Range(min=0)],load_default=0)
    price = Float(required=True, validate=[Range(min=0.01)])
    image_path = String(load_default="assets/products/default.png") # Caminho padrão




class ProductOut(Schema):
    id = Integer()
    name = String()
    description = String()
    quantity = Integer()
    price = Float()
    image_path = String() # Aparece na resposta da API


class ProductFilter(Schema):
    search = String(load_default=None)
    min_price = Float(load_default=None)
    mas_price = Float(load_default=None)

class UserIn(Schema):
    username = String(required=True)
    password = String(required=True)
    is_admin = Integer(load_default=0) # Campo opcional no cadastro

class UserOut(Schema):
    id = Integer()
    username = String()
    is_admin = Integer()    