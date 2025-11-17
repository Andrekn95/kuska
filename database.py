from pymongo import MongoClient
import os

# Lee la clave MONGO_URI de las variables de entorno (Render la inyectará)
MONGO_URI = os.environ.get('MONGO_URI') 

if MONGO_URI is None:
    # Si no encuentra la variable, lanza un error (solo ocurriría si Render falla)
    raise Exception("La variable MONGO_URI no está configurada. Verifica el panel de Render.")

# Ahora usa la URI para conectarte
client = MongoClient(MONGO_URI)
db = client['el_nombre_de_tu_db'] # ¡Asegúrate de poner el nombre de tu base de datos aquí!

# Si usas Blueprints o si el código continúa en app.py, asegúrate de que use 'client' o 'db'