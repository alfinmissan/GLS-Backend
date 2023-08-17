from pymongo import MongoClient

client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema

def textTranslation(req):
    data =list(db.translations.aggregate([
        { "$match": {"translation.master_id":str(req) }},
        { "$unwind": '$translation'},
        { "$match": {'translation.master_id': str(req)}},
        { "$group": {"_id": '$language',"translation": {"$push": '$translation'}}},
        {
            "$project": {
                "language": "$_id",
                "version": "$translation",
                "_id":0
            }
        }
        ]))
    translations = []
    for i in data:
        language = i['language']
        for j in i['version']:
            translation_ID = j['trans_id']
            for k in j['versions']:
                if k['currentVersion'] == True:
                    translation = k['trans']
                    version = k['version']
                    trans = {"translation":translation,"translation_ID":translation_ID,"language":language,"version":version}
                    translations.append(trans)
    return translations