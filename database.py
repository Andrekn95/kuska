from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI", "TU_URL_MONGO_AQUI")

client = MongoClient(MONGO_URI)
db = client["kuska"]