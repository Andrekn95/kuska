from pymongo import MongoClient
import os

# CAMBIO INCORPORADO: 
# Se reemplazó el '@' en el nombre de usuario de la URL por '%40' 
# para cumplir con el estándar RFC 3986 (Requerido por PyMongo).
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://kam.pilapanta%40yavirac.edu.ec:pilas652@kuska.eqrybhg.mongodb.net/?appName=kuska")

client = MongoClient(MONGO_URI)
db = client["kuska"]