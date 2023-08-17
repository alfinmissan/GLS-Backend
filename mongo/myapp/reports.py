from django.utils.datastructures import MultiValueDictKeyError
from pymongo import MongoClient
from dateutil import parser
import json
from bson import json_util

client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema

def viewerReport(request):
    try:
        varient = request.GET['varient']
    except MultiValueDictKeyError:
        varient = ''
    try:
        item = request.GET['item']
    except MultiValueDictKeyError:
        item = ''
    try:
        fromdate = request.GET['from']
    except MultiValueDictKeyError:
        fromdate = ''
    try:
        todate = request.GET['to']
    except MultiValueDictKeyError:
        todate = ''

    if item and varient:
        data = list(db.log_grid_module.find({"$and": [{"flag": 1}, {"varient": varient}, {'item': item},
                                                      {"type":"Certified"}]}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data

    elif varient:
        data = list(db.log_grid_module.find({"$and": [{"flag": 1}, {"varient": varient}, {"type":"Certified"}]}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    elif item:
        data = list(db.log_grid_module.find({"$and":[{"flag":1},{"item":str(item)}, {"type":"Certified"}]}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data

    elif fromdate and todate:
        date1 = parser.parse(fromdate)
        date2 = parser.parse(todate)
        data = list(db.log_grid_module.find(
        {"$and": [{"flag": 1}, {"type":"Certified"}, {"date": {"$gte":date1, "$lte":date2}}]}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    else:
        data = []
        return data

def Report(request):
    try:
        varient = request.GET['varient']
        if varient == '':
            varient = False
    except:
        varient = False
    try:
        item = request.GET['item']
        if item == '':
            item = False
    except:
        item = False
    try:
        fromdate = request.GET['from']
    except:
        fromdate = False
    try:
        todate = request.GET['to']
    except:
        todate = False
    try:
        type = request.GET['type']
        if type == '':
            type = False
    except:
        type = False
    try:
        status = request.GET['status']
        if status == '':
            status = False
    except:
        status = False
    try:
        usergroup = request.GET['usergroup']
        if usergroup == '':
            usergroup = False
    except:
        usergroup = False
    print(fromdate)
    print(todate)
    print(usergroup)
    print(varient)
    print(item)
    print(status)
    print(type)
    if item and varient:
        data = list(db.log_grid_module.find({"$and":[{"flag": 1}, {"varient": str(varient)},{'item':item}]}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    elif varient:
        data = list(db.log_grid_module.find({"flag": 1,"varient":str(varient)}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    elif item:
        data = list(db.log_grid_module.find({"flag": 1, "item": item}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    elif fromdate and todate and status:
        date1 = parser.parse(fromdate)
        date2 = parser.parse(todate)
        data = list(db.log_grid_module.find({"$and": [{"status":status},{"flag": 1}, {"date": {"$gte": date1, "$lte": date2 }}]}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    elif usergroup:
        data = list(db.log_grid_module.find(
            {"user_group": usergroup,"flag": 1}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    elif type and status:
        data = list(db.log_grid_module.find({"flag": 1, "status":status,"type":type}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    elif type and fromdate and todate:
        date1 = parser.parse(fromdate)
        date2 = parser.parse(todate)
        data = list(db.log_grid_module.find({"$and": [{"type":type},{"flag": 1}, {"date": {"$gte": date1, "$lte": date2 }}]}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    elif type:
        data =list(db.log_grid_module.find({"flag": 1, "type":type}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    elif status:
        data = list(db.log_grid_module.find({"flag": 1, "status": status}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    elif fromdate and todate:
        date1 = parser.parse(fromdate)
        date2 = parser.parse(todate)
        print(fromdate,todate)
        data = list(db.log_grid_module.find(
            {"$and": [{"flag": 1},{"date": {"$gte": date1, "$lte": date2}}]}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return json_data
    else:
        data = []
        return data
def dashboard():
    pending = list(db.pending_task.find())
    complete = list(db.completed_task.find())
    return [len(pending),len(complete),len(pending)+len(complete)]

def CountryData():
    country = []
    data = list(db.country.find())
    for i in data:
        names = []
        try:
            for j in i['language']:
                # print(j)
                lan = list(db.language.find({"code": j}, {"_id": 0, "code": 1}))
                try:
                    names.append(lan[0]['code'])
                except:
                    pass
                i['language'] = names
        except KeyError:
            i['language'] = []
        country.append(i)
    return country

def serach_task(request):
    try:
        table = request.GET['table']
    except MultiValueDictKeyError:
        table = False
    try:
        user_group = request.GET['usergroup']
    except MultiValueDictKeyError:
        user_group = False
    try:
        varient = request.GET['varient']
    except MultiValueDictKeyError:
        varient = False
    try:
        item = request.GET['item']
    except MultiValueDictKeyError:
        item = False
    try:
        from_dt = request.GET['fromdate']
        to_dt    = request.GET['todate']
    except MultiValueDictKeyError:
        from_dt = False
        to_dt = False
    if table == 'pending':
        if item and varient:
            data = list(db.pending_task.find({"$and": [{"usergroup":user_group}, {"varient": str(varient)}, {'item': item}]}).sort("date",-1))
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return json_data
        elif varient:
            data = list(db.pending_task.find({"usergroup":user_group, "varient": str(varient)}).sort("date",-1))
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return json_data
        elif item:
            data = list(db.pending_task.find({"usergroup":user_group,"item": item}).sort("date",-1))
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return json_data
        elif from_dt and to_dt:
            date1 = parser.parse(from_dt)
            date2 = parser.parse(to_dt)
            data = list(db.pending_task.find(
                {"$and": [{"date": {"$gte": date1, "$lte": date2}}]}).sort("date",-1))
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return json_data
        else:
            data = []
            return data

    elif table == 'completed':
        if item and varient:
            print("test")
            data = list(
                db.completed_task.find({"$and": [{"usergroup": user_group}, {"varient": str(varient)}, {'item': item}]}).sort("date",-1))
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return json_data
        elif varient:
            data = list(db.completed_task.find({"usergroup": user_group, "varient": str(varient)}).sort("date",-1))
            print(data,"test")
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return json_data
        elif item:
            data = list(db.completed_task.find({"usergroup": user_group, "item": item}).sort("date",-1))
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return json_data
        elif from_dt and to_dt:
            date1 = parser.parse(from_dt)
            date2 = parser.parse(to_dt)
            data = list(db.completed_task.find(
               {"usergroup": user_group,"date": {"$gte": date1, "$lte": date2}}).sort("date",-1))
            print(data)
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return json_data
        else:
            data = []
            return data


