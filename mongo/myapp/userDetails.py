from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import pandas as pd
from json import dumps
from pymongo import MongoClient

client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema

def username(auth_token):
    token = auth_token
    try:
        user_id = list(db.authtoken_token.find({"key":str(token)}))
        user = list(db.myapp_customuser.find({"id":user_id[0]['user_id']}))
        user_group = user[0]['user_group']
        id = user[0]['id']
        name = user[0]['first_name']+ ' '+user[0]['last_name']
        message = {"name": name, "user_group": user_group,"id":id}
        return message
    except Exception as e:
        status = 404
        return e

def AuthorizeAdmin(auth_token):
    token = auth_token
    try:
        user_id = list(db.authtoken_token.find({"key": str(token)}))
        user = list(db.myapp_customuser.find({"id": user_id[0]['user_id']}))
        user_group = user[0]['user_group']
        if user_group == 'Admin':
            return True
        else:
            return False
    except Exception as e:
        status = 404
        return e

def AuthorizeUser(auth_token):
    token = auth_token
    try:
        user_id = list(db.authtoken_token.find({"key": str(token)}))
        if db.myapp_customuser.find({"id": user_id[0]['user_id']}).count() > 0:
            return True
        else:
            return False
    except Exception as e:
        status = 404
        return e


def update_requirement_order():
    documents = db.additional_requirement.find().sort("order", 1)

    # Update the order field with the updated ascending values
    new_order = 1
    for document in documents:
        db.additional_requirement.update_one(
            {"_id": document["_id"]},
            {"$set": {"order": new_order}}
        )
        new_order += 1