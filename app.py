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
# CONFIGURACIÓN CARPETA UPLOADS
# ======================================================
UPLOADS_FOLDER = os.path.join(os.getcwd(), "uploads")

# Crear carpeta si no existe al iniciar
if not os.path.exists(UPLOADS_FOLDER):
    os.makedirs(UPLOADS_FOLDER)
    print(f"📁 Carpeta UPLOADS creada: {UPLOADS_FOLDER}")
else:
    print(f"📁 Carpeta UPLOADS ya existe: {UPLOADS_FOLDER}")

# Verificar permisos de escritura
if os.access(UPLOADS_FOLDER, os.W_OK):
    print("✅ Permisos de escritura en UPLOADS: OK")
else:
    print("❌ SIN permisos de escritura en UPLOADS")

# ======================================================
# FUNCIÓN MEJORADA PARA GUARDAR FOTO
# ======================================================
def guardar_foto_en_carpeta(foto_base64, formulario_id):
    try:
        print(f"🔄 Iniciando guardado de foto para formulario: {formulario_id}")
        
        if not foto_base64:
            print("❌ No hay foto base64 para guardar")
            return ""

        # Verificar que la carpeta existe y tiene permisos
        if not os.path.exists(UPLOADS_FOLDER):
            os.makedirs(UPLOADS_FOLDER)
            print(f"📁 Carpeta UPLOADS creada: {UPLOADS_FOLDER}")

        if not os.access(UPLOADS_FOLDER, os.W_OK):
            print("❌ SIN PERMISOS de escritura en UPLOADS")
            return ""

        # Limpiar cabecera base64 si viene con prefijo
        if foto_base64.startswith("data:image"):
            foto_base64 = foto_base64.split(",")[1]
            print("🔧 Base64 con prefijo data:image - prefijo removido")

        # Generar nombre único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"foto_{formulario_id}_{timestamp}.jpg"
        filepath = os.path.join(UPLOADS_FOLDER, filename)

        print(f"📸 Guardando foto como: {filename}")
        print(f"📂 Ruta completa: {filepath}")
        print(f"📊 Longitud Base64: {len(foto_base64)} caracteres")

        # Decodificar y guardar archivo
        try:
            img_bytes = base64.b64decode(foto_base64)
            print(f"📊 Imagen decodificada: {len(img_bytes)} bytes")
            
            with open(filepath, "wb") as f:
                f.write(img_bytes)
            print(f"💾 Archivo escrito en: {filepath}")
                
        except Exception as decode_error:
            print(f"❌ Error decodificando base64: {decode_error}")
            return ""

        # Verificar que el archivo se creó
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✅ Foto guardada EXITOSAMENTE: {filename} ({file_size} bytes)")
            return filename
        else:
            print("❌ ERROR: Archivo no se creó después de guardar")
            return ""

    except Exception as e:
        print(f"❌ Error CRÍTICO en guardar_foto_en_carpeta: {e}")
        return ""

# ======================================================
# RUTAS DEBUG MEJORADAS
# ======================================================
@app.route("/debug-uploads")
def debug_uploads():
    try:
        archivos = []
        if os.path.exists(UPLOADS_FOLDER):
            archivos = os.listdir(UPLOADS_FOLDER)
        
        return jsonify({
            "ruta_uploads": UPLOADS_FOLDER,
            "existe_carpeta": os.path.exists(UPLOADS_FOLDER),
            "permiso_escritura": os.access(UPLOADS_FOLDER, os.W_OK) if os.path.exists(UPLOADS_FOLDER) else False,
            "archivos": archivos,
            "total_archivos": len(archivos),
            "ruta_actual": os.getcwd()
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/debug-formulario/<form_id>")
def debug_formulario(form_id):
    try:
        formulario = formularios.find_one({"_id": ObjectId(form_id)})
        if not formulario:
            return jsonify({"error": "Formulario no encontrado"})
        
        formulario["_id"] = str(formulario["_id"])
        
        # Verificar archivo físico
        foto_en_carpeta = False
        archivo_info = {}
        if formulario.get("foto_archivo"):
            filepath = os.path.join(UPLOADS_FOLDER, formulario["foto_archivo"])
            foto_en_carpeta = os.path.exists(filepath)
            if foto_en_carpeta:
                archivo_info = {
                    "ruta": filepath,
                    "tamaño": os.path.getsize(filepath),
                    "existe": True
                }
            else:
                archivo_info = {
                    "ruta": filepath,
                    "existe": False
                }
        
        return jsonify({
            "formulario_id": str(formulario["_id"]),
            "tiene_foto_base64": bool(formulario.get("foto")),
            "tiene_foto_archivo": bool(formulario.get("foto_archivo")),
            "nombre_archivo": formulario.get("foto_archivo", ""),
            "foto_en_carpeta": foto_en_carpeta,
            "archivo_info": archivo_info
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/debug-completo")
def debug_completo():
    try:
        # Información del sistema
        info = {
            "sistema": {
                "ruta_actual": os.getcwd(),
                "plataforma": os.name,
                "separador": os.sep
            },
            "uploads": {
                "ruta": UPLOADS_FOLDER,
                "existe": os.path.exists(UPLOADS_FOLDER),
                "permiso_escritura": os.access(UPLOADS_FOLDER, os.W_OK),
                "archivos": os.listdir(UPLOADS_FOLDER) if os.path.exists(UPLOADS_FOLDER) else []
            },
            "formularios_db": {
                "total": formularios.count_documents({}),
                "con_foto_base64": formularios.count_documents({"foto": {"$ne": ""}}),
                "con_foto_archivo": formularios.count_documents({"foto_archivo": {"$ne": ""}})
            },
            "test_escritura": None
        }
        
        # Test de escritura
        test_file = os.path.join(UPLOADS_FOLDER, "test_escritura.txt")
        try:
            with open(test_file, "w") as f:
                f.write("Test de escritura - " + datetime.now().isoformat())
            info["test_escritura"] = {"exito": True, "archivo": test_file}
            # Limpiar archivo de test
            if os.path.exists(test_file):
                os.remove(test_file)
        except Exception as e:
            info["test_escritura"] = {"exito": False, "error": str(e)}
        
        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)})

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
    try:
        lista = list(usuarios.find({}, {"password": 0}))
        for u in lista:
            u["_id"] = str(u["_id"])
        return jsonify({"status": "ok", "usuarios": lista})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/usuarios", methods=["POST"])
def crear_usuario():
    try:
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"status": "error", "message": "Email y password requeridos"}), 400

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
            "id": str(res.inserted_id),
            "message": "Usuario creado exitosamente"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/usuarios/<user_id>", methods=["DELETE"])
def eliminar_usuario(user_id):
    try:
        result = usuarios.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
        return jsonify({"status": "ok", "message": "Usuario eliminado"})
    except Exception as e:
        return jsonify({"status": "error", "message": "ID inválido"}), 400

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
            return jsonify({"status": "error", "message": "Email y password requeridos"}), 400

        user = usuarios.find_one({
            "email": email,
            "password": password
        })

        if not user:
            return jsonify({"status": "error", "message": "Credenciales inválidas"}), 401

        return jsonify({
            "status": "ok",
            "user": {
                "id": str(user["_id"]), 
                "email": user["email"]
            },
            "message": "Login exitoso"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ======================================================
# FORMULARIOS - VERSIÓN CORREGIDA CON MÁS LOGS
# ======================================================
@app.route("/formularios", methods=["POST"])
def crear_formulario():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400

        print("=" * 50)
        print("📋 INICIANDO CREACIÓN DE FORMULARIO")
        print("=" * 50)
        
        print(f"📸 ¿Viene foto en la petición? {bool(data.get('foto'))}")
        print(f"📊 Longitud del base64: {len(data.get('foto', '')) if data.get('foto') else 0} caracteres")
        print(f"👤 User ID: {data.get('user_id')}")
        print(f"🏢 Nombre: {data.get('nombre_comercial')}")

        # ✅ PRIMERO: Insertar el formulario en MongoDB
        form = {
            "user_id": data.get("user_id"),
            "nombre_comercial": data.get("nombre_comercial"),
            "tipo": data.get("tipo"),
            "direccion": data.get("direccion"),
            "contacto": data.get("contacto"),
            "fijo": data.get("fijo", ""),
            "email": data.get("email"),
            "ubicacion": data.get("ubicacion", ""),
            "descripcion": data.get("descripcion"),
            "web": data.get("web", ""),
            "habitaciones": data.get("habitaciones", 0),
            "foto": data.get("foto", ""),  # ✅ BASE64 se guarda en MongoDB
            "foto_archivo": "",  # Inicialmente vacío - se actualizará después
            "lat": data.get("lat", 0),
            "lng": data.get("lng", 0),
            "fecha": datetime.now()
        }

        res = formularios.insert_one(form)
        form_id = str(res.inserted_id)
        print(f"✅ Formulario insertado en MongoDB: {form_id}")

        # ✅ SEGUNDO: Guardar foto en carpeta (si viene)
        filename = ""
        if data.get("foto"):
            print(f"🔄 Intentando guardar foto en carpeta con ID: {form_id}")
            filename = guardar_foto_en_carpeta(data["foto"], form_id)
            
            if filename:
                # ✅ TERCERO: Actualizar el formulario con el nombre del archivo
                formularios.update_one(
                    {"_id": ObjectId(form_id)},
                    {"$set": {"foto_archivo": filename}}
                )
                print(f"📝 Formulario actualizado con foto_archivo: {filename}")
            else:
                print("⚠️ NO se pudo guardar la foto en carpeta, pero el base64 está en MongoDB")
        else:
            print("ℹ️ No hay foto para guardar en carpeta")

        print("=" * 50)
        print("🎯 FINALIZANDO CREACIÓN DE FORMULARIO")
        print(f"📁 Foto guardada en carpeta: {bool(filename)}")
        print("=" * 50)

        return jsonify({
            "status": "ok", 
            "id": form_id,
            "foto_guardada_en_carpeta": bool(filename),
            "message": "Formulario creado exitosamente"
        })

    except Exception as e:
        print(f"❌ Error en crear_formulario: {str(e)}")
        return jsonify({"status": "error", "message": f"Error al crear formulario: {str(e)}"}), 500

@app.route("/formularios", methods=["GET"])
def obtener_formularios():
    try:
        lista = list(formularios.find({}))
        for f in lista:
            f["_id"] = str(f["_id"])
        return jsonify({"status": "ok", "formularios": lista})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/formularios/<form_id>", methods=["DELETE"])
def eliminar_formulario(form_id):
    try:
        form = formularios.find_one({"_id": ObjectId(form_id)})
        if not form:
            return jsonify({"status": "error", "message": "Formulario no encontrado"}), 404

        # Eliminar archivo físico si existe
        if form and form.get("foto_archivo"):
            path = os.path.join(UPLOADS_FOLDER, form["foto_archivo"])
            if os.path.exists(path):
                os.remove(path)
                print(f"🗑️ Archivo eliminado: {path}")

        formularios.delete_one({"_id": ObjectId(form_id)})
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

        comentario = {
            "user_id": data.get("user_id"),
            "lugar_id": data.get("lugar_id"),
            "comentario": data.get("comentario", ""),
            "puntuacion": data.get("puntuacion", 0),
            "fecha": datetime.now()
        }
        res = comentarios.insert_one(comentario)
        return jsonify({"status": "ok", "id": str(res.inserted_id)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/comentarios/<lugar_id>", methods=["GET"])
def obtener_comentarios(lugar_id):
    try:
        lista = list(comentarios.find({"lugar_id": lugar_id}).sort("fecha", -1))
        for c in lista:
            c["_id"] = str(c["_id"])
            c["fecha"] = c["fecha"].isoformat()
        return jsonify({"status": "ok", "comentarios": lista})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ======================================================
# RATING
# ======================================================
@app.route("/rating/<lugar_id>", methods=["GET"])
def obtener_rating(lugar_id):
    try:
        lista = list(comentarios.find({"lugar_id": lugar_id}))
        if not lista:
            return jsonify({"status": "ok", "promedio": 0, "total": 0})
            
        puntuaciones = [c.get("puntuacion", 0) for c in lista if c.get("puntuacion") is not None]
        promedio = round(sum(puntuaciones) / len(puntuaciones), 2) if puntuaciones else 0
        return jsonify({"status": "ok", "promedio": promedio, "total": len(puntuaciones)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
    print("📁 Ruta de UPLOADS:", UPLOADS_FOLDER)
    print("📁 Ruta actual:", os.getcwd())
    app.run(host="0.0.0.0", port=5000, debug=True)