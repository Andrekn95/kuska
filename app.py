from flask import Flask, jsonify, request
from flask_cors import CORS
from bson import ObjectId
import json
from datetime import datetime

# Importar la conexión de database.py
from database import db  

app = Flask(__name__)
CORS(app)

# Colecciones
usuarios = db["usuarios"]
formularios = db["formularios"]
comentarios = db["comentarios"]


# --------------------------
# Convertir ObjectId a string
# --------------------------
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

app.json_encoder = JSONEncoder


# --------------------------
# RUTA BASE
# --------------------------
@app.route("/")
def home():
    return "Backend Kuska funcionando correctamente 🚀"


# --------------------------
# LOGIN
# --------------------------
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = usuarios.find_one({"email": email, "password": password})

    if user:
        return jsonify({
            "status": "ok",
            "user": {
                "id": str(user["_id"]),
                "nombre": user.get("nombre", ""),
                "email": user.get("email", "")
            }
        })
    else:
        return jsonify({"status": "error", "message": "Credenciales inválidas"}), 401


# --------------------------
# REGISTRO
# --------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    nombre = data.get("nombre")

    if usuarios.find_one({"email": email}):
        return jsonify({"status": "error", "message": "El email ya existe"}), 400

    new_user = {
        "email": email,
        "password": password,
        "nombre": nombre
    }

    result = usuarios.insert_one(new_user)

    return jsonify({
        "status": "ok",
        "user": {
            "id": str(result.inserted_id),
            "email": email,
            "nombre": nombre
        }
    })


# ======================================================
# OBTENER TODOS LOS USUARIOS (SIN CONTRASEÑA)
# ======================================================
@app.route("/usuarios", methods=["GET"])
def obtener_usuarios():
    lista = list(usuarios.find({}))

    usuarios_limpios = []
    for u in lista:
        usuarios_limpios.append({
            "id": str(u["_id"]),
            "email": u.get("email", ""),
            "nombre": u.get("nombre", "")
        })

    return jsonify({"status": "ok", "usuarios": usuarios_limpios})


# --------------------------
# GUARDAR FORMULARIO
# --------------------------
@app.route("/formulario", methods=["POST"])
def guardar_formulario():
    data = request.get_json()

    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "Falta user_id"}), 400

    formulario = {
        "user_id": user_id,
        "nombre": data.get("nombre"),
        "telefono": data.get("telefono"),
        "direccion": data.get("direccion"),
        "foto": data.get("foto"),
        "lat": data.get("lat"),
        "lng": data.get("lng")
    }

    result = formularios.insert_one(formulario)

    return jsonify({"status": "ok", "id": str(result.inserted_id)})


# --------------------------
# OBTENER FORMULARIO POR USER_ID
# --------------------------
@app.route("/formulario/<user_id>", methods=["GET"])
def obtener_formulario(user_id):
    form = formularios.find_one({"user_id": user_id})

    if not form:
        return jsonify({"status": "empty"})

    form["_id"] = str(form["_id"])
    return jsonify({"status": "ok", "form": form})


# ======================================================
# OBTENER TODOS LOS FORMULARIOS (PÚBLICOS)
# ======================================================
@app.route("/formularios", methods=["GET"])
def obtener_todos_formularios():
    lista = list(formularios.find({}))

    for f in lista:
        f["_id"] = str(f["_id"])

    return jsonify({"status": "ok", "formularios": lista})


# ======================================================
# GUARDAR COMENTARIO + PUNTUACIÓN
# ======================================================
@app.route("/comentario", methods=["POST"])
def guardar_comentario():
    data = request.get_json()

    comentario = {
        "user_id": data.get("user_id"),
        "lugar_id": data.get("lugar_id"),
        "comentario": data.get("comentario", ""),
        "puntuacion": data.get("puntuacion", 0),
        "fecha": datetime.now().isoformat()
    }

    result = comentarios.insert_one(comentario)

    return jsonify({"status": "ok", "id": str(result.inserted_id)})


# ======================================================
# OBTENER COMENTARIOS DE UN LUGAR
# ======================================================
@app.route("/comentarios/<lugar_id>", methods=["GET"])
def obtener_comentarios(lugar_id):
    lista = list(comentarios.find({"lugar_id": lugar_id}))

    for c in lista:
        c["_id"] = str(c["_id"])

    return jsonify({"status": "ok", "comentarios": lista})


# ======================================================
# OBTENER PROMEDIO DE PUNTUACIÓN DE UN LUGAR
# ======================================================
@app.route("/rating/<lugar_id>", methods=["GET"])
def obtener_rating(lugar_id):
    lista = list(comentarios.find({"lugar_id": lugar_id}))

    if not lista:
        return jsonify({"status": "ok", "promedio": 0})

    total = sum([c.get("puntuacion", 0) for c in lista])
    promedio = round(total / len(lista), 2)

    return jsonify({"status": "ok", "promedio": promedio})


# --------------------------
# EJECUCIÓN LOCAL / RENDER
# --------------------------
if __name__ == "__main__":
    print("🚀 Servidor Flask iniciado")
    app.run(host="0.0.0.0", port=5000)
