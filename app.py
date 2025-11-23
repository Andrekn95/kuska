from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime
import base64
import os

# Conexión MongoDB
from database import db  

app = Flask(__name__)
CORS(app)

# Colecciones
usuarios = db["usuarios"]
formularios = db["formularios"]
comentarios = db["comentarios"]

# ======================================================
# CREAR CARPETA UPLOADS AL INICIAR SERVIDOR
# ======================================================
UPLOADS_FOLDER = os.path.join(os.getcwd(), "uploads")

if not os.path.exists(UPLOADS_FOLDER):
    os.makedirs(UPLOADS_FOLDER)
    print(f"📁 Carpeta creada: {UPLOADS_FOLDER}")
else:
    print(f"📁 Carpeta de uploads OK: {UPLOADS_FOLDER}")

# ======================================================
# FUNCIÓN PARA GUARDAR FOTO EN CARPETA
# ======================================================
def guardar_foto_en_carpeta(foto_base64, formulario_id):
    try:
        if not foto_base64:
            return ""

        # limpiar cabecera base64
        if foto_base64.startswith("data:image"):
            foto_base64 = foto_base64.split(",")[1]

        # generar nombre único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"foto_{formulario_id}_{timestamp}.jpg"
        filepath = os.path.join(UPLOADS_FOLDER, filename)

        # decodificar y guardar archivo
        try:
            img_bytes = base64.b64decode(foto_base64)
            with open(filepath, "wb") as f:
                f.write(img_bytes)
        except:
            print("⚠ Error decodificando base64")
            return ""

        # verificar
        if os.path.exists(filepath):
            print(f"📸 Foto guardada: {filepath}")
            return filename
        else:
            print("⚠ Archivo no creado")
            return ""

    except Exception as e:
        print(f"❌ Error guardar_foto_en_carpeta: {e}")
        return ""

# ======================================================
# RUTAS DEBUG
# ======================================================
@app.route("/debug-uploads")
def debug_uploads():
    return jsonify({
        "ruta_uploads": UPLOADS_FOLDER,
        "existe": os.path.exists(UPLOADS_FOLDER),
        "archivos": os.listdir(UPLOADS_FOLDER),
        "total": len(os.listdir(UPLOADS_FOLDER))
    })

# ======================================================
# HOME
# ======================================================
@app.route("/")
def home():
    return "Backend Kuska funcionando correctamente 🚀"

# ======================================================
# USUARIOS
# ======================================================
@app.route("/usuarios", methods=["GET"])
def obtener_usuarios():
    lista = list(usuarios.find({}, {"password": 0}))
    for u in lista:
        u["_id"] = str(u["_id"])
    return jsonify({"status": "ok", "usuarios": lista})

@app.route("/usuarios", methods=["POST"])
def crear_usuario():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if usuarios.find_one({"email": email}):
        return jsonify({"status": "error", "message": "Email ya registrado"}), 400

    usuario = {
        "email": email,
        "password": password,
        "fecha": datetime.now()
    }

    res = usuarios.insert_one(usuario)
    return jsonify({
        "status": "ok",
        "id": str(res.inserted_id)
    })

@app.route("/usuarios/<user_id>", methods=["DELETE"])
def eliminar_usuario(user_id):
    usuarios.delete_one({"_id": ObjectId(user_id)})
    return jsonify({"status": "ok"})

# ======================================================
# LOGIN
# ======================================================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = usuarios.find_one({
        "email": data.get("email"),
        "password": data.get("password")
    })

    if not user:
        return jsonify({"status": "error", "message": "Credenciales inválidas"}), 401

    return jsonify({
        "status": "ok",
        "user": {"id": str(user["_id"]), "email": user["email"]}
    })

# ======================================================
# FORMULARIOS
# ======================================================
@app.route("/formularios", methods=["POST"])
def crear_formulario():
    data = request.get_json()

    # Inserta sin foto primero
    form = {
        "user_id": data.get("user_id"),
        "nombre_comercial": data.get("nombre_comercial"),
        "tipo": data.get("tipo"),
        "direccion": data.get("direccion"),
        "contacto": data.get("contacto"),
        "email": data.get("email"),
        "descripcion": data.get("descripcion"),
        "lat": data.get("lat", 0),
        "lng": data.get("lng", 0),
        "foto_archivo": "",
        "fecha": datetime.now()
    }

    res = formularios.insert_one(form)
    form_id = str(res.inserted_id)

    # Guardar foto si viene
    if data.get("foto"):
        filename = guardar_foto_en_carpeta(data["foto"], form_id)
        if filename:
            formularios.update_one(
                {"_id": ObjectId(form_id)},
                {"$set": {"foto_archivo": filename}}
            )

    return jsonify({"status": "ok", "id": form_id})

@app.route("/formularios", methods=["GET"])
def obtener_formularios():
    lista = list(formularios.find({}))
    for f in lista:
        f["_id"] = str(f["_id"])
    return jsonify({"status": "ok", "formularios": lista})

@app.route("/formularios/<form_id>", methods=["DELETE"])
def eliminar_formulario(form_id):
    form = formularios.find_one({"_id": ObjectId(form_id)})

    # eliminar archivo físico
    if form and form.get("foto_archivo"):
        path = os.path.join(UPLOADS_FOLDER, form["foto_archivo"])
        if os.path.exists(path):
            os.remove(path)

    formularios.delete_one({"_id": ObjectId(form_id)})
    return jsonify({"status": "ok"})

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
        "fecha": datetime.now()
    }
    res = comentarios.insert_one(comentario)
    return jsonify({"status": "ok", "id": str(res.inserted_id)})

@app.route("/comentarios/<lugar_id>", methods=["GET"])
def obtener_comentarios(lugar_id):
    lista = list(comentarios.find({"lugar_id": lugar_id}).sort("fecha", -1))
    for c in lista:
        c["_id"] = str(c["_id"])
        c["fecha"] = c["fecha"].isoformat()
    return jsonify({"status": "ok", "comentarios": lista})

# ======================================================
# RATING
# ======================================================
@app.route("/rating/<lugar_id>", methods=["GET"])
def obtener_rating(lugar_id):
    lista = list(comentarios.find({"lugar_id": lugar_id}))
    puntuaciones = [c.get("puntuacion", 0) for c in lista]
    promedio = round(sum(puntuaciones) / len(puntuaciones), 2) if puntuaciones else 0
    return jsonify({"status": "ok", "promedio": promedio})

# ======================================================
# SERVIR FOTOS
# ======================================================
@app.route("/uploads/<filename>")
def descargar_foto(filename):
    try:
        return send_from_directory(UPLOADS_FOLDER, filename)
    except:
        return jsonify({"status": "error", "message": "Archivo no encontrado"}), 404

# ======================================================
# RUN SERVER
# ======================================================
if __name__ == "__main__":
    print("🚀 Servidor corriendo en http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
