from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

class Afiliado(Base):
    __tablename__ = "afiliados"

    id = Column(Integer, primary_key=True, index=True)

    nombre_comercial = Column(String)
    nombre_legal = Column(String)
    direccion = Column(String)

    giro = Column(String)
    rfc = Column(String)

    num_afiliado = Column(String, unique=True)
    tipo = Column(String)