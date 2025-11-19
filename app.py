from flask import Flask, jsonify, request
from flask_cors import CORS
from bson import ObjectId
import json
from datetime import datetime
from flask.json.provider import DefaultJSONProvider

# Importar la conexión a MongoDB
from database import db  

app = Flask(__name__)
CORS(app)

# Colecciones
usuarios = db["usuarios"]
formularios = db["formularios"]
comentarios = db["comentarios"]


# ======================================================
# CONVERTIR ObjectId AUTOMÁTICAMENTE
# ======================================================
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

app.json = CustomJSONProvider(app)


# ======================================================
# RUTA PRINCIPAL
# ======================================================
@app.route("/")
def home():
    return "Backend Kuska funcionando correctamente 🚀"


# ======================================================
# LOGIN
# ======================================================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = usuarios.find_one({"email": email, "password": password})

    if not user:
        return jsonify({"status": "error", "message": "Credenciales inválidas"}), 401

    return jsonify({
        "status": "ok",
        "user": {
            "id": str(user["_id"]),
            "nombre": user.get("nombre", ""),
            "email": user.get("email", "")
        }
    })


# ======================================================
# REGISTRO
# ======================================================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")
    nombre = data.get("nombre")

    if usuarios.find_one({"email": email}):
        return jsonify({"status": "error", "message": "El email ya existe"}), 400

    nuevo_usuario = {
        "email": email,
        "password": password,
        "nombre": nombre
    }

    result = usuarios.insert_one(nuevo_usuario)

    return jsonify({
        "status": "ok",
        "user": {
            "id": str(result.inserted_id),
            "email": email,
            "nombre": nombre
        }
    })


# ======================================================
# FORMULARIOS (CRUD COMPLETO)
# ======================================================

# 1) CREAR FORMULARIO
@app.route("/formulario", methods=["POST"])
def crear_formulario():
    data = request.get_json()

    if not data.get("user_id"):
        return jsonify({"status": "error", "message": "Falta user_id"}), 400

    nuevo = {
        "user_id": data.get("user_id"),
        "nombre": data.get("nombre"),
        "telefono": data.get("telefono"),
        "direccion": data.get("direccion"),
        "foto": data.get("foto"),
        "lat": data.get("lat"),
        "lng": data.get("lng")
    }

    result = formularios.insert_one(nuevo)

    return jsonify({"status": "ok", "id": str(result.inserted_id)})


# 2) OBTENER FORMULARIO POR ID (formulario_id)
@app.route("/formulario/<form_id>", methods=["GET"])
def obtener_formulario(form_id):
    try:
        form = formularios.find_one({"_id": ObjectId(form_id)})
    except:
        return jsonify({"status": "error", "message": "ID inválido"}), 400

    if not form:
        return jsonify({"status": "error", "message": "Formulario no encontrado"}), 404

    form["_id"] = str(form["_id"])
    return jsonify({"status": "ok", "form": form})


# 3) OBTENER TODOS LOS FORMULARIOS
@app.route("/formularios", methods=["GET"])
def obtener_todos_formularios():
    lista = list(formularios.find({}))

    for f in lista:
        f["_id"] = str(f["_id"])

    return jsonify({"status": "ok", "formularios": lista})


# 4) ELIMINAR FORMULARIO POR ID
@app.route("/formulario/<form_id>", methods=["DELETE"])
def eliminar_formulario(form_id):
    try:
        result = formularios.delete_one({"_id": ObjectId(form_id)})
    except:
        return jsonify({"status": "error", "message": "ID inválido"}), 400

    if result.deleted_count == 0:
        return jsonify({"status": "error", "message": "Formulario no encontrado"}), 404

    return jsonify({"status": "ok", "message": "Formulario eliminado"})


# ======================================================
# COMENTARIOS
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
# OBTENER PROMEDIO DE PUNTUACIÓN
# ======================================================
@app.route("/rating/<lugar_id>", methods=["GET"])
def obtener_rating(lugar_id):
    lista = list(comentarios.find({"lugar_id": lugar_id}))

    if not lista:
        return jsonify({"status": "ok", "promedio": 0})

    promedio = round(sum(c.get("puntuacion", 0) for c in lista) / len(lista), 2)

    return jsonify({"status": "ok", "promedio": promedio})


# ======================================================
# EJECUCIÓN LOCAL
# ======================================================
if __name__ == "__main__":
    print("🚀 Servidor Flask iniciado")
    app.run(host="0.0.0.0", port=5000)
