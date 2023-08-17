from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema

def Query_generator(query):
    logic = query['condition']
    conditions = query['statement']['logic']
    statements = query['statement']['statements']
    condition = []
    Querys = []
    for statement in statements:
        con1 = None
        con2 = None
        for i in statement:
            if i['condition'] == 'is':
                if con1:
                    con2 = {i['category']: i['value']}
                else:
                    con1 = {i['category'] :i['value']}
            else:
                if con1:
                    con2 = {i['category'] :{"$ne" :i['value']}}
                else:
                    con1 = {i['category']: {"$ne": i['value']}}
            if con1 and con2:
                Querys.append([con1,con2])
    for i in range(len(conditions)):
        condition.append({"$ " +conditions[i] :Querys[i]})
    data = db.condition_query.insert_one(
        {
            "logic": conditions,
            "conditions" :condition
        }
    )
    return data.acknowledged

