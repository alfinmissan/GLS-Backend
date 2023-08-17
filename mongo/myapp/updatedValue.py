from pymongo import MongoClient
from bson.json_util import dumps,ObjectId

client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema

def get_updated_values(request):
    query = request['query']
    update_result = request['result']
    collection = request['collection']
    if update_result.modified_count > 0:
        updated_document = db[collection].find_one(query)
        modified_fields = update_result.raw_result.get("updatedExisting", False)
        if modified_fields:
            for field in query["$set"]:
                if field in updated_document:
                    print(f"Field '{field}' updated. New value: {updated_document[field]}")