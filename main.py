from fastapi import FastAPI, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from database import Base, engine, SessionLocal
from models import User
from passlib.hash import bcrypt
from jose import JWTError, jwt
import pandas as pd
from fpdf import FPDF
import os
from datetime import datetime, timedelta

# 🔐 CONFIG JWT
SECRET_KEY = "super_secreto_itrsf"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def crear_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")

        return username

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# 🚀 APP
app = FastAPI()
Base.metadata.create_all(bind=engine)

# 📁 RUTA BASE
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 📊 CARGAR EXCEL
excel_path = os.path.join(BASE_DIR, "afiliados_limpio.xlsx")
df = pd.read_excel(excel_path)
df = df.fillna("")
data = df.to_dict(orient="records")

# 💰 COSTOS
costos = {
    "P": 500,
    "M": 800,
    "G": 1200
}

# 🏠 HOME
@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

# 🔍 BUSCAR
@app.get("/buscar/")
def buscar(q: str = "", user: str = Depends(verificar_token)):

    if not q.strip():
        return []

    q = q.lower()

    resultados = [
        d for d in data
        if (
            q in str(d.get("nombre_comercial", "")).lower()
            or q in str(d.get("nombre_legal", "")).lower()
            or q in str(d.get("num_afiliado", "")).lower()
        )
    ]

    return resultados

# 🧾 RECIBO
@app.get("/recibo/{num_afiliado}")
def generar_recibo(num_afiliado: str, user: str = Depends(verificar_token)):

    afiliado = next(
        (d for d in data if str(d.get("num_afiliado")) == num_afiliado),
        None
    )

    if not afiliado:
        return {"error": "No encontrado"}

    tipo = afiliado.get("tipo", "P")
    costo = costos.get(tipo, 500)

    folio = f"REC-{int(datetime.now().timestamp())}"

    pdf = FPDF('P', 'mm', (140, 216))
    pdf.add_page()

    pdf.rect(5, 5, 130, 206)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "CAMARA DE COMERCIO", 0, 1, "C")

    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, "RECIBO OFICIAL", 0, 1, "C")

    pdf.cell(0, 5, datetime.now().strftime("%d/%m/%Y"), 0, 1, "R")
    pdf.cell(0, 5, f"Folio: {folio}", 0, 1, "R")

    pdf.ln(5)

    pdf.cell(45, 6, "No. Afiliado:", 0, 0)
    pdf.cell(0, 6, str(afiliado.get("num_afiliado","")), 0, 1)

    pdf.cell(45, 6, "Nombre Comercial:", 0, 0)
    pdf.multi_cell(0, 6, afiliado.get("nombre_comercial",""))

    pdf.cell(45, 6, "Nombre Legal:", 0, 0)
    pdf.multi_cell(0, 6, afiliado.get("nombre_legal",""))

    pdf.cell(45, 6, "Tipo:", 0, 0)
    pdf.cell(0, 6, tipo, 0, 1)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(45, 8, "Costo:", 0, 0)
    pdf.cell(0, 8, f"${costo}", 0, 1)
    pdf.set_font("Arial", size=10)

    pdf.ln(15)

    pdf.cell(55, 6, "____________________", 0, 0, "C")
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(55, 6, "____________________", 0, 1, "C")

    pdf.cell(55, 6, "Firma Afiliado", 0, 0, "C")
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(55, 6, "Óscar Alberto de Ávila Alfaro", 0, 1, "C")

    pdf.cell(55, 6, "", 0, 0)
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(55, 6, "Presidente Cámara", 0, 1, "C")

    archivo = os.path.join(BASE_DIR, f"recibo_{num_afiliado}.pdf")
    pdf.output(archivo)

    return FileResponse(archivo, media_type="application/pdf")

# 📄 COMPROBANTE
@app.get("/comprobante/{num_afiliado}")
def generar_comprobante(num_afiliado: str, user: str = Depends(verificar_token)):

    afiliado = next(
        (d for d in data if str(d.get("num_afiliado")) == num_afiliado),
        None
    )

    if not afiliado:
        return {"error": "No encontrado"}

    pdf = FPDF('P', 'mm', (140, 216))
    pdf.add_page()

    pdf.rect(5, 5, 130, 206)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, "CAMARA DE COMERCIO", 0, 1, "C")

    pdf.set_font("Arial", size=10)
    pdf.cell(0, 5, "COMPROBANTE", 0, 1, "C")

    pdf.cell(0, 5, datetime.now().strftime("%d/%m/%Y"), 0, 1, "R")

    pdf.ln(5)

    pdf.cell(45, 6, "Nombre Comercial:", 0, 0)
    pdf.multi_cell(0, 6, afiliado.get("nombre_comercial",""))

    pdf.cell(45, 6, "Nombre Legal:", 0, 0)
    pdf.multi_cell(0, 6, afiliado.get("nombre_legal",""))

    pdf.cell(45, 6, "Direccion:", 0, 0)
    pdf.multi_cell(0, 6, afiliado.get("direccion",""))

    pdf.ln(15)

    pdf.cell(55, 6, "____________________", 0, 0, "C")
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(55, 6, "____________________", 0, 1, "C")

    pdf.cell(55, 6, "Firma Afiliado", 0, 0, "C")
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(55, 6, "Óscar Alberto de Ávila Alfaro", 0, 1, "C")

    pdf.cell(55, 6, "", 0, 0)
    pdf.cell(10, 6, "", 0, 0)
    pdf.cell(55, 6, "Presidente Cámara", 0, 1, "C")

    archivo = os.path.join(BASE_DIR, f"comprobante_{num_afiliado}.pdf")
    pdf.output(archivo)

    return FileResponse(archivo, media_type="application/pdf")

# 👤 REGISTER
@app.post("/register")
def register(username: str = Form(...), password: str = Form(...)):
    try:
        db = SessionLocal()

        existing = db.query(User).filter(User.username == username).first()
        if existing:
            db.close()
            return {"error": "Usuario ya existe"}

        user = User(
            username=username,
            password=bcrypt.hash(password)
        )

        db.add(user)
        db.commit()
        db.close()

        return {"msg": "Usuario creado"}

    except Exception as e:
        return {"error": str(e)}

# 🔑 LOGIN
@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()

    if not user or not bcrypt.verify(password, user.password):
        db.close()
        return {"error": "Credenciales incorrectas"}

    token = crear_token({"sub": user.username})

    db.close()
    return {"access_token": token, "token_type": "bearer"}

# 🔒 CAMBIAR PASSWORD
@app.post("/cambiar-password")
def cambiar_password(username: str = Form(...), nueva_password: str = Form(...)):
    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()

    if not user:
        db.close()
        return {"error": "Usuario no encontrado"}

    user.password = bcrypt.hash(nueva_password)

    db.commit()
    db.close()

    return {"msg": "Contraseña actualizada"}
