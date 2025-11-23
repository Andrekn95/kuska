from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from bson import ObjectId
from datetime import datetime
import base64
import os

# Importar la conexión a MongoDB
from database import db  

app = Flask(__name__)
CORS(app)

# Colecciones
usuarios = db["usuarios"]
formularios = db["formularios"]
comentarios = db["comentarios"]

# ======================================================
# FUNCIÓN MEJORADA PARA GUARDAR FOTO EN CARPETA
# ======================================================
def guardar_foto_en_carpeta(foto_base64, formulario_id):
    try:
        if not foto_base64 or not formulario_id:
            print("❌ Datos insuficientes para guardar foto")
            return ""
            
        # Ruta absoluta para uploads
        uploads_path = os.path.join(os.getcwd(), "uploads")
        if not os.path.exists(uploads_path):
            os.makedirs(uploads_path)
            print(f"📂 Carpeta uploads creada: {uploads_path}")
            
        # Verificar permisos
        if not os.access(uploads_path, os.W_OK):
            print("❌ Sin permisos de escritura en uploads/")
            return ""

        # Generar nombre único
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"establecimiento_{formulario_id}_{timestamp}.jpg"
        filepath = os.path.join(uploads_path, filename)
        
        print(f"📸 Guardando foto: {filename}")
        
        # Limpiar Base64 si viene con prefijo
        if foto_base64.startswith('data:image'):
            foto_base64 = foto_base64.split(',')[1]
        
        # Decodificar y guardar
        try:
            photo_data = base64.b64decode(foto_base64)
            print(f"📊 Imagen decodificada: {len(photo_data)} bytes")
            
            with open(filepath, "wb") as f:
                f.write(photo_data)
                
            # Verificar que se creó
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"✅ Foto guardada: {filepath} ({file_size} bytes)")
                return filename
            else:
                print("❌ Archivo no se creó")
                return ""
                
        except Exception as e:
            print(f"❌ Error procesando imagen: {e}")
            return ""
        
    except Exception as e:
        print(f"❌ Error general guardando foto: {str(e)}")
        return ""

# ======================================================
# VERIFICAR CARPETA UPLOADS
# ======================================================
@app.route("/debug-uploads")
def debug_uploads():
    try:
        uploads_path = os.path.join(os.getcwd(), "uploads")
        exists = os.path.exists(uploads_path)
        can_write = os.access(uploads_path, os.W_OK) if exists else False
        
        files = []
        if exists:
            files = os.listdir(uploads_path)
        
        return jsonify({
            "ruta_actual": os.getcwd(),
            "ruta_uploads": uploads_path,
            "carpeta_existe": exists,
            "permiso_escritura": can_write,
            "archivos": files,
            "total_archivos": len(files)
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# ======================================================
# VERIFICAR FORMULARIO Y FOTO
# ======================================================
@app.route("/debug-formulario/<form_id>")
def debug_formulario(form_id):
    try:
        formulario = formularios.find_one({"_id": ObjectId(form_id)})
        if not formulario:
            return jsonify({"error": "Formulario no encontrado"})
        
        # Convertir ObjectId a string
        formulario["_id"] = str(formulario["_id"])
        
        # Verificar si el archivo existe
        foto_existe = False
        file_info = {}
        if formulario.get("foto_archivo"):
            filepath = os.path.join(os.getcwd(), "uploads", formulario["foto_archivo"])
            foto_existe = os.path.exists(filepath)
            if foto_existe:
                file_info = {
                    "ruta": filepath,
                    "tamaño": os.path.getsize(filepath),
                    "nombre": formulario["foto_archivo"]
                }
        
        return jsonify({
            "formulario": formulario,
            "foto_en_carpeta": foto_existe,
            "archivo_info": file_info,
            "tiene_foto_base64": bool(formulario.get("foto")),
            "tiene_foto_archivo": bool(formulario.get("foto_archivo"))
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# ======================================================
# RUTA PRINCIPAL
# ======================================================
@app.route("/")
def home():
    return "Backend Kuska funcionando correctamente 🚀"

# ======================================================
# USUARIOS - GET (Obtener todos los usuarios)
# ======================================================
@app.route("/usuarios", methods=["GET"])
def obtener_usuarios():
    try:
        lista_usuarios = list(usuarios.find({}, {"password": 0}))  # Excluir passwords
        
        for usuario in lista_usuarios:
            usuario["_id"] = str(usuario["_id"])
            
        return jsonify({
            "status": "ok", 
            "usuarios": lista_usuarios,
            "total": len(lista_usuarios)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al obtener usuarios: {str(e)}"}), 500

# ======================================================
# USUARIOS - POST (Crear usuario)
# ======================================================
@app.route("/usuarios", methods=["POST"])
def crear_usuario():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"status": "error", "message": "Email y password son requeridos"}), 400

        # Verificar si el usuario ya existe
        if usuarios.find_one({"email": email}):
            return jsonify({"status": "error", "message": "El email ya está registrado"}), 400

        nuevo_usuario = {
            "email": email,
            "password": password,
            "fecha_creacion": datetime.now(),
            "activo": True
        }

        result = usuarios.insert_one(nuevo_usuario)

        return jsonify({
            "status": "ok",
            "message": "Usuario registrado exitosamente",
            "user": {
                "id": str(result.inserted_id),
                "email": email
            }
        }), 201
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al crear usuario: {str(e)}"}), 500

# ======================================================
# USUARIOS - DELETE (Eliminar usuario)
# ======================================================
@app.route("/usuarios/<user_id>", methods=["DELETE"])
def eliminar_usuario(user_id):
    try:
        if not user_id or user_id == "null":
            return jsonify({"status": "error", "message": "ID de usuario requerido"}), 400

        result = usuarios.delete_one({"_id": ObjectId(user_id)})

        if result.deleted_count == 0:
            return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404

        return jsonify({
            "status": "ok", 
            "message": "Usuario eliminado exitosamente"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": "ID de usuario inválido"}), 400

# ======================================================
# LOGIN - GET (Verificar estado de login)
# ======================================================
@app.route("/login", methods=["GET"])
def verificar_login():
    try:
        return jsonify({
            "status": "ok",
            "message": "Servicio de login activo"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error en login: {str(e)}"}), 500

# ======================================================
# LOGIN - POST (Iniciar sesión)
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
            "message": "Login exitoso",
            "user": {
                "id": str(user["_id"]),
                "email": user.get("email", "")
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error en el servidor: {str(e)}"}), 500

# ======================================================
# FORMULARIOS - GET (Obtener todos los formularios)
# ======================================================
@app.route("/formularios", methods=["GET"])
def obtener_formularios():
    try:
        lista_formularios = list(formularios.find({}))

        for formulario in lista_formularios:
            formulario["_id"] = str(formulario["_id"])

        return jsonify({
            "status": "ok", 
            "formularios": lista_formularios,
            "total": len(lista_formularios)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al obtener formularios: {str(e)}"}), 500

# ======================================================
# FORMULARIOS - POST (Crear formulario) - VERSIÓN CORREGIDA
# ======================================================
@app.route("/formularios", methods=["POST"])
def crear_formulario():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No se recibieron datos"}), 400

        if not data.get("user_id"):
            return jsonify({"status": "error", "message": "user_id es requerido"}), 400

        print(f"📸 ¿Viene foto en la petición? {bool(data.get('foto'))}")

        # ✅ PRIMERO: Insertar el formulario en MongoDB para obtener el ID real
        nuevo_formulario = {
            "user_id": data.get("user_id"),
            "nombre_comercial": data.get("nombre_comercial"),
            "tipo": data.get("tipo"),
            "direccion": data.get("direccion"),
            "contacto": data.get("contacto"),
            "fijo": data.get("fijo"),
            "email": data.get("email"),
            "ubicacion": data.get("ubicacion"),
            "descripcion": data.get("descripcion"),
            "web": data.get("web"),
            "habitaciones": data.get("habitaciones"),
            "foto": data.get("foto", ""),  # Base64 (backup)
            "foto_archivo": "",  # Inicialmente vacío
            "lat": data.get("lat", 0),
            "lng": data.get("lng", 0),
            "fecha_creacion": datetime.now()
        }

        result = formularios.insert_one(nuevo_formulario)
        formulario_id = str(result.inserted_id)
        print(f"✅ Formulario insertado en MongoDB: {formulario_id}")

        # ✅ SEGUNDO: Ahora guardar la foto con el ID REAL del formulario
        foto_archivo = ""
        if data.get("foto"):
            print(f"🔄 Guardando foto con ID REAL del formulario: {formulario_id}")
            foto_archivo = guardar_foto_en_carpeta(data.get("foto"), formulario_id)
            print(f"📁 Resultado de guardar foto: {foto_archivo}")
            
            # ✅ TERCERO: Actualizar el formulario con la ruta de la foto
            if foto_archivo:
                formularios.update_one(
                    {"_id": ObjectId(formulario_id)}, 
                    {"$set": {"foto_archivo": foto_archivo}}
                )
                print(f"📝 Formulario actualizado con foto_archivo: {foto_archivo}")
            else:
                print("⚠️ No se pudo guardar la foto en carpeta")

        return jsonify({
            "status": "ok", 
            "message": "Formulario creado exitosamente",
            "id": formulario_id
        }), 201
        
    except Exception as e:
        print(f"❌ Error en crear_formulario: {str(e)}")
        return jsonify({"status": "error", "message": f"Error al crear formulario: {str(e)}"}), 500

# ======================================================
# FORMULARIOS - DELETE (Eliminar formulario)
# ======================================================
@app.route("/formularios/<form_id>", methods=["DELETE"])
def eliminar_formulario(form_id):
    try:
        if not form_id:
            return jsonify({"status": "error", "message": "ID de formulario requerido"}), 400

        # Opcional: También eliminar el archivo físico de la foto
        formulario = formularios.find_one({"_id": ObjectId(form_id)})
        if formulario and formulario.get("foto_archivo"):
            filepath = os.path.join(os.getcwd(), "uploads", formulario["foto_archivo"])
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🗑️ Archivo eliminado: {filepath}")

        result = formularios.delete_one({"_id": ObjectId(form_id)})

        if result.deleted_count == 0:
            return jsonify({"status": "error", "message": "Formulario no encontrado"}), 404

        return jsonify({
            "status": "ok", 
            "message": "Formulario eliminado exitosamente"
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": "ID de formulario inválido"}), 400

# ======================================================
# FORMULARIO - UPDATE (EDITAR formularios)
# ======================================================
@app.route("/formularios/<form_id>", methods=["PUT"])
def actualizar_formulario(form_id):
    try:
        data = request.get_json()
        update = {
            "nombre_comercial": data.get("nombre_comercial"),
            "tipo": data.get("tipo"),
            "direccion": data.get("direccion"),
            "contacto": data.get("contacto"),
            "email": data.get("email"),
            "descripcion": data.get("descripcion"),
            "lat": data.get("lat"),
            "lng": data.get("lng")
        }
        
        # Manejar actualización de foto si viene en la petición
        if data.get("foto"):
            print(f"🔄 Actualizando foto para formulario: {form_id}")
            foto_archivo = guardar_foto_en_carpeta(data.get("foto"), form_id)
            if foto_archivo:
                update["foto_archivo"] = foto_archivo
                update["foto"] = data.get("foto")  # Mantener base64 también
                print(f"📸 Nueva foto guardada: {foto_archivo}")
        
        # Eliminar claves None
        update = {k: v for k, v in update.items() if v is not None}
        
        result = formularios.update_one({"_id": ObjectId(form_id)}, {"$set": update})
        
        if result.matched_count == 1:
            return jsonify({"status":"ok", "message":"Formulario actualizado"})
        return jsonify({"status":"error", "message":"Formulario no encontrado"}), 404
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al actualizar: {str(e)}"}), 500

# ======================================================
# COMENTARIOS - POST (Crear comentario)
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
# COMENTARIOS - GET (Obtener comentarios de un lugar)
# ======================================================
@app.route("/comentarios/<lugar_id>", methods=["GET"])
def obtener_comentarios(lugar_id):
    try:
        if not lugar_id:
            return jsonify({"status": "error", "message": "lugar_id requerido"}), 400

        lista = list(comentarios.find({"lugar_id": lugar_id}).sort("fecha", -1))

        for c in lista:
            c["_id"] = str(c["_id"])
            if isinstance(c.get("fecha"), datetime):
                c["fecha"] = c["fecha"].isoformat()

        return jsonify({"status": "ok", "comentarios": lista})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al obtener comentarios: {str(e)}"}), 500

# ======================================================
# RATING - GET (Obtener promedio de puntuación)
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
# SERVIR FOTOS DESCARGA
# ======================================================
@app.route("/uploads/<filename>")
def descargar_foto(filename):
    try:
        return send_from_directory("uploads", filename)
    except Exception as e:
        return jsonify({"status": "error", "message": "Foto no encontrada"}), 404

# ======================================================
# LIMPIAR FOTOS HUÉRFANAS (Opcional)
# ======================================================
@app.route("/limpiar-fotos")
def limpiar_fotos():
    try:
        uploads_path = os.path.join(os.getcwd(), "uploads")
        if not os.path.exists(uploads_path):
            return jsonify({"status": "ok", "message": "No existe carpeta uploads"})
        
        # Obtener todos los formularios
        formularios_lista = list(formularios.find({}, {"foto_archivo": 1}))
        fotos_validas = {f["foto_archivo"] for f in formularios_lista if f.get("foto_archivo")}
        
        # Listar archivos en uploads
        archivos = os.listdir(uploads_path)
        eliminados = 0
        
        for archivo in archivos:
            if archivo not in fotos_validas:
                filepath = os.path.join(uploads_path, archivo)
                os.remove(filepath)
                eliminados += 1
                print(f"🗑️ Eliminado archivo huérfano: {archivo}")
        
        return jsonify({
            "status": "ok", 
            "message": f"Limpieza completada. Eliminados: {eliminados} archivos huérfanos"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ======================================================
# MANEJO DE ERRORES
# ======================================================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"status": "error", "message": "Error interno del servidor"}), 500

# ======================================================
# EJECUCIÓN
# ======================================================
if __name__ == "__main__":
    print("🚀 Servidor Flask iniciado en http://0.0.0.0:5000")
    print("📊 Endpoints disponibles:")
    print("   GET  /usuarios           - Listar usuarios")
    print("   POST /usuarios           - Crear usuario")
    print("   DELETE /usuarios/:id     - Eliminar usuario")
    print("   GET  /login              - Verificar login")
    print("   POST /login              - Iniciar sesión")
    print("   GET  /formularios        - Listar formularios")
    print("   POST /formularios        - Crear formulario")
    print("   DELETE /formularios/:id  - Eliminar formulario")
    print("   PUT  /formularios/:id    - Actualizar formulario")
    print("   POST /comentario         - Crear comentario")
    print("   GET  /comentarios/:id    - Obtener comentarios")
    print("   GET  /rating/:id         - Obtener rating")
    print("   GET  /uploads/:filename  - Descargar foto")
    print("   GET  /debug-uploads      - Verificar carpeta uploads")
    print("   GET  /debug-formulario/:id - Verificar formulario y foto")
    print("   GET  /limpiar-fotos      - Limpiar fotos huérfanas")
    app.run(host="0.0.0.0", port=5000, debug=True)