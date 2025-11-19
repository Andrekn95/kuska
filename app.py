from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

DB_NAME = "database.db"


# ------------------------------------------------
# 🔧 CREAR TABLAS SI NO EXISTEN
# ------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabla usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Tabla formularios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS formularios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            fecha TEXT
        )
    ''')

    conn.commit()
    conn.close()


init_db()


# ------------------------------------------------
# 🔐 LOGIN
# ------------------------------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE email=? AND password=?", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({"message": "Login correcto", "usuario": user[1]})
    else:
        return jsonify({"error": "Credenciales incorrectas"}), 401


# ------------------------------------------------
# 🆕 REGISTRO DE USUARIO
# ------------------------------------------------
@app.route("/usuarios", methods=["POST"])
def register_user():
    data = request.json
    nombre = data.get("nombre")
    email = data.get("email")
    password = data.get("password")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)",
                       (nombre, email, password))
        conn.commit()
        conn.close()
        return jsonify({"message": "Usuario registrado correctamente"})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "El correo ya existe"}), 400


# ------------------------------------------------
# 📄 OBTENER TODOS LOS FORMULARIOS
# ------------------------------------------------
@app.route("/formularios", methods=["GET"])
def get_formularios():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM formularios")
    data = cursor.fetchall()
    conn.close()

    formularios = []
    for f in data:
        formularios.append({
            "id": f[0],
            "nombre": f[1],
            "descripcion": f[2],
            "fecha": f[3]
        })

    return jsonify(formularios)


# ------------------------------------------------
# ➕ CREAR FORMULARIO
# ------------------------------------------------
@app.route("/formularios", methods=["POST"])
def create_formulario():
    data = request.json
    nombre = data.get("nombre")
    descripcion = data.get("descripcion")
    fecha = data.get("fecha")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO formularios (nombre, descripcion, fecha) VALUES (?, ?, ?)",
                   (nombre, descripcion, fecha))
    conn.commit()
    conn.close()

    return jsonify({"message": "Formulario creado correctamente"})


# ------------------------------------------------
# ✏️ EDITAR FORMULARIO
# ------------------------------------------------
@app.route("/formularios/<int:id>", methods=["PUT"])
def update_formulario(id):
    data = request.json
    nombre = data.get("nombre")
    descripcion = data.get("descripcion")
    fecha = data.get("fecha")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE formularios
        SET nombre=?, descripcion=?, fecha=?
        WHERE id=?
    """, (nombre, descripcion, fecha, id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Formulario actualizado"})


# ------------------------------------------------
# ❌ ELIMINAR FORMULARIO  (🔥 NUEVO: DELETE)
# ------------------------------------------------
@app.route("/formularios/<int:id>", methods=["DELETE"])
def delete_formulario(id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM formularios WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Formulario eliminado"})


# ------------------------------------------------
# 🟢 FIX PARA RENDER (PORT DINÁMICO)
# ------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Servidor Flask iniciado en el puerto {port}")
    app.run(host="0.0.0.0", port=port)
