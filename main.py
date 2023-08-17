from pymongo import MongoClient


client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema

data = db.log_input_module.delete_many({"module":"ingredient"})
teaOrigin = db.master_code.find({"id": "826"}).count()
print(teaOrigin)

grid = list(db.grids.find({"varient":"111"}))