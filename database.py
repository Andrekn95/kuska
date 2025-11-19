from pymongo import MongoClient

MONGO_URI = "mongodb+srv://kuska:12345@kuska.eqrybhg.mongodb.net/?retryWrites=true&w=majority&appName=kuska"

client = MongoClient(MONGO_URI)

db = client["kuska"]  # nombre de la base de datos
