import json
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from pymongo import MongoClient
from bson.json_util import dumps,ObjectId
from .serializers import InputLogSerializer,GridLogSerializer
from rest_framework.decorators import api_view
import datetime
from .userDetails import username
from .Id_generator import grid_log_id,logNo
from bson import json_util
from .mailgenerator import email
from django.core.mail import EmailMessage, get_connection
from django.conf import settings
from django.core.mail import send_mail
from .userDetails import username
client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema
module = openapi.Parameter('module', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING)
log_no = openapi.Parameter('log_no', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_INTEGER)
@swagger_auto_schema(method='get', manual_parameters=[module])
@swagger_auto_schema(method='delete', manual_parameters=[module,log_no])
@swagger_auto_schema(methods=['post'], request_body=InputLogSerializer)
@api_view(['GET','POST','DELETE'])
def Log_input_mudules(request):
    if request.method == 'GET':
        module = request.GET['module']
        try:
            data = list(db.log_input_module.find({"module":module}).sort("_id",-1))
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return Response(json_data)
        except:
            return Response(data = [])
    if request.method == 'POST':
        dateAndtime = {
            "date":'',
            "log_no":'',
            "time":''
        }
        module = request.data['module']
        log_no = logNo(module)
        dateAndtime['date'] = datetime.datetime.utcnow()
        dateAndtime['log_no'] = log_no
        query = request.data
        query.update(dateAndtime)
        data = db.log_input_module.insert_one(query)
        return Response(data=data.acknowledged,status=200)
    if request.method == 'DELETE':
        module = request.GET['module']
        log_no = request.GET['log_no']
        data = db.log_input_module.delete_one({"module":module,"log_no":int(log_no)})
        return Response(data=data.acknowledged)
module = openapi.Parameter('module', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING)
item = openapi.Parameter('item', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_INTEGER)
@swagger_auto_schema(methods=['post'], request_body=InputLogSerializer)
@api_view(['POST'])
def Log_input_mudules_reg(request):
    if request.method == 'POST':
        module = request.GET['module']
        item = request.GET['item']
        try:
            data = list(db.log_input_module.find({"module":module,"item":str(item)}).sort("_id",-1))
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return Response(json_data)
        except:
            return Response(data = ["test"])
@swagger_auto_schema(methods=['post'], request_body=InputLogSerializer)
@api_view(['POST'])
def blend_requirement_history(request):
    if request.method == 'POST':
        module = request.GET['module']
        blend = request.GET['blend']
        try:
            data = list(db.log_input_module.find({"module":module,"blend":str(blend)}).sort("_id",-1))
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return Response(json_data)
        except:
            return Response(data = ["test"])

varient = openapi.Parameter('varient', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING)
@swagger_auto_schema(method='get', manual_parameters=[varient])
@swagger_auto_schema(methods=['post'], request_body=GridLogSerializer)
@api_view(['GET','POST','DELETE'])
def log_grid_module(request):
    if request.method == 'POST':
        item = request.data['item']
        varient = request.data['varient']
        status = request.data['status']
        job = request.data['job']
        user = request.data['user']
        mail = ''
        Description=request.data['Description']
        factory =request.data['factory']
        type = request.data['type']
        try:
            approver= request.data['approver']
            if approver == 'Graphics Team' and status != 'Certified':
                status = 'Published'
        except:
            pass
        try:
            mail = request.data['email']
        except:
            pass

        data = list(db.myapp_customuser.find({"username":user}, {"_id": 0, 'user_group':1}))
        usergroup = request.data['user_group']
        update = db.log_grid_module.update_many({"varient":varient},{"$set":{"flag":0}})
        data = db.log_grid_module.insert_one({"user":user,"varient":varient,"item":item,"Description":Description,
                "date":datetime.datetime.today(),"status":status,"flag":1,"log":grid_log_id(varient)
                                        ,"type":type, "user_group":usergroup})
        history = db.grid_history.insert_one(
            {"user": user, "varient": varient,
             "date":datetime.datetime.utcnow(),
             "action": status, "V-no": 1})
        if usergroup =='Admin':
            if status == 'Modified' or status == 'Duplicated' or status == 'Created':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group":approver},{"_id":0,"email":1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.pending_task.delete_one({"item": item, "varient": varient})
                delete = db.completed_task.delete_one({"usergroup": approver, "varient": varient})
                completed = db.completed_task.insert_one({"item":item,"varient":varient,"user":user,"usergroup":usergroup,"date":datetime.datetime.today(),"status":status})
                pending = db.pending_task.insert_one({"item":item,"varient":varient,"user":user,"usergroup": approver,"date":datetime.datetime.today(),"status":status})
                setNotification({"user":user,"usergroupto":approver,"usergroupfrom":usergroup,"item":item,"job":job,"action":status,"varient":varient,"type":"grid"})
                subject = "Grid " +status+ " By "+ usergroup
                sales_report = False
                if approver == 'UK Sales':
                    salesreport = list(db.myapp_salesreport.find({"varient":varient}))
                    if len(salesreport)>0:
                        sales_report = "http://"+request.get_host()+"/media/"+salesreport[0]['file']
                message = {"varient":varient,"usergroup":usergroup,"status":status,"description":Description,"job":job,"item":item,"date":datetime.datetime.today(),"factory": factory,"report":sales_report,"message":mail}
                mail = email(message,subject,mail_ids)
            elif status == 'Published':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "Graphics Team"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.pending_task.delete_many({"item": item, "varient": varient})
                delete = db.completed_task.delete_many({"usergroup": "Admin", "varient": varient})
                pending = db.pending_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup":"Graphics Team", "date": datetime.datetime.today(),"status": status})
                completed = db.completed_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": usergroup,"date": datetime.datetime.today(), "status": status})
                setNotification({"user": user, "usergroupfrom": usergroup,"usergroupto":"Graphics Team","item":item,"job":job,"action": status, "varient": varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
            elif status == 'Certified':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "Admin"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.completed_task.delete_many({"varient": varient})
                delete = db.pending_task.delete_many({"item": item, "varient": varient})
                completed = db.completed_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup":usergroup, "date": datetime.datetime.today(),"status": status,"type":status})
                pending = db.pending_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": "Admin", "date": datetime.datetime.today(), "status": status})
                setNotification({"user": user, "usergroupto": "Admin","usergroupfrom":usergroup,"item":item,"job":job, "action": status, "varient": varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
            elif status == 'Artwork Completed':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "Admin"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.completed_task.delete_many({"usergroup": "Admin", "varient": varient})
                delete = db.pending_task.delete_many({"usergroup": "Admin", "varient": varient})
                completed = db.completed_task.insert_one(
                    {"item": item, "varient": varient, "user": user, "usergroup": usergroup,
                     "date": datetime.datetime.today(), "status": status})
                setNotification(
                    {"user": user, "usergroupto": "Admin", "usergroupfrom": usergroup, "item": item, "job": job,
                     "action": status, "varient": varient, "type": "grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)

        elif usergroup =="UK Sales":
            if status == 'Approved':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group":"Language Approver"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                completed = db.completed_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": usergroup, "date": datetime.datetime.today(),"status": status})
                pending = db.pending_task.update_one({"item": item, "varient": varient},{"$set":{"user": user, "usergroup":"Language Approver", "date": datetime.datetime.today(),"status":status}})
                setNotification({"user": user, "usergroupto": "Language Approver","usergroupfrom":usergroup,"item":item,"job":job, "action": status, "varient": varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
            elif status == 'Rejected':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "Admin"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.completed_task.delete_many({"item": item, "varient": varient})
                completed = db.completed_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": usergroup, "date":datetime.datetime.today(),"status": status})
                pending = db.pending_task.update_one({"item": item, "varient": varient},{"$set": {"user": user, "usergroup": "Admin", "date": datetime.datetime.today(),"status":status}})
                setNotification({"user": user, "usergroupto":"Admin","usergroupfrom":usergroup,"item":item,"job":job, "action": status, "varient": varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
        elif usergroup == "Language Approver":
            if status == 'Approved':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "Admin"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.completed_task.delete_many({"usergroup": "Admin", "varient": varient})
                completed = db.completed_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": usergroup, "date": datetime.datetime.today(),"status": status})
                pending = db.pending_task.update_one({"item": item, "varient": varient},{"$set": {"user": user, "usergroup": "Admin", "date": datetime.datetime.today(),"status":status}})
                # pending = db.pending_task.update_one({"item": item, "varient": varient}, {"$set": {"user": user, "usergroup": "Editor", "date": datetime.datetime.today(), "status": status}})
                setNotification({"user": user, "usergroupto":  "Admin","usergroupfrom":usergroup,"item":item,"job":job, "action": status, "varient": varient,"type":"grid"})
                setNotification({"user": user, "usergroupto": "Editor", "usergroupfrom": usergroup,"item":item,"job":job, "action": status,"varient": varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
            if status == 'Rejected':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "Admin"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.completed_task.delete_many({"usergroup": "Admin", "varient": varient})
                completed = db.completed_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": usergroup, "date":datetime.datetime.today(),"status": status})
                pending = db.pending_task.update_one({"item": item, "varient": varient}, {"$set": {"user": user, "usergroup": "Admin", "date": datetime.datetime.today(), "status": status}})
                setNotification({"user": user, "usergroupto":"Admin","usergroupfrom":usergroup,"item":item,"job":job, "action": status, "varient": varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
        if usergroup == 'Editor':
            if status == 'Modified' or status == 'Duplicated':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "UK Sales"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.pending_task.delete_many({"item": item, "varient": varient})
                delete = db.completed_task.delete_many({"usergroup": "UK Sales", "varient": varient})
                completed = db.completed_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": usergroup,"date": datetime.datetime.today(), "status": status})
                pending = db.pending_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup":"UK Sales","date": datetime.datetime.today(), "status": status})
                setNotification({"user": user, "usergroupto":"UK Sales","usergroupfrom":usergroup,"item":item,"job":job, "action": status, "varient": varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
            elif status == 'Published':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "Graphics Team"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.completed_task.delete_many({"usergroup": "Admin", "varient": varient})
                delete = db.pending_task.delete_many({"usergroup": "Admin", "varient": varient})
                completed = db.completed_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": usergroup,"date": datetime.datetime.today(), "status": status})
                pending = db.pending_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": "Graphics Team","date": datetime.datetime.today(), "status": status})
                setNotification({"user": user, "usergroupto":"Admin","usergroupfrom":usergroup,"item":item,"job":job, "action": status, "varient": varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
            elif status == 'Certified':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "Admin"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.completed_task.delete_many({"usergroup": "Admin", "varient": varient})
                delete = db.pending_task.delete_many({"usergroup": "Admin", "varient": varient})
                completed = db.completed_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": usergroup,"date": datetime.datetime.today(), "status": status})
                pending = db.pending_task.insert_one(
                    {"item": item, "varient": varient, "user": user, "usergroup": "Admin",
                     "date": datetime.datetime.today(), "status": status})
                setNotification({"user": user, "usergroupto":"Admin","usergroupfrom":usergroup,"item":item,"job":job, "action": status, "varient": varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
            elif status == 'Artwork Completed':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "Admin"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.completed_task.delete_many({"usergroup": "Admin", "varient": varient})
                delete = db.pending_task.delete_many({"usergroup": "Admin", "varient": varient})
                completed = db.completed_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": usergroup,"date": datetime.datetime.today(), "status": status})
                setNotification({"user": user, "usergroupto":"Admin","usergroupfrom":usergroup,"item":item,"job":job, "action": status, "varient": varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
        if usergroup == 'Graphics Team':
            if status == 'Acknowledged':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "Admin"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.pending_task.delete_many({"item": item, "varient": varient})
                delete = db.completed_task.delete_many({"usergroup": "Graphics Team", "varient": varient})
                # completed = db.completed_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup": usergroup,"date": datetime.datetime.today(), "status": status})
                pending = db.pending_task.insert_one({"item": item, "varient": varient, "user": user, "usergroup":"Graphics Team","date": datetime.datetime.today(), "status": status})
                setNotification({"user": user, "usergroupto":"Admin","usergroupfrom":usergroup,"item":item,"job":job, "action": status, "varient": varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
            elif status == 'Design Completed':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group": "Admin"}, {"_id": 0, "email": 1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.pending_task.delete_many({"item": item, "varient": varient})
                delete = db.completed_task.delete_many({"usergroup": "Graphics Team", "varient": varient})
                completed = db.completed_task.insert_one(
                    {"item": item, "varient": varient, "user": user, "usergroup": usergroup,
                     "date": datetime.datetime.today(), "status": status})
                pending = db.pending_task.insert_one(
                    {"item": item, "varient": varient, "user": user, "usergroup": "Admin",
                     "date": datetime.datetime.today(), "status": status})
                setNotification(
                    {"user": user, "usergroupto": "Admin", "usergroupfrom": usergroup, "item": item, "job": job,
                     "action": status, "varient": varient, "type": "grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
        return Response(data=data.acknowledged,status=200)

    if request.method == 'GET':
        varient = request.GET['varient']
        data = db.log_grid_module.find({"varient":varient})
        js_data = dumps(data, indent=1)
        with open('data.json', 'w') as file:
            file.write(js_data)
        json_data = json.loads(js_data)
        return Response(data=json_data)
    if request.method == 'DELETE':
        module = request.GET['module']
        log_no = request.GET['log_no']
        data = db.log_input_module.delete_one({"module":module,"log_no":int(log_no)})
        return Response(data=data.acknowledged)


user_group = openapi.Parameter('user_group', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING)
@swagger_auto_schema(method='get', manual_parameters=[user_group])
@swagger_auto_schema(method='post', manual_parameters=[user_group])
@api_view(['GET','POST'])
def task_view(request):
    if request.method == 'GET':
        user = request.GET['user_group']
        if user == 'Admin' or 'Editor' == user:
            data = list(db.pending_task.find({"$or":[{"usergroup": 'Admin'},{"usergroup": 'Editor'}]}))
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return Response(data=json_data)
        else:
            data = list(db.pending_task.find({"usergroup": user}))
            js = json.dumps(data, default=json_util.default)
            json_data = json.loads(js)
            return Response(data=json_data)
    if request.method == 'POST':
        usergroup = request.GET['user_group']
        data = list(db.completed_task.find({"usergroup":usergroup}).sort("date",-1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)




def log_input(request,module):
        dateAndtime = {
            "date":'',
            "log_no":'',
            "time":''
        }
        module = module
        log_no = logNo(module)
        dateAndtime['date'] =datetime.datetime.utcnow()
        dateAndtime['log_no'] = log_no
        query = request
        query.update(dateAndtime)
        data = db.log_input_module.insert_one(query)
        return Response(data=data.acknowledged,status=200)

varient = openapi.Parameter('varient', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING)
@swagger_auto_schema(method='get', manual_parameters=[varient])
@api_view(['GET'])
def GridFlowInformation(request):
    if request.method == 'GET':
        data = list(db.log_grid_module.find({"varient":request.GET['varient']}))
        date1 = False
        date2 = ''
        duration = False
        myList = []
        for i in data:
            date2 = i['date']
            status = i['status']
            user_group = i['user_group']
            if date1:
                date = date2 - date1
                duration = date.days
            mydict = {"status":status,"date":i['date'],"duration":duration,"user_group":user_group}
            myList.append(mydict)
            date1 = date2
        js = json.dumps(myList, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)

def setNotification(dict):
    dele = db.notification.delete_many({"user_group_to":dict['usergroupto'],"varient":dict['varient']})
    dele = db.notification.delete_many({"user_group_to": dict['usergroupfrom'], "varient": dict['varient']})
    data = db.notification.insert_one({"user_group_from":dict['usergroupfrom'],"user_group_to":dict['usergroupto'],"action":dict['action'],
                                       "date":datetime.datetime.now(),"user":dict['user'],"item":dict['item'],"job":dict['job'],"varient":dict['varient'],"type":dict['type']})
    try:
        noti = db.notificationCount.update({"usergroup":dict['usergroupto']},{"$inc":{"count":1}})
        if noti.nMatched ==0 :
            noti = db.notificationCount.insert({"usergroup": dict['usergroupto'], "count": 1})
    except:
        noti = db.notificationCount.insert({"usergroup":dict['usergroupto'],"count": 1})
    if data.acknowledged == True:
        return True
    else:
        return False

user_group = openapi.Parameter('user_group', openapi.IN_QUERY, description=" manual param", type=openapi.TYPE_STRING)
type= openapi.Parameter('type', openapi.IN_QUERY, description=" manual param", type=openapi.TYPE_STRING)
@swagger_auto_schema(method='get', manual_parameters=[user_group,type])
@swagger_auto_schema(method='post', manual_parameters=[user_group])
@swagger_auto_schema(method='delete', manual_parameters=[user_group])
@api_view(['GET','POST','DELETE'])
def ViewNotification(request):
    if request.method == 'GET':
        user = username(request.auth)
        user_group = user['user_group']
        if user_group == "Editor":
            user_group = 'Admin'
        myList = []
        pipeline = [
            {
                "$match": {
                    "$and": [
                        {"user_group_to":user_group},
                        {"type": "grid"}
                    ]
                }
            },
            {
                "$lookup": {
                    "from": "pending_task",
                    "let": {
                        "varient_value": "$varient",
                        "user_group_value": "$user_group_to"
                    },
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$varient", "$$varient_value"]},
                                        {"$eq": ["$usergroup", "$$user_group_value"]}
                                    ]
                                }
                            }
                        },
                        {
                            "$count": "matched_count"
                        }
                    ],
                    "as": "matched_documents"
                }
            },
            {
                "$addFields": {
                    "matched_count": {"$arrayElemAt": ["$matched_documents.matched_count", 0]}
                }
            },
            {
                "$lookup": {
                    "from": "completed_task",
                    "let": {
                        "varient_value": "$varient",
                        "user_group_value": "$user_group_to"
                    },
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$varient", "$$varient_value"]},
                                        {"$eq": ["$usergroup", "$$user_group_value"]}
                                    ]
                                }
                            }
                        },
                        {
                            "$count": "completed_count"
                        }
                    ],
                    "as": "completed_documents"
                }
            },
            {
                "$addFields": {
                    "completed_count": {"$arrayElemAt": ["$completed_documents.completed_count", 0]}
                }
            },
            {
                "$match": {
                    "$or": [
                        {"matched_count": {"$gt": 0}},
                        {"completed_count": {"$gt": 0}}
                    ]
                }
            },
            {
                "$sort": {
                    "date": -1
                }
            },
            {
                "$group": {
                    "_id": {
                        "field1": "$job",
                        "field2": "$user_group_to"
                    },
                    "documents": {"$push": "$$ROOT"},
                    "count": {"$sum": 1},
                    "total_matched_count": {"$sum": "$matched_count"},
                    "total_completed_count": {"$sum": "$completed_count"}
                }
            },
            {
                "$match": {
                    "count": {"$gte": 1}
                }
            }
        ]
        result = list(db.notification.aggregate(pipeline))
        js = json.dumps(result, default=json_util.default)
        json_data = json.loads(js)
        count = 0
        pipeline = [
                {
                    "$match": {
                        "$and": [
                            {"receiver": str(user['id'])},
                            {"type": "chat"}
                        ]
                    }
                },
                {
                    "$sort": {
                        "date": -1
                    }
                },
                ];

        chat_result = list(db.notification.aggregate(pipeline))
        for i in chat_result:
            if db.pending_task.find({"varient":i['varient'],"usergroup":user_group}).count() > 0:
                data = list(db.pending_task.find({"varient":i['varient'],"usergroup":user_group}))
                mydict = {"varient":i['varient'],'item':data[0]['item'],"date":i['date'],"pending":True,"status":data[0]['status']}
                myList.append(mydict)
                count += 1
            elif db.completed_task.find({"varient":i['varient'],"usergroup":user_group}).count() > 0:
                data = list(db.completed_task.find({"varient": i['varient'],"usergroup":user_group}))
                mydict = {"varient":i['varient'],'item':data[0]['item'],"date":i['date'],"pending":False,"status":data[0]['status']}
                myList.append(mydict)
                count += 1
            else:
                pass
        js = json.dumps(myList, default=json_util.default)
        chat_data = json.loads(js)
        return Response(data={"grid": json_data,"chat":chat_data,"count":count})
    if request.method == 'POST':
        data = list(db.notificationCount.find({"usergroup":request.GET['user_group']}))
        try:
            count = data[0]['count']
            return  Response(data=count)
        except:
            count = False
            return Response(data=count)


    if request.method == 'DELETE':
       data = db.notificationCount.update({"usergroup":request.GET['user_group']},{"$set":{"count":0}})
       try:
            return Response(data=data.acknowledged)
       except:return Response(data=False)


varient= openapi.Parameter('varient', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(method='POST', manual_parameters=[varient])
@api_view(['POST'])
def gridvarientCheck(request):
    if request.method == 'POST':
        if db.grids.find({"varient":request.GET['varient']}).count() > 0:
            return Response(data="version already exist",status=200)
        return Response(data="not exist",status=203)

varient = openapi.Parameter('varient', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING)
@swagger_auto_schema(method='get', manual_parameters=[varient])
@swagger_auto_schema(methods=['post'], request_body=GridLogSerializer)
@api_view(['GET','POST','DELETE'])
def grid_duplicate_logs(request):
    if request.method == 'POST':
        item = request.data['item']
        varient = request.data['varient']
        status = request.data['status']
        user = request.data['user']
        job = request.data['job']
        Description = request.data['Description']
        factory = request.data['factory']
        user_group = request.data['approver']
        type = request.data['type']
        mail = request.data['email']
        data = list(db.myapp_customuser.find({"username":user}, {"_id": 0, 'user_group':1}))
        usergroup = request.data['user_group']
        update = db.log_grid_module.update_many({"varient":varient},{"$set":{"flag":0}})
        data = db.log_grid_module.insert_one({"user":user,"varient":varient,"item":item,"Description":Description,
                "date":datetime.datetime.utcnow(),"status":status,"flag":1,"log":grid_log_id(varient)
                                        ,"type":type, "user_group":usergroup})

        history = db.grid_history.insert_one({"user": user, "varient": varient,"date":datetime.datetime.utcnow(), "action": status, "V-no": 1})
        if user_group == 'Graphics Team':
            status = 'Published'
        if usergroup =='Admin' or usergroup == 'Editor':
            if status =='Duplicated' or  status == 'Published':
                mail_ids = []
                users = db.myapp_customuser.find({"user_group":user_group},{"_id":0,"email":1})
                for i in users:
                    mail_ids.append(i['email'])
                delete = db.pending_task.delete_one({"item": item, "varient": varient})
                delete = db.completed_task.delete_one({"usergroup": user_group , "varient": varient})
                completed = db.completed_task.insert_one({"item":item,"varient":varient,"user":user,"usergroup":usergroup,"date":datetime.datetime.today(),"status":status})
                pending = db.pending_task.insert_one({"item":item,"varient":varient,"user":user,"usergroup":user_group ,"date":datetime.datetime.today(),"status":status})
                setNotification({"user":user,"usergroupto":user_group,"usergroupfrom":usergroup,"item":item,"job":job,"action":status,"varient":varient,"type":"grid"})
                message = {"varient": varient, "usergroup": usergroup, "status": status, "description": Description,
                           "job": job, "item": item, "date": datetime.datetime.today(), "factory": factory,"message":mail}
                subject = "Grid " + status + " By " + usergroup
                mail = email(message, subject, mail_ids)
        return Response(data=data.acknowledged,status=201)

def get_link(group,status,approver,varient):
    if status == 'Created' or status == 'Modified' or status == 'Duplicated':
        return "http://localhost:3000/tasklist/grid/"+varient
    if status == 'Published':
        return "http://localhost:3000/grph/tasklist/grid/" + status



