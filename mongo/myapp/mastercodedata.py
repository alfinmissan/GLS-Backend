from bson import ObjectId
import re
from pymongo import MongoClient
client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema

def masterCodeId():
    try:
        data = list(db.master_code.find({}).sort('id',1).collation({"locale": "en_US", "numericOrdering": True}))
        print(data)
        leng = len(data)
        forid = data[leng-1]
        print(forid)
        master_id = forid['id']
        s = [int(s) for s in re.findall(r'-?\d+\.?\d*', master_id)]
        id = s[0] + 1
        return str(id)
    except:
        return 1


