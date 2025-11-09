from pymongo import MongoClient
from config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.MONGO_DB_NAME]
news_collection = db["articles"]