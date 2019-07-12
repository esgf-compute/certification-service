import pymongo

client = pymongo.MongoClient('mongodb://127.0.0.1:27017/')

db = client['certification']

db.servers.create_index('url', unique=True)
