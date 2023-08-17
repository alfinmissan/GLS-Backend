from bson.json_util import dumps,ObjectId
from pymongo import MongoClient

client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema

def deleteLanguage(request):
    objId = request['id']
    objectId = []
    for i in objId:
        ob = ObjectId(i)
        objectId.append(ob)
    print(objectId)
    return objectId