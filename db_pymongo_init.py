# Creates requests collection and fills it with the data from the local json file.

import json
from pymongo import MongoClient
from model_worker import DB_URI, DB_NAME, REQUESTS_COLLECTION

JSON_DATA_FILE = "db_init_content.json" # Local file with records, to generate use db_pymogo_json_gen.py

client = MongoClient(DB_URI)
db = client[DB_NAME]
collection = db[REQUESTS_COLLECTION]

print("Working with the following collection: ", collection)

if collection.count_documents({}):
    print("Collection already has data in it.")
else:
    with open(JSON_DATA_FILE) as file:
      init_data = json.load(file)
    collection.insert_many(init_data)
    print("Data from ", JSON_DATA_FILE, " added successfully.")

