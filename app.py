from flask import Flask, jsonify, request
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime

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
@app.route("/")
def home():
    return "Backend Kuska funcionando correctamente 🚀"

# ======================================================
# LOGIN
# ======================================================
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400
            
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"status": "error", "message": "Email y contraseña requeridos"}), 400

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
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error en el servidor: {str(e)}"}), 500

# ======================================================
# REGISTRO
# ======================================================
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400

        email = data.get("email")
        password = data.get("password")
        nombre = data.get("nombre")

        if not email or not password or not nombre:
            return jsonify({"status": "error", "message": "Todos los campos son requeridos"}), 400

        if usuarios.find_one({"email": email}):
            return jsonify({"status": "error", "message": "El email ya existe"}), 400

        nuevo_usuario = {
            "email": email,
            "password": password,
            "nombre": nombre,
            "fecha_creacion": datetime.now()
        }

        result = usuarios.insert_one(nuevo_usuario)

        return jsonify({
            "status": "ok",
            "message": "Usuario registrado exitosamente",
            "user": {
                "id": str(result.inserted_id),
                "email": email,
                "nombre": nombre
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error en el servidor: {str(e)}"}), 500

# ======================================================
# FORMULARIOS (CRUD COMPLETO)
# ======================================================

# 1) CREAR FORMULARIO
@app.route("/formulario", methods=["POST"])
def crear_formulario():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400

        if not data.get("user_id"):
            return jsonify({"status": "error", "message": "Falta user_id"}), 400

        nuevo_formulario = {
            "user_id": data.get("user_id"),
            "nombre": data.get("nombre"),
            "telefono": data.get("telefono"),
            "direccion": data.get("direccion"),
            "foto": data.get("foto", ""),
            "lat": data.get("lat", 0),
            "lng": data.get("lng", 0),
            "fecha_creacion": datetime.now()
        }

        result = formularios.insert_one(nuevo_formulario)

        return jsonify({
            "status": "ok", 
            "message": "Formulario creado exitosamente",
            "id": str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error en el servidor: {str(e)}"}), 500

# 2) OBTENER FORMULARIO POR ID
@app.route("/formulario/<form_id>", methods=["GET"])
def obtener_formulario(form_id):
    try:
        if not form_id or form_id == "null":
            return jsonify({"status": "error", "message": "ID inválido"}), 400

        form = formularios.find_one({"_id": ObjectId(form_id)})
        
        if not form:
            return jsonify({"status": "error", "message": "Formulario no encontrado"}), 404

        form["_id"] = str(form["_id"])
        return jsonify({"status": "ok", "form": form})
        
    except Exception as e:
        return jsonify({"status": "error", "message": "ID inválido"}), 400

# 3) OBTENER TODOS LOS FORMULARIOS
@app.route("/formularios", methods=["GET"])
def obtener_todos_formularios():
    try:
        lista = list(formularios.find({}))

        for f in lista:
            f["_id"] = str(f["_id"])

        return jsonify({"status": "ok", "formularios": lista})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al obtener formularios: {str(e)}"}), 500

# 4) ELIMINAR FORMULARIO POR ID
@app.route("/formulario/<form_id>", methods=["DELETE"])
def eliminar_formulario(form_id):
    try:
        if not form_id:
            return jsonify({"status": "error", "message": "ID requerido"}), 400

        result = formularios.delete_one({"_id": ObjectId(form_id)})

        if result.deleted_count == 0:
            return jsonify({"status": "error", "message": "Formulario no encontrado"}), 404

        return jsonify({"status": "ok", "message": "Formulario eliminado"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": "ID inválido"}), 400

# ======================================================
# COMENTARIOS
# ======================================================
@app.route("/comentario", methods=["POST"])
def guardar_comentario():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400

        if not data.get("user_id") or not data.get("lugar_id"):
            return jsonify({"status": "error", "message": "user_id y lugar_id requeridos"}), 400

        comentario = {
            "user_id": data.get("user_id"),
            "lugar_id": data.get("lugar_id"),
            "comentario": data.get("comentario", ""),
            "puntuacion": data.get("puntuacion", 0),
            "fecha": datetime.now()
        }

        result = comentarios.insert_one(comentario)

        return jsonify({
            "status": "ok", 
            "message": "Comentario guardado",
            "id": str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al guardar comentario: {str(e)}"}), 500

# ======================================================
# OBTENER COMENTARIOS DE UN LUGAR
# ======================================================
@app.route("/comentarios/<lugar_id>", methods=["GET"])
def obtener_comentarios(lugar_id):
    try:
        if not lugar_id:
            return jsonify({"status": "error", "message": "lugar_id requerido"}), 400

        lista = list(comentarios.find({"lugar_id": lugar_id}).sort("fecha", -1))

        for c in lista:
            c["_id"] = str(c["_id"])
            # Convertir fecha a string si es necesario
            if isinstance(c.get("fecha"), datetime):
                c["fecha"] = c["fecha"].isoformat()

        return jsonify({"status": "ok", "comentarios": lista})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al obtener comentarios: {str(e)}"}), 500

# ======================================================
# OBTENER PROMEDIO DE PUNTUACIÓN
# ======================================================
@app.route("/rating/<lugar_id>", methods=["GET"])
def obtener_rating(lugar_id):
    try:
        if not lugar_id:
            return jsonify({"status": "error", "message": "lugar_id requerido"}), 400

        lista = list(comentarios.find({"lugar_id": lugar_id}))

        if not lista:
            return jsonify({"status": "ok", "promedio": 0, "total": 0})

        puntuaciones = [c.get("puntuacion", 0) for c in lista if c.get("puntuacion") is not None]
        promedio = round(sum(puntuaciones) / len(puntuaciones), 2) if puntuaciones else 0

        return jsonify({
            "status": "ok", 
            "promedio": promedio,
            "total": len(puntuaciones)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al calcular rating: {str(e)}"}), 500

# ======================================================
# MANEJO DE ERRORES GLOBAL
# ======================================================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Error interno del servidor"}), 500

# ======================================================
# EJECUCIÓN LOCAL
# ======================================================
if __name__ == "__main__":
    print("🚀 Servidor Flask iniciado en http://0.0.0.0:5000")
    print("📊 Colecciones disponibles: usuarios, formularios, comentarios")
    app.run(host="0.0.0.0", port=5000, debug=True)