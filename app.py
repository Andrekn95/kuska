from flask import Flask, jsonify, request
from flask_cors import CORS
from database import db
from bson import ObjectId
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ---------------------------------------
# JSON Encoder para ObjectId
# ---------------------------------------
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

app.json_encoder = JSONEncoder


# ---------------------------------------
# 1. REGISTRO DE USUARIO
# ---------------------------------------
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"status": "error", "message": "Email y contraseña requeridos"}), 400

        existing = db.usuarios.find_one({"email": email})
        if existing:
            return jsonify({"status": "error", "message": "El usuario ya existe"}), 400

        result = db.usuarios.insert_one({
            "email": email,
            "password": password,
            "fecha_registro": datetime.now()
        })

        return jsonify({
            "status": "ok",
            "message": "Usuario registrado",
            "userId": str(result.inserted_id)
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------
# 2. LOGIN
# ---------------------------------------
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"status": "error", "message": "Email y contraseña requeridos"}), 400

        user = db.usuarios.find_one({"email": email})

        if not user or user["password"] != password:
            return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401

        return jsonify({
            "status": "ok",
            "message": "Login correcto",
            "user": {
                "id": str(user["_id"]),
                "email": user["email"]
            }
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------
# 3. GUARDAR FORMULARIO
# ---------------------------------------
@app.route("/save-form", methods=["POST"])
def save_form():
    try:
        data = request.json

        # userId ES OBLIGATORIO
        user_id = data.get("userId")
        if not user_id:
            return jsonify({"status": "error", "message": "userId es requerido"}), 400

        required_fields = ["nombreComercial", "tipo", "direccion", "contacto", "email", "ubicacion"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"status": "error", "message": f"Campo requerido: {field}"}), 400

        form_data = {
            "userId": user_id,   # 🔥 RELACIÓN REAL (usuario → formulario)
            "nombreComercial": data.get("nombreComercial"),
            "tipo": data.get("tipo"),
            "direccion": data.get("direccion"),
            "fijo": data.get("fijo"),
            "contacto": data.get("contacto"),
            "email": data.get("email"),
            "provincia": data.get("ubicacion"),
            "descripcion": data.get("descripcion"),
            "web": data.get("web"),
            "habitaciones": data.get("habitaciones"),
            "foto": data.get("foto"),
            "lat": data.get("lat"),
            "lng": data.get("lng"),
            "ubi": data.get("ubi"),
            "fecha_creacion": datetime.now()
        }

        result = db.formularios.insert_one(form_data)

        return jsonify({
            "status": "ok",
            "message": "Formulario guardado correctamente",
            "formId": str(result.inserted_id)
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------
# 4. OBTENER FORMULARIOS POR USUARIO (ID) - 🔥 ENDPOINT PRINCIPAL
# ---------------------------------------
@app.route("/establecimientos/usuario/<user_id>", methods=["GET"])
def get_establecimientos_usuario(user_id):
    try:
        print(f"🔍 Buscando establecimientos para userId: {user_id}")
        
        establecimientos = list(db.formularios.find({"userId": user_id}))
        print(f"📊 Establecimientos encontrados: {len(establecimientos)}")

        for est in establecimientos:
            est["_id"] = str(est["_id"])

        return jsonify(establecimientos)

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------
# 5. OBTENER FORMULARIOS POR EMAIL (ENDPOINT ALTERNATIVO)
# ---------------------------------------
@app.route("/get-forms/<email>", methods=["GET"])
def get_forms_by_email(email):
    try:
        print(f"🔍 Buscando formularios para email: {email}")
        
        forms = list(db.formularios.find({"email": email}))
        print(f"📊 Formularios encontrados: {len(forms)}")
        
        for form in forms:
            form["_id"] = str(form["_id"])

        return jsonify({
            "status": "ok",
            "total": len(forms),
            "formularios": forms
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------
# 6. OBTENER UN FORMULARIO ESPECÍFICO
# ---------------------------------------
@app.route("/get-form/<form_id>", methods=["GET"])
def get_form(form_id):
    try:
        form = db.formularios.find_one({"_id": ObjectId(form_id)})

        if not form:
            return jsonify({"status": "error", "message": "Formulario no encontrado"}), 404

        form["_id"] = str(form["_id"])

        return jsonify({
            "status": "ok",
            "formulario": form
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------
# 7. ACTUALIZAR FORMULARIO
# ---------------------------------------
@app.route("/update-form/<form_id>", methods=["PUT"])
def update_form(form_id):
    try:
        data = request.json

        result = db.formularios.update_one(
            {"_id": ObjectId(form_id)},
            {"$set": data}
        )

        if result.matched_count == 0:
            return jsonify({"status": "error", "message": "Formulario no encontrado"}), 404

        return jsonify({"status": "ok", "message": "Formulario actualizado"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------
# 8. ELIMINAR FORMULARIO
# ---------------------------------------
@app.route("/delete-form/<form_id>", methods=["DELETE"])
def delete_form(form_id):
    try:
        result = db.formularios.delete_one({"_id": ObjectId(form_id)})

        if result.deleted_count == 0:
            return jsonify({"status": "error", "message": "Formulario no encontrado"}), 404

        return jsonify({"status": "ok", "message": "Formulario eliminado"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------
# 9. OBTENER TODOS LOS ESTABLECIMIENTOS (MAPA)
# ---------------------------------------
@app.route("/establecimientos", methods=["GET"])
def get_all_establecimientos():
    try:
        establecimientos = list(db.formularios.find(
            {},
            {"nombreComercial": 1, "tipo": 1, "direccion": 1, "lat": 1, "lng": 1, "provincia": 1, "foto": 1}
        ))

        for est in establecimientos:
            est["_id"] = str(est["_id"])

        return jsonify({
            "status": "ok",
            "establecimientos": establecimientos
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------
# 10. ENDPOINT DE DEBUG
# ---------------------------------------
@app.route("/debug", methods=["GET"])
def debug():
    try:
        # Contar documentos
        usuarios_count = db.usuarios.count_documents({})
        formularios_count = db.formularios.count_documents({})
        
        # Obtener algunos ejemplos
        usuarios_ejemplo = list(db.usuarios.find().limit(3))
        formularios_ejemplo = list(db.formularios.find().limit(3))
        
        for user in usuarios_ejemplo:
            user["_id"] = str(user["_id"])
        for form in formularios_ejemplo:
            form["_id"] = str(form["_id"])
            
        return jsonify({
            "status": "ok",
            "database_status": "conectada",
            "counts": {
                "usuarios": usuarios_count,
                "formularios": formularios_count
            },
            "ejemplos": {
                "usuarios": usuarios_ejemplo,
                "formularios": formularios_ejemplo
            },
            "endpoints_disponibles": [
                "/register (POST)",
                "/login (POST)", 
                "/save-form (POST)",
                "/establecimientos/usuario/<user_id> (GET)",
                "/get-forms/<email> (GET)",
                "/get-form/<form_id> (GET)",
                "/update-form/<form_id> (PUT)",
                "/delete-form/<form_id> (DELETE)",
                "/establecimientos (GET)"
            ]
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error en debug: {str(e)}"}), 500


# ---------------------------------------
# 11. HEALTH CHECK
# ---------------------------------------
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "ok", 
        "message": "Backend funcionando correctamente",
        "timestamp": datetime.now().isoformat()
    })


# ---------------------------------------
# RUN SERVER
# ---------------------------------------
if __name__ == "__main__":
    print("🚀 Iniciando servidor Flask...")
    print("📊 Endpoints disponibles:")
    print("   POST /register")
    print("   POST /login") 
    print("   POST /save-form")
    print("   GET  /establecimientos/usuario/<user_id>")
    print("   GET  /get-forms/<email>")
    print("   GET  /get-form/<form_id>")
    print("   PUT  /update-form/<form_id>")
    print("   DELETE /delete-form/<form_id>")
    print("   GET  /establecimientos")
    print("   GET  /debug")
    print("   GET  /health")
    print("🔧 Servidor listo en http://127.0.0.1:5000")
    
    app.run(port=5000, debug=True)