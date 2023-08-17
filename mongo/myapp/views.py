import json
from drf_yasg import openapi
from django.views import View
from rest_framework.decorators import authentication_classes, permission_classes
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status,parsers
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import viewsets, renderers
from pymongo import MongoClient
from bson.json_util import dumps,ObjectId
from .models import CustomUser, Asset, Fonts,excelImport
from .models import Attachment,Document
from .gridview import Gridgenerator,make_duplicate_empty
from .mailgenerator import email
from .mastercodedata import masterCodeId
from .Id_generator import translationId, transVersionId, \
    versionId,subtranslation_id,transVersion,GridVersion
from .serializers import UserSerialiser, TranslationSerializers, DocumentSerializer,\
    TranslationUpdateSerializer, AssetSerializer, GridDuplicateSerilaizer, AttachmentSerializer
from .serializers import LanguageSerializer,CountrySerializer,CountryUpdateSerializer,\
    LegalNameSerializer,LegalNameUpdateSerializer,LegalNameImportExcelSerializer,ChatSerializer
from .serializers import BlendSerializer,BlendUpdateSerializer,IngredientSerializer,\
    IngredientUpdateSerializer,GridVersionAddSerializer,BlendDeleteSerializer,SaveGridSerializer
from .serializers import FactorySerializer,FactoryUpdateSerializer,RequirementSerializers,\
    GridSerializer,RequirementUpdateSerializers,LanguageUpdateSerializer,DeleteRequirementsSerializer
from rest_framework.decorators import api_view,parser_classes
from .serializers import CustomCondtionSerializer,FontSerializer,\
    DeleteAssetSerializer,DeleteCountryRequirementSerializer,IngredientDeleteSerializer,\
    BlendImportExcelSerializer,CountryRequirementSerializers
from .userDetails import username
from .custom_querygenerator import Query_generator
from .mailgenerator import user_registered_mail
import datetime
from rest_framework.views import APIView
from bson import json_util
from .deleteData import deleteLanguage
from .Id_generator import grid_log_id,logNo
from .excel import importExcel,LanaguaugeExport,TranslationExport
from .excel import ImportTranslation
from .logs import log_input
from django.db.models import Q
from django.utils import timezone
import re
# database connection
client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema


# adding user
@authentication_classes([])
@permission_classes([])
class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerialiser
    def create(self,request):
        serializer_class = UserSerialiser(data=request.data)
        print(request.data['password'])
        if serializer_class.is_valid():
            serializer_class.save()
            subject = " User Registration Successfull - GLS"
            msg= {"username":request.data['username'],"password":request.data['password']}
            try:
                mail = user_registered_mail(msg,subject,[request.data['email']])
            except:
                pass
            return Response(data='user registered' ,status=200)
        else:
            return Response(data = serializer_class.errors,status=400)


class AssetViewSet(viewsets.ModelViewSet):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    def create(self,request):
        Date = datetime.datetime.today()
        time = datetime.datetime.now().time()
        log_no = logNo("asset")
        name = username(request.auth)
        serializer = AssetSerializer(data = request.data)
        if serializer.is_valid():
            if db.myapp_asset.find({'name':request.POST['name']}).count() > 0:
                return Response(data={"message":"name already exist"},status=200)
            else:
                asset = Asset.objects.create(
                    name=request.POST['name'],
                    type=request.POST['type'],
                    photo=request.FILES['photo'],
                    )
                data = db.log_input_module.insert_one(
                    {"user": name['name'], "action": "added new asset " + request.POST['name'],
                     "module": "asset", "date":datetime.datetime.utcnow(), "log_no": log_no})
            return Response(serializer.data, status=204)
        else:
            return Response(serializer.errors, status=400)


@swagger_auto_schema(methods=['delete'], request_body=DeleteAssetSerializer)
@api_view(['DELETE'])
def deleteAsset(request):
    Date = datetime.datetime.today()
    name = username(request.auth)
    log_no = logNo("asset")
    if request.method == 'DELETE':
        assets = []
        asset = list(db.myapp_asset.find({"id":{"$in":request.data['id']}}))
        for i in asset:
            req = db.additional_requirement.find({"value":i['id']}).count()
            if req > 0:
                assets.append(i['id'])
            else:pass
        if len(assets) > 0:
            names = []
            asset_name = list(db.myapp_asset.find({"id": {"$in":assets}},{"_id":0,"name":1}))
            for i in asset_name:
                name = i['name']
                names.append(name)
            return Response(data=names,status=201)
        else:
            for i in asset:
                data = db.myapp_asset.delete_many({"id":i['id']})
                log = db.log_input_module.insert_one(
                    {"user": name['name'], "action": "deleted " + i['name'],
                    "module": "asset", "date":datetime.datetime.utcnow(), "log_no": log_no})
            if data.acknowledged:
                return Response(data={"message":"Asset deleted"}, status=200)
            return Response(data={"message": "Asset not deleted"}, status=200)




#api for get update delete and add translations
language = openapi.Parameter('language', openapi.IN_QUERY,type=openapi.TYPE_STRING)
tran_ids = openapi.Parameter('tran_ids', openapi.IN_QUERY,type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['post'], request_body=TranslationSerializers)
@swagger_auto_schema(methods=['put'], request_body=TranslationUpdateSerializer)
@swagger_auto_schema(methods=['delete'], manual_parameters=[language,tran_ids])
@swagger_auto_schema(methods=['get'], manual_parameters=[language])
@api_view(['GET','POST','PUT','DELETE'])
def addUpdateDelTranslations(request):
    name = username(request.auth)
    Date = datetime.datetime.today()
    time = datetime.datetime.now().time()
    log_no = logNo("translation")
    if request.method == 'GET':
        language = request.GET.get('language')
        translations = []

        pipeline = [
            {"$match": {"language": language}},
            {"$unwind": "$translation"},
            {"$sort": {"translation.trans_id": 1}},
            {"$group": {
                "_id": "$_id",
                "language": {"$first": "$language"},
                "translation": {"$push": "$translation"}
            }},
        ]

        data = list(db.translations.aggregate(pipeline, collation={"locale": "en_US", "numericOrdering": True}))

        try:
            for item in data:
                translation_list = item['translation']

                for translation in translation_list:
                    text = translation['text']
                    trans_id = translation['trans_id']
                    master_id = translation['master_id']

                    for versions in translation['versions']:
                        if versions['currentVersion']:
                            version = versions['version']
                            trans = versions['trans']
                            break

                    row_data = {"text": text,"version":version, "trans": trans, "trans_id": trans_id, "master_id": master_id}
                    translations.append(row_data)

            js = json.dumps(translations, default=json_util.default)
            json_data = json.loads(js)

            return Response(data=json_data)

        except:
            return Response(status=400)
    elif request.method == 'POST':
        try:
            serializer = TranslationSerializers(data=request.data)
            if serializer.is_valid():
                if db.translations.find({"translation.trans_id":request.data['tran_id']}).count() > 0:
                    return Response(data={"message":"Tranlation already present"},status=200)
                data = db.translations.find({"language":request.data['language']})
                lan = request.data['language']
                for i in data:
                    if i['language'] == request.data['language']:
                        db.translations.update_one({"language": request.data['language']},
                                                   {"$push": {"translation":{"text":request.data['text'],
                                                    "versions":[{"trans":request.data['trans'],"version":1,"currentVersion":True}],
                                                            "master_id":request.data['master_id'],"trans_id":request.data['tran_id']}}})
                        data = db.log_input_module.insert_one({"user": name['name'], "action": "added new translation for " + request.data['text'] +" in language "+ request.data['language'],
                                                               "module": "translation",  "date": datetime.datetime.utcnow(), "log_no": log_no})
                        return Response(data={"message":"Tranlation added"},status=200)
                db.translations.insert_one({"language":request.data['language'],"translation":[{"text":request.data['text'],
                                        "versions":[{"trans":request.data['trans'],"version":1,"currentVersion":True}],
                                                "master_id":request.data['master_id'],"trans_id":request.data['tran_id']}]})
                data = db.log_input_module.insert_one({"user": name['name'], "action": "added new translation " + request.data['text'],
                                                       "module": "translation", "date": datetime.datetime.utcnow(), "log_no": log_no})
                return Response(data={"message":"Tranlation added"},status=200)
            return Response(serializer.errors,status=400)
        except KeyError:
            return Response(status=400)
    elif request.method == 'PUT':
        serializer = TranslationUpdateSerializer(data=request.data)
        if serializer.is_valid():
            lan = request.data['language']
            master = request.data['master_id']
            db.translations.update_many({"language": request.data['language'], "translation.master_id": request.data['master_id']},
                                        {"$set": {"translation.$.versions.$[].currentVersion":False}})
            up = db.translations.update_one({"language":request.data['language'],"translation.master_id":request.data['master_id']},
                                       {"$push":{"translation.$.versions":{"trans":request.data['trans'],"version":transVersion(lan,master),"currentVersion":True}}})
            data = db.log_input_module.insert_one({"user": name['name'], "action": "added new version " + request.data['trans'] +" to "+request.data['language'],
                                                   "module": "translation","date": datetime.datetime.utcnow(), "log_no": log_no})
            if up.acknowledged:
                return Response(data={"message":"Translation updated"},status=200)
            return Response(data={"message": "Translation not updated"}, status=200)
        else:
            return Response(data=serializer.errors,status=400)
    elif request.method == 'DELETE':
        for i in request.data["tran_ids"]:
            text = list(db.translations.find({"translation.trans_id":i}))
            for j in text[0]['translation']:
                if i == j['trans_id']:
                    log = db.log_input_module.insert_one(
                        {"user": name['name'], "action": "deleted translation of " + j['text'] + " from " + text[0]['language'],
                         "module": "translation",  "date": datetime.datetime.utcnow(), "log_no": log_no})
        data = db.translations.update_many(
            {'language': request.data['language']},
            {"$pull": {"translation": {"trans_id": {"$in": request.data['tran_ids']}}}},
            upsert=True)
        if data.acknowledged:
            return Response(data={"message":"Translation deleted"},status=200)
        return Response(data={"message": "Translation Not deleted"}, status=200)
language = openapi.Parameter('language', openapi.IN_QUERY, type=openapi.TYPE_STRING)
trans_id = openapi.Parameter('trans_id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['get'], manual_parameters=[language,trans_id])
@api_view(['GET'])
def translationVerions(request):
    name = username(request.auth)
    if request.method == 'GET':
        string = request.GET['trans_id']
        clean_string = re.sub(r'\s|\[.*?\]', '', string)
        print(clean_string)
        data =list(db.translations.aggregate([
    { "$match": {"language": request.GET['language']}},
    { "$unwind": '$translation'},
    { "$match": {'translation.trans_id':   clean_string }},
    { "$group": {"_id": '$translation.text',"translation": {"$push": '$translation.versions'}}}
    ]))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)


#api for get update delete and add language
@swagger_auto_schema(methods=['post'], request_body=LanguageSerializer)
@swagger_auto_schema(methods=['put'], request_body=LanguageUpdateSerializer)
@api_view(['POST','GET','DELETE','PUT'])
def languageAddViewDelUpdate(request):
    name = username(request.auth)
    Date = datetime.datetime.today()
    time = datetime.datetime.now().time()
    log_no = logNo("language")
    if request.method == 'GET':
        data = db.language.find()
        js_data = dumps(data, indent=1)
        with open('data.json', 'w') as file:
            file.write(js_data)
        json_data = json.loads(js_data)
        return Response(data=json_data)
    elif request.method == 'POST':
        serializer = LanguageSerializer(data=request.data)
        if serializer.is_valid():
            if db.language.find({"code":request.data['code']}).count():
                return Response(data={"message":"language code already exist"},status=400)
            db.language.insert_one(request.data)
            data = db.log_input_module.insert_one({"user":name['name'],"action":"added new language " + request.data['name'],
                                                       "module":"language", "date": datetime.datetime.utcnow(),"log_no":log_no})
            return Response(status=201)
        else:
            return Response(serializer.errors,status=400)
    elif request.method == 'PUT':
        try:
            serializer = LanguageUpdateSerializer(data=request.data)
            if serializer.is_valid():
                lang = list(db.language.find({"_id": ObjectId(request.data['id'])}))
                up = db.translations.update_one({"language":lang[0]['code']},{"$set":{"language":request.data['code']}})
                data =db.language.update_one({"_id": ObjectId(request.data['id'])},{"$set":{"name":request.data['name'],
                                                                           "code":request.data['code']}})
                action = ''
                if lang[0]['name'] != request.data['name']:
                    if action == '':
                        action += "changed "
                    action += " language name " + lang[0]['name'] + " to " + request.data['name']
                if lang[0]['code'] != request.data['code']:
                    if action == '':
                        action += "changed "
                    else:
                        action += " and "
                    action += "language code " + lang[0]['code'] + " to " + request.data['code']
                log = db.log_input_module.insert_one(
                    {"user": name['name'], "action": action, "module": "language",
                     "date": datetime.datetime.utcnow(), "log_no": log_no})
                if data.acknowledged:
                    return Response(data={"message": "langauge updated"},status=200)
                return Response(data={"message": "langauge not updated"}, status=200)
            return Response(data = serializer.errors,status=400)
        except KeyError:
            return Response(status=400)
    elif request.method == "DELETE":
        data = deleteLanguage(request.data)
        for i in request.data['id']:
            try:
                lan = list(db.language.find({"_id":ObjectId(i)}))
                tran = db.translations.delete_one({"language": lan[0]['code']})
                log = db.log_input_module.insert_one({"user":name['name'],"action":"deleted language " + lan[0]['name'],"module":"language",
                                                       "date": datetime.datetime.utcnow(),"log_no":log_no})
                delete_from_country = db.country.find({"$pull": { 'language': lan[0]['code'] }})
            except:pass
        delete = db.language.delete_many({
                "_id": {
                "$in": data
            }
        })
        res = {
            "aknowledged": delete.acknowledged,
            "deletedCount": delete.deleted_count
        }
        return Response(data=res)
from .history import countryHistory
from .reports import CountryData
#api for get update delete and add language
@swagger_auto_schema(methods=['post'], request_body=CountrySerializer)
@swagger_auto_schema(methods=['put'], request_body=CountryUpdateSerializer)
@api_view(['GET','POST','DELETE','PUT'])
def counrtyViewAddDelUpdate(request):
    name = username(request.auth)
    Date = datetime.datetime.today()
    time = datetime.datetime.now().time()
    log_no = logNo("country")
    if request.method == 'GET':
        data = CountryData()
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)
    elif request.method == 'POST':
        serializer = CountrySerializer(data=request.data)
        try:
            if serializer.is_valid():
                data = db.country.find({"code": request.data['code']})
                for i in data:
                    if i['code'] == request.data['code']:
                        return Response(data={"message": "country already exist"},status=400)
                data = db.country.insert_one(request.data)
                data = db.log_input_module.insert_one(
                    {"user": name['name'], "action": "added new country " + '"' + request.data['name'] + '"',
                     "module": "country",  "date": datetime.datetime.utcnow(), "log_no": log_no})
                res = {"message": "country added"}
                return Response(data=res,status=200)
            return Response(data=serializer.errors,status=400)
        except KeyError:
            return Response(status=400)
    elif request.method == 'PUT':
        serializer = CountryUpdateSerializer(data=request.data)
        try:
            if serializer.is_valid():
                country = list(db.country.find({"_id":ObjectId(request.data['id'])}))
                action = countryHistory(request.data,country[0])
                if (db.factory.find({"location.label":country[0]['name']}).count()) > 0:
                    db.factory.update({"location.label":country[0]['name']},
                                      {"$set":{"location":{"label":request.data['name'],
                                                                         "value":request.data['code']}}})
                data = db.country.update_one({"_id":ObjectId(request.data['id'])},
                                             {"$set":{"name":request.data['name'],"code":request.data['code'],
                                                      "language":request.data['language']}})
                data = db.log_input_module.insert_one(
                    {"user": name['name'], "action":action,
                     "module": "country",  "date": datetime.datetime.utcnow(), "log_no": log_no})
                if data.acknowledged:
                    return Response(data ={"message":"Counry modified"},status=200)
                return Response(data={"message": "Counry not modified"}, status=200)
            return Response(data=serializer.errors,status=401)
        except KeyError:
            return Response(status=400)
    elif request.method == "DELETE":
        for i in request.data['code']:
            country = list(db.country.find({"code":i}))
            data = db.country.delete_one({"code":i})
            log = db.log_input_module.insert_one(
                {"user": name['name'], "action": "deleted country " + '"' + country[0]['name'] + '"',
                 "module": "country", "date": datetime.datetime.utcnow(), "log_no": log_no})
        if data.acknowledged:
            return Response(data={"message":"Country deleted"},status=200)
        return Response(data={"message":"Country not deleted"},status=200)

#api for get update delete and add mastercode
from .serializers import DeleteMastaerCodeSerializer
text= openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING)
type = openapi.Parameter('type', openapi.IN_QUERY,type=openapi.TYPE_INTEGER)
master_id = openapi.Parameter('master_id', openapi.IN_QUERY,type=openapi.TYPE_STRING)
id = openapi.Parameter('id', openapi.IN_QUERY,type=openapi.TYPE_STRING)

@swagger_auto_schema(method='post', manual_parameters=[text])
@swagger_auto_schema(method='put', manual_parameters=[text,id])
@swagger_auto_schema(method='delete', request_body=DeleteMastaerCodeSerializer)
@api_view(['GET', 'POST', 'DELETE', 'PUT'])
def masterCodeVIewAddDelUpdate(request):
    Date = datetime.datetime.today()
    time = datetime.datetime.now().time()
    log_no = logNo("mastercode")
    user = username(request.auth)
    if request.method == 'GET':
        data = db.master_code.find({},{"_id":0,"id":1,"text":1,"type":1}).sort("id",1).collation({"locale": "en_US", "numericOrdering": True})
        js_data = dumps(data, indent=1)
        with open('data.json', 'w') as file:
            file.write(js_data)
        json_data = json.loads(js_data)
        return Response(data=json_data)
    elif request.method == 'POST':
        data = db.master_code.find({"text": request.GET['text']})
        for i in data:
            if i['text'] == request.GET['text']:
                return Response(data={"message":"masterCode already exists"},status=200)
            else:
                pass
        master_id = str(masterCodeId())
        data = db.master_code.insert_one({"id": master_id, "text": request.GET['text'], "type":0})
        data = db.log_input_module.insert_one({"user": user['name'], "action": "added new Master Code " +'"' + master_id+'"',
                                               "module": "mastercode","date": datetime.datetime.utcnow(), "log_no": log_no})
        if data.acknowledged == True:
            return Response(data={"message":"masterCode added"}, status=200)
        else:
            return Response(status=400)
    elif request.method == 'PUT':
        try:
            master_code = list(db.master_code.find({"id":request.GET['id']}))
            data = db.master_code.update_one({"id":request.GET['id']}, {
                "$set": {"text": request.GET['text']}})
            action = "edited master code " + request.GET['id'] +" "+ master_code[0]['text'] + " to " + request.GET['text']
            data = db.log_input_module.insert_one(
                {"user":user['name'], "action":action, "module": "mastercode",
                 "date": datetime.datetime.utcnow(), "log_no": log_no})
            return Response(data= data.acknowledged,status=200)
        except KeyError:
            return Response(status=400)
    elif request.method == 'DELETE':
        master_code = []
        for i in request.data['master_ids']:
            translation = db.translations.find({"translation.master_id":i}).count()
            blend =db.blend.find({"$or":[{"blend_loose":i},{" blend_tea_bag":i},{" tea_origin":i},
                                         {"ingredient_loose":i},{"ingredient_tea_bag":i}]}).count()
            factory = db.factory.find({"$or":[{"packed_in.value":i},{"address.value":i}]}).count()
            legal = db.legal_name.find({"translation":i}).count()
            blend_requirements = db.blend_requirements.find({"value":i}).count()
            item_requirements= db.item_no_requirements.find({"value":i}).count()
            custom = db.custom_condition.find({"output.value":i}).count()
            if db.additional_requirement.find({"value":i}).count() >0:
                res = {"Master code " + i + ' Present in Requirement module'}
                return Response(data=res, status=200)
            if translation > 0:
                res = {"Translation present for master code " +"  " + '" '+ i + ' "' }
                return Response(data=res, status=200)
            elif blend > 0:
                res = {"Master code " + i + ' Present in blend module'}
                return Response(data=res, status=200)
            elif factory > 0 :
                res = {"Master code " + i + ' Present in factory module'}
                return Response(data=res, status=200)
            elif legal > 0:
                res = {"Master code " + i + ' Present in legal name module'}
                return Response(data=res, status=200)
            elif custom > 0:
                res = {"Master code " + i + ' Present in custom condition'}
                return Response(data=res, status=200)
            elif blend_requirements > 0:
                res = {"Master code " + i + ' Present in blend requirement'}
                return Response(data=res, status=200)
            elif item_requirements > 0:
                res = {"Master code " + i + ' Present in item requirement'}
                return Response(data=res, status=200)
            else:
                masterCode = list(db.master_code.find({"id":i}))
                data = db.master_code.delete_one({"id":i})
                log = db.log_input_module.insert_one(
                {"user": user['name'], "action": "deleted  Master Code " + i + "-" +masterCode[0]['text'], "module": "mastercode",
                 "date": datetime.datetime.utcnow(), "log_no": log_no})
        return Response(data="true", status=201)

#api for get update delete and add factory
from .history import factoryHistory
id = openapi.Parameter('id', openapi.IN_QUERY,type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['post'], request_body=FactorySerializer)
@swagger_auto_schema(methods=['put'], request_body= FactoryUpdateSerializer)
@swagger_auto_schema(methods=['delete'], manual_parameters= [id])
@api_view(['GET', 'POST', 'DELETE', 'PUT'])
def factoryAddViewDelUpdate(request):
    Date = datetime.datetime.today()
    name = username(request.auth)
    time = datetime.datetime.now().time()
    log_no = logNo("factory")
    if request.method == 'GET':
        data = list(db.factory.find())
        js_data = dumps(data, indent=1)
        with open('data.json', 'w') as file:
            file.write(js_data)
        json_data = json.loads(js_data)
        return Response(data=json_data)
    elif request.method == 'POST':
        serializer = FactorySerializer(data=request.data)
        try:
            if serializer.is_valid():
                data = db.factory.find({"location.value":request.data['location']['value']})
                for i in data:
                    if i['location'] == request.data['location']:
                        return Response({"message":"factory already exist"},status=200)
                db.factory.insert_one({"location":request.data['location'],"packed_in":request.data['packed_in'],
                                       "address":request.data['address']})
                data = db.log_input_module.insert_one(
                    {"user":name['name'], "action": "added new factory " + '"' + request.data['location']['label'] + '"',
                     "module": "factory", "date": datetime.datetime.utcnow(), "log_no": log_no})
                return Response(data=serializer.data, status=201)
            return Response(data=serializer.errors,status=401)
        except KeyError:
            return Response(status=400)
    elif request.method == 'PUT':
        serializer = FactoryUpdateSerializer(data=request.data)
        if serializer.is_valid():
            factory = list(db.factory.find({"_id": ObjectId(request.data['id'])}))
            data = db.factory.update_one({"_id": ObjectId(request.data['id'])},{"$set":{"location":request.data['location'],
                                            "packed_in":request.data['packed_in'],"address":request.data['address']}})
            action = factoryHistory(request.data,factory[0])
            log = db.log_input_module.insert_one(
                {"user": name['name'], "action":action,
                 "module": "factory","date": datetime.datetime.utcnow(), "log_no": log_no})
            if data.acknowledged:
                return Response(data={"message":"Factory modified"},status=200)
            return Response(data={"message":"Factory not modified"},status=200)
        else:
            return Response(data=serializer.errors,status=400)
    elif request.method == 'DELETE':
        factory = db.factory.find_one({"_id": ObjectId(request.GET['id'])})
        data = db.factory.delete_one({"_id": ObjectId(request.GET['id'])})
        log = db.log_input_module.insert_one(
            {"user": name['name'], "action": "deleted factory" + '"' + factory['location']['label'] + '"',
             "module": "factory","date": datetime.datetime.utcnow(), "log_no": log_no})
        return Response(data=data.acknowledged)


# Api for  add update and delete requiremnt
from .history import requirementHistory
from .userDetails import update_requirement_order
id = openapi.Parameter('id', openapi.IN_QUERY,type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['get'], manual_parameters=[id])
@swagger_auto_schema(methods=['post'], request_body=RequirementSerializers)
@swagger_auto_schema(methods=['put'], request_body= RequirementUpdateSerializers)
@swagger_auto_schema(methods=['delete'],request_body=DeleteRequirementsSerializer)
@api_view(['GET','POST', 'DELETE', 'PUT'])
def AddDelUpdateRequirements(request):
    Date = datetime.datetime.today()
    name = username(request.auth)
    time = datetime.datetime.now().time()
    log_no = logNo("requirement")
    if request.method == 'GET':
        data = list(db.additional_requirement.find({'_id': ObjectId(request.GET['id'])}).sort("order",1))
        requirements = []
        for i in data:
            if i['type'] == 'Translation-ID':
                text = db.master_code.find({"id": i['value']})
                dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],
                               "value":text[0]['id'] +"-"+ text[0]['text'], "country": i['country'],"order":i['order'],
                               "static":i['static']}
                requirements.append(dict_values)
            elif i['type'] == 'Asset':
                image = db.myapp_asset.find({'id': i['value']})
                dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],
                               "value": image[0]['name'],"photo":"http://"+request.get_host()+"/media/"+image[0]['photo'], "country": i['country'],
                               "order": i['order'], "static": i['static']
                               }
                requirements.append(dict_values)
            else:
                dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'], "value": i['value'],
                               "country": i['country'],"order": i['order'], "static": i['static']}
                requirements.append(dict_values)
        js = json.dumps(requirements, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)
    if request.method == 'POST':
        serializer = RequirementSerializers(data=request.data)
        if serializer.is_valid():
            # if db.additional_requirement.find({"requirement":request.data['requirement']}).count() >0:
            #     return Response(data={"message":"Requirement already exist"},status=201)
            if request.data['type'] == 'Translation-ID':
                val = db.master_code.find({"id":request.data['value']})
                try:
                    id = val[0]['id']
                except:
                    id = ""
                if db.additional_requirement.find({"order":int(request.data['order'])}).count() > 0:
                    db.additional_requirement.update_many(
                        {"order": {"$gte":int(request.data['order'])}},
                        {"$inc": {"order": 1}},
                    )
                data = db.additional_requirement.insert_one({"requirement":request.data['requirement'],"type":request.data['type'],
                                                             "value":id,"country":request.data['country'],
                                                             "static":request.data['static'],"order":int(request.data['order'])})
                log = db.log_input_module.insert_one({"user": name['name'], "action": "added new requirement " + request.data['requirement'],
                                                      "module": "requirement","date": datetime.datetime.utcnow(), "log_no": log_no})
                json_data = dumps(data.acknowledged, indent=1)
                update_order = update_requirement_order()
                return Response(data={"message":"requirement added"}, status=200)
            else:
                # if db.additional_requirement.find({"order": int(request.data['order'])}).count() > 0:
                #     db.additional_requirement.update_many(
                #         {"order": {"$gte": int(request.data['order'])}},
                #         {"$inc": {"order": 1}},
                #     )
                data = db.additional_requirement.insert_one({"requirement": request.data['requirement'],
                                                             "type": request.data['type'], "value": request.data['value'],
                                                             "country": request.data['country'],
                                                             "static":request.data['static'],"order":int(request.data['order'])})
                log = db.log_input_module.insert_one({"user": name['name'], "action": "added new requirement " + request.data['requirement'],
                                                      "module": "requirement", "date": datetime.datetime.utcnow(), "log_no": log_no})
                update_order = update_requirement_order()
                return Response(data={"message": "requirement added"}, status=200)
        else:
            return Response(serializer.errors,status=401)
    elif request.method == 'PUT':
        serializer = RequirementUpdateSerializers(data=request.data)
        if serializer.is_valid():
            order = int(request.data['order'])
            req = list(db.additional_requirement.find({"_id":ObjectId(request.data['id'])}))
            action = requirementHistory(request.data,req[0])
            setcustom = db.custom_condition.update({"output.requirement": req[0]['requirement']},
                                                   {"$set": {"output.requirement": request.data['requirement']}})
            if request.data['type'] == 'Translation-ID':
                setcustom = db.custom_condition.update({"output.requirement":req[0]['requirement']},{"$set":{"output.requirement":request.data['requirement']}})
                if db.additional_requirement.find({"_id": ObjectId(request.data['id']),"order": {"$lte": order}}).count() > 0:
                    order += 1
                if db.additional_requirement.find({"order": order}).count() > 0:
                    db.additional_requirement.update_many(
                        {"order": {"$gte":  order}},
                        {"$inc": {"order": 1}},
                    )
                value = ''
                if db.master_code.find({"id": request.data['value']}).count() >0:
                    val = db.master_code.find({"id": request.data['value']})
                    value = val[0]['id']
                data = db.additional_requirement.update_one({"_id":ObjectId(request.data['id'])},
                        {"$set":{"requirement":request.data['requirement'],"type":request.data['type'],
                                 "value":value,"country":request.data['country'],
                                 "static":request.data['static'],"order":order}})
                log = db.log_input_module.insert_one(
                    {"user": name['name'], "action": action,
                     "module": "requirement", "date": datetime.datetime.utcnow(), "log_no": log_no})
                update_order = update_requirement_order()
                return Response(data={"message":"Requirement Modified"},status=200)
            else:
                if db.additional_requirement.find({"_id": ObjectId(request.data['id']),
                                                   "order": {"$lte": order}}).count() > 0:
                    order += 1
                if db.additional_requirement.find({"order":order}).count() > 0:
                    db.additional_requirement.update_many(
                        {"order": {"$gte": order}},
                        {"$inc": {"order": 1}},
                    )
                data = db.additional_requirement.update_one({"_id": ObjectId(request.data['id'])},
                                                            {"$set": {"requirement": request.data['requirement'],
                                                                      "type": request.data['type'],"value":
                    request.data['value'], "country": request.data['country'],
                                                                      "static":request.data['static'],"order":order}})
                log = db.log_input_module.insert_one(
                    {"user": name['name'], "action":action,
                     "module": "requirement","date": datetime.datetime.utcnow(), "log_no": log_no})
                update_order = update_requirement_order()
                return Response(data={"message":"Requirement Modified"},status=200)
        else:
            return Response(serializer.errors,status=400)
    elif request.method == 'DELETE':
        for i in request.data['id']:
            req = list(db.additional_requirement.find({"_id":ObjectId(i)}))
            try:
                if req[0]['static']:
                    return Response(data={"message":"Static requirement cannot delete"},status=200)
            except Exception as e:
                pass
            data = db.additional_requirement.delete_many({"_id":ObjectId(i)})
        if data.acknowledged:
            log = db.log_input_module.insert_one(
                {"user": name['name'], "action": "deleted requirement " + req[0]['requirement'],
                 "module": "requirement", "date": datetime.datetime.utcnow(), "log_no": log_no})
            update_order = update_requirement_order()
            return Response(data={"message":"Requirement Deleted"},status=200)
        return Response(data={"message":"Requirement Not Deleted"},status=200)

#Api for  view requirement
country = openapi.Parameter('country', openapi.IN_QUERY,type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(method='post', manual_parameters=[country])
@api_view(['GET','POST'])
def viewRequirement(request):
    name = username(request.auth)
    if request.method == 'GET':
        data = list(db.additional_requirement.find().sort("order",1))
        requirements = []
        for i in data:
                if i['type']=='Translation-ID':
                    text = list(db.master_code.find({"id":i['value']}))
                    try:
                        dict_values = {"_id":i['_id'],"requirement":i['requirement'],"type":i['type'],"value":i['value'],"text":text[0]['text'],"country":i['country']
                                       ,"order": i['order'], "static": i['static']}
                    except:
                        dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],"value": "", "text": "", "country": i['country']
                                       ,"order": i['order'], "static": i['static']}
                    requirements.append(dict_values)
                elif i['type'] == 'Asset':
                    images = db.myapp_asset.find({'id':i['value']}).count()
                    if images > 0:
                        image = db.myapp_asset.find({'id': i['value']})
                        dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],
                                       "photo":"http://"+request.get_host()+"/media/"+image[0]['photo'], "text": image[0]['name'],"country":i['country'],"value":i['value'],
                                       "order": i['order'], "static": i['static']}
                        requirements.append(dict_values)
                    else:
                        dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],
                                       "photo": "","order": i['order'], "static": i['static'],
                                       "text": "", "country": i['country'], "value": i['value']}
                        requirements.append(dict_values)

                else:
                    dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'], "value": i['value'],"country":i['country']
                                   ,"order": i['order'], "static": i['static']}
                    requirements.append(dict_values)
        js = json.dumps(requirements, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)
    elif request.method == 'POST':
        data = list(db.additional_requirement.find({ "$or": [ { "country": "All" }, { "country": request.GET['country']} ] }).sort("order",1))
        requirements = []
        for i in data:
            if i['type'] == 'Translation-ID':
                if db.master_code.find({"id": i['value']}).count() > 0:
                    text = list(db.master_code.find({"id": i['value']}))
                    dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],
                                   "value": str(text[0]['id']) + "-" + str(text[0]['text']), "country": i['country']
                        ,"order": i['order'], "static": i['static']}
                else:
                    dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],
                                   "value":i['value'], "country": i['country'],"order": i['order'], "static": i['static']}
                requirements.append(dict_values)
            elif i['type'] == 'Asset':
                image = db.myapp_asset.find({'id': i['value']})
                dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],
                               "value":"http://"+request.get_host()+"/media/"+image[0]['photo'],"order": i['order'], "static": i['static']}
                requirements.append(dict_values)
            else:
                dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'], "value": i['value']
                               ,"order": i['order'], "static": i['static']}
                requirements.append(dict_values)
        js = json.dumps(requirements, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)

# api for add update delete and view blends
from .history import blendHistory
@swagger_auto_schema(methods=['post'], request_body=BlendSerializer)
@swagger_auto_schema(methods=['put'], request_body=BlendUpdateSerializer)
@swagger_auto_schema(methods=['delete'], request_body=BlendDeleteSerializer)
@api_view(['GET','POST','DELETE','PUT'])
def addViewDelUpdateBlend(request):
    name = username(request.auth)
    Date = datetime.datetime.today()
    time = datetime.datetime.now().time()
    log_no = logNo("blend")
    if request.method == 'GET':
        blends =[]
        data = db.blend.find()
        for i in data:
            try:
                blend_name_loose = list(db.master_code.find({"id":i['blend_loose']}))
                blend_loose =  blend_name_loose[0]['id'] +'-'+ blend_name_loose[0]['text']
                blendLoose_code =  blend_name_loose[0]['id']
            except:
                blend_loose = ''
                blendLoose_code= ''
            try:
                blend_name_teaBag = list(db.master_code.find({"id":i['blend_tea_bag']}))
                blend_tea_bag = blend_name_teaBag[0]['id'] +'-'+blend_name_teaBag[0]['text']
                blendTeaBag_code = blend_name_teaBag[0]['id']
            except:
               blend_tea_bag = ''
               blendTeaBag_code= ''
            try:
                ingredient_name_teaBag = list(db.master_code.find({"id": i['ingredient_tea_bag']}))
                ingredient_tea_bag = ingredient_name_teaBag [0]['id'] + '-' + ingredient_name_teaBag [0]['text']
                ingredientTeaBag_code = ingredient_name_teaBag [0]['id']
            except:
                ingredient_tea_bag = ''
                ingredientTeaBag_code = ''
            try:
                ingredient_name_loose = list(db.master_code.find({"id": i['ingredient_loose']}))
                ingredient_loose = ingredient_name_loose [0]['id'] + '-' + ingredient_name_loose [0]['text']
                ingredientLoose_code= ingredient_name_loose [0]['id']
            except:
                ingredient_loose = ''
                ingredientLoose_code = ''
            try:
                tea_origin_name = list(db.master_code.find({"id": i['tea_origin']}))
                tea_origin =  tea_origin_name[0]['id'] + '-' + tea_origin_name[0]['text']
                tea_origin_code =  tea_origin_name[0]['id']
            except:
                tea_origin = ''
                tea_origin_code = ''

            my_dict = {"name":i['name'],'blend_loose':blend_loose,"blend_tea_bag":blend_tea_bag,"ingredient_tea_bag":ingredient_tea_bag,
                   "ingredient_loose":ingredient_loose,"tea_origin":tea_origin,"_id":i['_id'],"blendLoose_code":blendLoose_code,
                      "blendTeaBag_code":blendTeaBag_code ,"tea_origin_code": tea_origin_code,
                       "ingredientLoose_code":ingredientLoose_code,"ingredientTeaBag_code":ingredientTeaBag_code,"range":i['range']}
            blends.append(my_dict)
        js = json.dumps(blends, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)
    elif request.method == 'POST':
        try:
            serializer = BlendSerializer(data=request.data)
            if serializer.is_valid():
                data = db.blend.find({"name":request.data['name']})
                for i in data:
                    if i['name'] == request.data['name']:
                        return Response(data={"message":"blend already exist"},status=200)
                db.blend.insert_one({"name":request.data['name'],
                                     "blend_loose":request.data['blend_loose'],"blend_tea_bag":request.data['blend_tea_bag'],
                                     "tea_origin":request.data['tea_origin'],"ingredient_loose":request.data['ingredient_loose'],
                                     "ingredient_tea_bag":request.data['ingredient_tea_bag'],"range":request.data['range']})
                log = db.log_input_module.insert_one(
                    {"user":name['name'], "action": "added blend " + request.data['name'],
                     "module": "blend", "date": datetime.datetime.utcnow(), "log_no": log_no})
                return Response(data={"message":"blend added"},status=200)
            return Response(data = serializer.errors,status=401)
        except KeyError:
            return Response(status=400)
    elif request.method == 'PUT':
        try:
            serializer = BlendUpdateSerializer(data=request.data)
            if serializer.is_valid():
                history = list(db.blend.find({"_id":ObjectId(request.data['id'])}))
                action = blendHistory(request.data,history[0])
                data = db.blend.update_one({"_id":ObjectId(request.data['id'])},{"$set":{"name":request.data['name'],
                                     "blend_loose":request.data['blend_loose'],"blend_tea_bag":request.data['blend_tea_bag'],
                                     "tea_origin":request.data['tea_origin'],"ingredient_loose":request.data['ingredient_loose'],
                                     "ingredient_tea_bag":request.data['ingredient_tea_bag'],"range":request.data['range']}})
                log = db.log_input_module.insert_one(
                    {"user": name['name'], "action": action,
                     "module": "blend","date": datetime.datetime.utcnow(), "log_no": log_no})
                if data.acknowledged:
                    return Response(data={"message":"Blend modified"},status=200)
                return Response(data={"message": "Blend not modified"}, status=200)
            return Response(data=serializer.errors,status=401)
        except KeyError:
            return Response(status=400)
    elif request.method == 'DELETE':
        for i in request.data['id']:
            legal = list(db.blend.find({"_id":ObjectId(i)}))
            try:
                legal = legal[0]['name']
            except:
                legal = ""
            data = db.blend.delete_one({"_id":ObjectId(i)})
            log = db.log_input_module.insert_one(
                {"user": name['name'], "action": "deleted blend" + legal[0]['name'],
                 "module": "blend","date": datetime.datetime.utcnow(), "log_no": log_no})
        if data.acknowledged:
            return Response(data={"message":"Blend deleted"},status=200)
        return Response(data={"message":"Blend not deleted"},status=200)


#Api for view add delete and update legal name
from .serializers import DeleteLegalNameUpdateSerializer
from .history import legalnameHistory
@swagger_auto_schema(methods=['post'], request_body= LegalNameSerializer )
@swagger_auto_schema(methods=['put'], request_body= LegalNameUpdateSerializer)
@swagger_auto_schema(methods=['delete'],  request_body= DeleteLegalNameUpdateSerializer)
@api_view(['GET','POST','DELETE','PUT'])
def addViewDelUpdateLegalName(request):
    Date = datetime.datetime.today()
    name = username(request.auth)
    time = datetime.datetime.now().time()
    log_no = logNo("legalname")
    if request.method == 'GET':
        legalName = []
        data = list(db.legal_name.find())
        for i in data:
            try:
                translations= list(db.master_code.find({"id": i['translation']}))
                translation = translations[0]['id'] + '-' + translations[0]['text']
                id = translations [0]['id']
            except:
                translation = ''
                id = ''
            my_dict ={"name":i['name'],"translation":translation,"id":id,"_id":i['_id']}
            legalName.append(my_dict)
        js = json.dumps(legalName, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)
    elif request.method == 'POST':
            serializer = LegalNameSerializer(data=request.data)
            if serializer.is_valid():
                data = db.legal_name.find({"name":request.data['name']})
                for i in data:
                    if i['name'] == request.data['name']:
                        return Response(data={"message": "legal name already exist"},status=200)
                data = db.legal_name.insert_one({"translation":request.data['translation'],"name":request.data['name'],
                                         })
                log = db.log_input_module.insert_one(
                    {"user":name['name'], "action": "added legal name " + request.data['name'],
                     "module": "legalname","date": datetime.datetime.utcnow(), "log_no": log_no})
                return Response(data={"message":"legal name added"},status=200)
            else:
                return Response(data=serializer.errors,status=400)
    elif request.method == 'PUT':
        try:
            serializer = LegalNameUpdateSerializer(data=request.data)
            if serializer.is_valid():
                legalname = list(db.legal_name.find({"_id": ObjectId(request.data['id'])}))
                data = db.legal_name.update({"_id": ObjectId(request.data['id'])}, {
                    "$set": {"name": request.data['name'],"translation":request.data['translation']}})
                action = legalnameHistory(request.data,legalname[0])
                log = db.log_input_module.insert_one(
                    {"user": name['name'], "action": action,
                     "module": "legalname", "date": datetime.datetime.utcnow(), "log_no": log_no})
                return Response(data={"message": "Legalname modified"},status=200)
            else:
                return Response(data=serializer.errors,status=400)
        except KeyError:
            return Response(status=400)
    elif request.method == 'DELETE':
        for i in request.data['id']:
            name = list(db.legal_name.find({"_id": ObjectId(i)}))
            data = db.legal_name.delete_one({"_id": ObjectId(i)})
            log = db.log_input_module.insert_one(
                {"user": name['name'], "action": "deleted legal name " + name[0]['name'],
                 "module": "legalname","date": datetime.datetime.utcnow(), "log_no": log_no})
            if data.acknowledged:
                return Response(data={"message":"Legalname Deleted"},status=200)
            return Response(data={"message":"Legalname Not Deleted"},status=200)


from .Id_generator import grid_log_id
from .gridview import GridPreview,additionalRequirements,LanguageTranslation,filter_data_lanuage,filter_grouped_translation
user = openapi.Parameter('user', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(methods=['post'], request_body= GridSerializer,manual_parameters=[user])
@api_view(['GET','POST','DELETE','PUT'])
def gridUpdateDeleteAdd(request):
    if request.method == 'GET':
        data = db.grids.find(request.data)
        name = username(request.auth)
        js_data = dumps(data, indent=1)
        with open('data.json', 'w') as file:
            file.write(js_data)
        json_data = json.loads(js_data)
        return Response(data=json_data)
    if request.method == 'POST':
        serializer = GridSerializer(data=request.data)
        users = list(db.myapp_customuser.find({"username": "langtest"}, {"_id": 0, "user_group": 1}))
        if serializer.is_valid():
            grid_values = request.data
            host = request.get_host()
            Grid = db.grids.find({"varient":request.data['varient']})
            for i in Grid:
                if i['varient'] == request.data['varient']:
                    error = {"message":"Grid already exist"}
                    return Response(data = error, status=201)
            grid = additionalRequirements(grid_values,host)
            preview = GridPreview(grid[0])
            lan = LanguageTranslation(grid[1],preview['languages'])
            print(lan)
            language_translation = filter_data_lanuage(lan,preview['data'])
            grouped_translation = filter_grouped_translation(grid[3],preview['data'])
            # group = grid[3]
            name = username(request.auth)
            Date = datetime.date.today()
            formatted_date =  Date.strftime("%d %B %Y")
            response = {"data":preview,"grid":grid[2],"translation":language_translation,"name":name['name'],
                                       "date":formatted_date ,"grouped":grouped_translation,"gridvalues":grid_values}
            return Response(data=response)
        else:
            return Response(data = serializer.errors,status=400)


varient = openapi.Parameter('var', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING)
@swagger_auto_schema(method='get', manual_parameters=[varient])
@swagger_auto_schema(methods=['post'], request_body= SaveGridSerializer)
@swagger_auto_schema(methods=['put'], request_body=GridVersionAddSerializer)
@api_view(['POST','PUT','GET'])
def gridVersion(request):
    name = username(request.auth)
    if request.method == 'POST':
        serializer = SaveGridSerializer(data=request.data)
        # print( serializer)
        if serializer.is_valid():
            user = username(request.auth)
            count =  db.grids.find({"varient":serializer.data['grid']['varient']}).count()
            if count == 0:
                date = datetime.datetime.today()
                formatted_date = date.strftime("%d %B %Y")
                res  = db.grids.insert_one({"job": serializer.data['grid']['job'],
                                            "item": serializer.data['grid']['item'],
                                            "varient": serializer.data['grid']['varient'],
                                            "countries": serializer.data['grid']['countries'],
                                            "date": request.data['date'],
                                            "user": serializer.data['user'],
                                            "blends":request.data['blend'],
                                            "duplicated":False,
                                            "category":request.data['category'],
                                            "range": serializer.data['grid']['range'],
                                            "no_of_bags":request.data['no_of_bags'],
                                            "legalname":request.data['legalname'],
                                            "tea_form": serializer.data['grid']['tea_form'],
                                            "weight":serializer.data['grid']['weight'],
                                            "languages":serializer.data['languages'],
                                            "Description": serializer.data['grid']['Description'],
                                            "factory": serializer.data['grid']['factory'],
                                            "type": serializer.data['grid']['type'],
                                            "version": [{"v_no": 1, "grid": serializer.data['data'],
                                            "languages": serializer.data['languages'],
                                            "translation_values":serializer.data['translation'],
                                            "grouped_translation":serializer.data['grouped_translation'],
                                            "special_requirement":serializer.data['special_requirement'],
                                            "gridinformations":serializer.data['gridinformations']
                                                                                           }]})

                loginfo= {"user": serializer.data['user'], "varient": serializer.data['grid']['varient'],"email":request.data['email'],
                          "type": "open","Description": serializer.data['grid']['Description'],"approver":request.data['approver'],
                          "item":serializer.data['grid']['item'],"job": serializer.data['grid']['job'],
                          "status": "Created", "flag": 1, "log": grid_log_id(serializer.data['grid']['varient']),
                          "user_group":user['user_group'],"factory": request.data['grid']['factory']['label']}
                history = db.grid_history.insert_one({"user": serializer.data['user'], "varient": serializer.data['grid']['varient'],"date": datetime.datetime.utcnow(),
                                                      "action":"Created Grid","V-no":1})
                return Response(data =loginfo,status=200)
            elif count > 0:
                v_no =   GridVersion(serializer.data['grid']['varient'])
                serializer.data['gridinformations']
                res = db.grids.update_one({"item": serializer.data['grid']['item'],
                                "varient": serializer.data['grid']['varient']}, {"$push": {
                                "version": {"v_no":v_no, "grid": serializer.data['data'],
                                "languages": serializer.data['languages'],
                                "grouped_translation": serializer.data['grouped_translation'],
                                "special_requirement": serializer.data['special_requirement'],
                                "translation_values": serializer.data['translation'],
                                "gridinformations":serializer.data['gridinformations']
                                }}})
                loginfo = {"user": serializer.data['user'], "varient": serializer.data['grid']['varient'],"email":request.data['email'],
                           "type": "open", "Description": serializer.data['grid']['Description'],"factory":request.data['grid']['factory']['label'],
                           "item": serializer.data['grid']['item'],"job": serializer.data['grid']['job'],"approver":request.data['approver'],
                           "status": "Modified", "flag": 1, "log": grid_log_id(serializer.data['grid']['varient']),
                           "user_group": user['user_group']}
                history = db.grid_history.insert_one(
                    {"user": serializer.data['user'], "varient": serializer.data['grid']['varient'],
                     "date": datetime.datetime.utcnow(),"action": "Added new version ,version no " +str(v_no) ,"V-no": v_no})
                return Response(data = loginfo ,status=200)
        else:
            return Response(data=serializer.errors,status=400)


    if request.method == 'PUT':
        v_no = GridVersion(serializer.data['grid']['varient'])
        serializer = SaveGridSerializer(data=request.data)
        if serializer.is_valid():
            res = db.grids.update_one({  "item": serializer.data['grid']['item'],
                                       "varient": serializer.data['grid']['varient']}, {"$push": {
                                            "version": {"v_no":v_no, "grid": serializer.data['data'],
                                                 "translation_values": serializer.data['translation']
                                                                         }}})
            return Response(status=200)
        else:
            return Response(data=serializer.errors, status=400)
    if request.method == 'GET':
        var = request.GET['var']
        data = db.grids.find_one({"varient":var})
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)


@api_view(['POST'])
def saveDuplicateGrid(request):
    name = username(request.auth)
    if request.method == 'POST':
        user = username(request.auth)
        date = datetime.datetime.today()
        res = db.grids.insert_one({"job": request.data['job'],
                                   "item": request.data['grid']['item'],
                                   "varient": request.data['varient'],
                                   "countries": request.data['grid']['countries'],
                                   "date": request.data['date'],
                                   "user": request.data['user'],
                                   "blends": request.data['grid']['blends'],
                                   "category": request.data['grid']['category'],
                                   "duplicated": True,
                                   "oldGrid":request.data['oldGrid'],
                                   "oldGrouped": request.data['oldGrouped'],
                                   "oldLanTrans": request.data['oldLanTrans'],
                                   "range": request.data['grid']['range'],
                                   "no_of_bags": request.data['grid']['no_of_bags'],
                                   "legalname": request.data['grid']['legalname'],
                                   "tea_form": request.data['grid']['tea_form'],
                                   "weight": request.data['grid']['weight'],
                                   "languages": request.data['languages'],
                                   "Description": request.data['grid']['Description'],
                                   "factory": request.data['grid']['factory'],
                                   "type": request.data['grid']['type'],
                                   "version": [{"v_no": 1, "grid": request.data['data'],
                                                "languages": request.data['languages'],
                                                "translation_values": request.data['translation'],
                                                "grouped_translation": request.data['grouped_translation'],
                                                "special_requirement": request.data['special_requirement']}]})

        loginfo = {"user": request.data['user'], "varient": request.data['varient'],"job": request.data['grid']['job'],"email":request.data['email'],
                   "type": "open", "Description": request.data['grid']['Description'], "factory": request.data['grid']['factory']['label'],
                   "item": request.data['grid']['item'],'approver':request.data['approver'],
                   "status":"Duplicated", "flag": 1, "log": grid_log_id(request.data['varient']),
                   "user_group": user['user_group']}

        return Response(data=loginfo, status=200)





category=openapi.Parameter('category', openapi.IN_QUERY,type=openapi.TYPE_STRING)
id = openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['post'], manual_parameters=[category])
@swagger_auto_schema(methods=['delete'], manual_parameters=[id])
@api_view(['GET','POST','DELETE'])
def categoryAddDeleteView(request):
    name = username(request.auth)
    if request.method == 'POST':
        db.category.insert_one({"category":request.GET['category']})
        return Response(data = request.GET['category'],status=200)
    if request.method == 'GET':
        data = db.category.find()
        return Response(dumps(data))
    if request.method == 'DELETE':
        data = db.category.delete_one({"_id":ObjectId(request.GET['id'])})
        json_data = dumps(data, indent=1)
        with open('data.json', 'w') as file:
            file.write(json_data)
        return Response(data=json_data)

no_of_teabags = openapi.Parameter('no_of_teabags', openapi.IN_QUERY, type=openapi.TYPE_STRING)
id = openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['post'], manual_parameters=[no_of_teabags])
@swagger_auto_schema(methods=['delete'], manual_parameters=[id])
@swagger_auto_schema(methods=['put'], manual_parameters=[id,no_of_teabags])
@api_view(['GET','POST','DELETE','PUT'])
def noOfTeaBag(request):
    name = username(request.auth)
    if request.method == 'POST':
        if db.no_of_tea_bag.find({"no_of_teabags":request.GET['no_of_teabags']}).count() >0:
            return Response(data="exist")
        db.no_of_tea_bag.insert_one({"no_of_teabags":request.GET['no_of_teabags']})
        return Response(data = request.GET['no_of_teabags'],status=200)
    if request.method == 'GET':
        data = list(db.no_of_tea_bag.find().sort("no_of_teabags",1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return Response(json_data)
    if request.method == 'PUT':
        data = db.no_of_tea_bag.update_one({"_id": ObjectId(request.GET['id'])},
                                           {"$set":{"no_of_teabags":request.GET['no_of_teabags']}})
        return Response(data.matched_count)
    if request.method == 'DELETE':
        data = db.no_of_tea_bag.delete_one({"_id":ObjectId(request.GET['id'])})
        return Response(data=data.acknowledged)

weight = openapi.Parameter('weight', openapi.IN_QUERY, type=openapi.TYPE_STRING)
id = openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['post'], manual_parameters=[weight])
@swagger_auto_schema(methods=['delete'], manual_parameters=[id])
@swagger_auto_schema(methods=['put'], manual_parameters=[id, weight])
@api_view(['GET', 'POST', 'DELETE', 'PUT'])
def Weights(request):
    name = username(request.auth)
    if request.method == 'POST':
        if db.weight.find({"weight": request.GET['weight']}).count() > 0:
            return Response(data="exist")
        db.weight.insert_one({"weight": request.GET['weight']})
        return Response(data=request.GET['weight'], status=200)
    if request.method == 'GET':
        data = list(db.weight.find().sort("weight", 1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return Response(json_data)
    if request.method == 'PUT':
        data = db.weight.update_one({"_id": ObjectId(request.GET['id'])},
                                           {"$set": {"weight": request.GET['weight']}})
        return Response(data.matched_count)
    if request.method == 'DELETE':
        data = db.weight.delete_one({"_id": ObjectId(request.GET['id'])})
        return Response(data=data.acknowledged)

tea_form = openapi.Parameter('tea_form', openapi.IN_QUERY, type=openapi.TYPE_STRING)
id = openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['post'], manual_parameters=[tea_form])
@swagger_auto_schema(methods=['delete'], manual_parameters=[id])
@swagger_auto_schema(methods=['put'], manual_parameters=[id,tea_form])
@api_view(['GET', 'POST', 'DELETE', 'PUT'])
def TeaBagForm(request):
    name = username(request.auth)
    if request.method == 'POST':
        if db.tea_form.find({"tea_form": request.GET['tea_form']}).count() > 0:
            return Response(data="exist")
        db.tea_form.insert_one({"tea_form": request.GET['tea_form']})
        return Response(data=request.GET['tea_form'], status=200)
    if request.method == 'GET':
        data = list(db.tea_form.find().sort("tea_form", 1))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return Response(json_data)
    if request.method == 'PUT':
        data = db.tea_form.update_one({"_id": ObjectId(request.GET['id'])},
                                           {"$set": {"tea_form": request.GET['tea_form']}})
        return Response(data.matched_count)
    if request.method == 'DELETE':
        data = db.tea_form.delete_one({"_id": ObjectId(request.GET['id'])})
        return Response(data=data.acknowledged)

asset_type = openapi.Parameter('tea_form', openapi.IN_QUERY, type=openapi.TYPE_STRING)
id = openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['post'], manual_parameters=[asset_type])
@swagger_auto_schema(methods=['delete'], manual_parameters=[id])
@swagger_auto_schema(methods=['put'], manual_parameters=[id,asset_type])
@api_view(['GET', 'POST', 'DELETE', 'PUT'])
def AssetType(request):
    name = username(request.auth)
    if request.method == 'POST':
        if db.asset_type.find({"asset_type": request.GET['asset_type']}).count() > 0:
            return Response(data="exist")
        db.asset_type.insert_one({"asset_type": request.GET['asset_type']})
        return Response(data=request.GET['asset_type'], status=200)
    if request.method == 'GET':
        data = list(db.asset_type.find().sort("asset_type", 1))
        myList = []
        for i in data:
            mydict={"label":i["asset_type"],"value":i["asset_type"],"id":i["_id"]}
            myList.append(mydict)
        js = json.dumps(myList, default=json_util.default)
        json_data = json.loads(js)
        return Response(json_data)
    if request.method == 'PUT':
        data = db.asset_type.update_one({"_id": ObjectId(request.GET['id'])},
                                           {"$set": {"asset_type": request.GET['asset_type']}})
        return Response(data.matched_count)
    if request.method == 'DELETE':
        data = db.asset_type.delete_one({"_id": ObjectId(request.GET['id'])})
        return Response(data=data.acknowledged)



Range = openapi.Parameter('range', openapi.IN_QUERY, type=openapi.TYPE_STRING)
id = openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['post'], manual_parameters=[Range])
@swagger_auto_schema(methods=['delete'], manual_parameters=[id])
@api_view(['GET','POST','DELETE'])
def selectRange(request):
    if request.method == 'POST':
        db.range.insert_one({"range":request.GET['range']})
        return Response(data = request.GET['range'],status=200)
    if request.method == 'GET':
        data = db.range.find()
        return Response(dumps(data))
    if request.method == 'DELETE':
        data = db.range.delete_one({"_id":ObjectId(request.GET['id'])})
        return Response(data=data.acknowledged)


id = openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['post'], request_body=CustomCondtionSerializer )
@swagger_auto_schema(methods=['put'], manual_parameters=[id])
@api_view(['GET','POST','PUT','DELETE'])
def CustomCondtionView(request):
    name = username(request.auth)
    if request.method == 'GET':
        data = db.custom_condition.find()
        js_data = dumps(data, indent=1)
        with open('data.json', 'w') as file:
            file.write(js_data)
        json_data = json.loads(js_data)
        return Response(data=json_data)
    if request.method == 'POST':
        serializer = CustomCondtionSerializer(data= request.data)
        if serializer.is_valid():
            serializer.data.update({"state":True})
            data = db.custom_condition.insert_one(serializer.data)
            return Response(data=serializer.data,status=200)
        else:
            return Response(data=serializer.errors, status=400)
    if request.method == 'PUT':
        serializer = CustomCondtionSerializer(data=request.data)
        if serializer.is_valid():
            data = db.custom_condition.update_one({"_id":ObjectId(request.GET['id'])},{"$set":serializer.data})
            return Response(data=data.acknowledged, status=200)
        else:
            return Response(data=serializer.errors, status=400)
    if request.method == 'DELETE':
        db.custom_condition.delete_one({"_id": ObjectId(request.data['id'])})
        message = {"message":"condition deleted"}
        return Response(data=message,status=200)

id = openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
state = openapi.Parameter('state', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN)
@swagger_auto_schema(methods=['post'], manual_parameters=[id,state])
@api_view(['POST'])
def enable_disable_condition(request):
    name = username(request.auth)
    if request.method == 'POST':
        state = request.GET['state']
        if state == 'false':
           state = False
        else:
           state = True
        data =  db.custom_condition.update_one({"_id":ObjectId(request.GET['id'])},{"$set":{"state":state}})
        if data.modified_count > 0:
            if state == True:
                message= {"message":"Condition Enabled"}
            else:
                message = {"message": "Condition disabled"}
            return Response(data=message,status=200)
        else:
            return Response(status=400)


language = openapi.Parameter('language', openapi.IN_QUERY,type=openapi.TYPE_STRING)
master_id = openapi.Parameter('master_id', openapi.IN_QUERY,type=openapi.TYPE_STRING)
tran_id = openapi.Parameter('tran_id', openapi.IN_QUERY,type=openapi.TYPE_STRING)
@swagger_auto_schema(methods=['post'], manual_parameters=[language,trans_id,master_id] )
@api_view(['GET','POST','DELETE'])
def transVersionChange(request):
    name = username(request.auth)
    if request.method == 'POST':
        try:
            version = int(request.GET['version'])
            setversion = db.translations.update_many(
                {"language":request.GET['language'], "translation.master_id":request.GET['master_id']},
                {"$set": {"translation.$.versions.$[].currentVersion": False}})
            update = db.translations.update_one(
                {"language": request.GET['language'], "translation.master_id":request.GET['master_id']},
                {"$set": {"translation.$.versions.$[b].currentVersion": True}}, upsert=True,
                array_filters=[{"b.version":version}])
            return Response(data=update.acknowledged,status=200)
        except:
            return Response(data="Select version",status=201)


from .reports import viewerReport
varient = openapi.Parameter('varient', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
item = openapi.Parameter('item', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_INTEGER,default='')
frm = openapi.Parameter('from', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
to = openapi.Parameter('to', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(method='post', manual_parameters=[varient,item,frm,to])
@api_view(['GET','POST'])
def grid_viewer_report(request):
    name = username(request.auth)
    if request.method == 'GET':
        data = db.log_grid_module.find({"status": "certified","flag":1})
        js_data = dumps(data, indent=1)
        with open('data.json', 'w') as file:
            file.write(js_data)
        json_data = json.loads(js_data)
        return Response(data=json_data)
    if request.method == 'POST':
        data = viewerReport(request)
        return Response(data = data)

from .reports import Report
varient = openapi.Parameter('varient', openapi.IN_QUERY, description="varient code ", type=openapi.TYPE_STRING,default='')
item = openapi.Parameter('item', openapi.IN_QUERY, description="item number", type=openapi.TYPE_INTEGER,default='')
frm = openapi.Parameter('frm', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
to = openapi.Parameter('to', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
type = openapi.Parameter('type', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_INTEGER,default='')
status = openapi.Parameter('status', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
usergroup = openapi.Parameter('usergroup', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(method='post', manual_parameters=[varient,item,frm,to,type,status,usergroup])
@api_view(['GET','POST'])
def grid_report(request):
    name = username(request.auth)
    if request.method == 'GET':
        data = db.log_grid_module.find({"flag":1})
        js_data = dumps(data, indent=1)
        with open('data.json', 'w') as file:
            file.write(js_data)
        json_data = json.loads(js_data)
        return Response(data=json_data,status=200)
    if request.method == 'POST':
        data = Report(request)
        return Response(data=data)

class FontViewSet(viewsets.ModelViewSet):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    queryset = Fonts.objects.all()
    serializer_class = FontSerializer
    def create(self,request):
        name = username(request.auth)
        serializer = FontSerializer(data = request.data)
        if serializer.is_valid():
            if Fonts.objects.filter(language=request.POST['language']).exists():
                fonts = Fonts.objects.filter(language=request.POST['language']).update(
                    name=request.POST['name'],
                    font = request.FILES['font']
                )
            else:
                fonts = Fonts.objects.create(
                    name=request.POST['name'],
                    font=request.FILES['font'],
                    language=request.POST['language'],
                    )
            return Response(serializer.data, status=204)
        else:
            return Response(serializer.errors, status=400)


from django.core.mail import EmailMessage, get_connection
from django.conf import settings
subject= openapi.Parameter('subject', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
message = openapi.Parameter('message', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
recipient_list = openapi.Parameter('recipient', openapi.IN_QUERY, description="test manual param", type=openapi.FORMAT_EMAIL,default='')
@swagger_auto_schema(method='post', manual_parameters=[message,subject,recipient_list])
@api_view(['POST'])
def Email(request):
    if request.method == "POST":
        with get_connection(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS
        ) as connection:
            subject = request.GET["subject"]
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [request.GET["recipient"],]
            message = request.GET["message"]
            EmailMessage(subject, message, email_from, recipient_list, connection=connection).send()
    return Response(data = message)

text= openapi.Parameter('text', openapi.IN_QUERY, type=openapi.TYPE_STRING)
type = openapi.Parameter('type', openapi.IN_QUERY,type=openapi.TYPE_INTEGER)
master_id = openapi.Parameter('master_id', openapi.IN_QUERY,type=openapi.TYPE_STRING)
@swagger_auto_schema(method='post', manual_parameters=[master_id,text,type])
@api_view(['POST'])
def Subtranslation(request):
    if request.method == 'POST':
         master_id = request.GET['master_id']
         master_id = subtranslation_id(master_id)
         data = db.master_code.insert_one({"id": master_id,
                                           "text": request.GET['text']})
         return Response(data=data.acknowledged ,status=200)

class AttachmentViewSet(viewsets.ModelViewSet):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
from .reports import dashboard
@api_view(['GET'])
def Dashboard(request):
    if request.method == 'GET':
        values = dashboard()
        return Response(data = values)


from .serializers import ExcelSerializer,TranslationImportExcelSerializer
from rest_framework.generics import GenericAPIView
class ExcelView(GenericAPIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = ExcelSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            files = data["files"]
            excel = importExcel(files)
            if excel['code'] == 200:
                return Response(data=excel['data'],status=200)
            elif excel['code'] == 204:
                return Response(data=excel['data'], status=204)
        return Response({'success': "False"}, status=status.HTTP_400_BAD_REQUEST)
    def get(self,request):
        data = LanaguaugeExport()
        server = "http://"+request.get_host()+"/media/exceltemplates/exported_json_data.xlsx"
        return Response({"file":server})

# api for converting database values to excel file
class TranslationImportView(GenericAPIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = TranslationImportExcelSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            excel = ImportTranslation(data)
            if excel['code'] == 200:
                return Response(data=excel['data'],status=204)
            elif excel['code'] == 204:
                return Response(data=excel['data'], status=200)
            elif excel['code'] == 208:
                return Response(data=excel['data'], status=201)
        return Response({'success': "False"}, status=status.HTTP_400_BAD_REQUEST)
    def get(self,request):
        language = request.GET['language']
        data = TranslationExport(language)
        server = "http://"+request.get_host()+"/media/exceltemplates/exported-translation.xlsx"
        return Response({"file":server})


language = openapi.Parameter('language', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(method='get', manual_parameters=[language])
@api_view(['GET'])
def get_font_name(request):
    if request.method == 'GET':
        lan =request.GET['language']
        data = list(db.myapp_fonts.find({'language': lan}))
        try:
            data[0]['name']
            return Response(data={"font":data[0]['name'],"url":"media/"+data[0]['font']})
        except:
            return Response(data={"font":"","url":""})

from .textTranslation import textTranslation
id = openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(method='get', manual_parameters=[id])
@swagger_auto_schema(method='delete', manual_parameters=[tran_ids])
@api_view(['GET','DELETE'])
def text_translation(request):
    name = username(request.auth)
    Date = datetime.datetime.today()
    time = datetime.datetime.now().time()
    log_no = logNo("translation")
    if request.method == 'GET':
        id = request.GET['id']
        data = textTranslation(id)
        # js = json.dumps(data, default=json_util.default)
        # with open('data.json', 'w') as file:
        #     file.write(js)
        return Response(data=data)
    elif request.method == 'DELETE':
        for i in request.data["tran_ids"]:
            log = db.log_input_module.insert_one(
                {"user": name['name'], "action": "deleted translation for " + i,
                "module": "translation","date": datetime.datetime.utcnow(), "log_no": log_no})
        data = db.translations.update_many({},{"$pull": {"translation": {"trans_id": {"$in":request.data["tran_ids"]}}}})

        return Response(data=data.acknowledged)

# api class for master code import and export
from .serializers import MasterCodeSerializer
from .excel import ImportMasterCode,MasterCodeExport
class MasterCodeImportView(GenericAPIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = MasterCodeSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            excel = ImportMasterCode(data)
            if excel['code'] == 200:
                return Response(data=excel['data'], status=200)
            elif excel['code'] == 204:
                return Response(data=excel['data'], status=204)
        return Response({'success': "False"}, status=status.HTTP_400_BAD_REQUEST)
    def get(self,request):
        data = MasterCodeExport()
        server = "http://"+request.get_host()+"/media/exceltemplates/exported-code.xlsx"
        return Response({"file":server})

@api_view(['GET'])
def languageCodes(request):
    if request.method == 'GET':
        List = []
        data = db.language.find({},{"_id":0,"name":0})
        for i in data:
            List.append(i['code'])
        return Response(data=List)


@api_view(['GET'])
def requirementDropdownvalues(request):
    if request.method == 'GET':
        value = []
        req = [{"label":"None","value":"","text":""}]
        country = []
        asset = []
        values = list(db.master_code.find().sort("id",1).collation({"locale": "en_US", "numericOrdering": True}))
        countries = list(db.country.find())
        assets = list(db.myapp_asset.find())
        try:
            for i in values:
                if i['text']:
                    value.append({"label":i["text"],"value":i['id']})
                    req.append({"label": i["id"] + " - " + i['text'], "value": i['id'],'text':i['text']})
        except:pass
        try:
            for j in countries:
                country .append({"label":j["name"],"value":j['code']})
        except:pass
        try:
            for k in assets:
                asset.append({"label":k["name"],"value":k['id']})
        except:pass
        return Response(data={"req_translation": req, "asset": asset,"country":country,"translation":value})

@api_view(['GET'])
def languageDropdownvalues(request):
    if request.method == 'GET':
        data = list(db.language.find())
        lan = []
        try:
            for i in data:
                lan.append({"value":i['code'],"label":i['name']})
            return Response(data={"languages": lan})
        except:
            return Response(data={"languages":lan})



from .serializers import CountryImportSerializer
from .excel import CountryExport,ImportCountry
class CountryImportExport(GenericAPIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = CountryImportSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            excel = ImportCountry(data)
            if excel['code'] == 200:
                return Response(data=excel['data'], status=200)
            elif excel['code'] == 204:
                return Response(data=excel['data'], status=204)
            elif excel['code'] == 202:
                return Response(data=excel['data'], status=202)
            return Response({'success': "False"}, status=status.HTTP_400_BAD_REQUEST)
    def get(self,request):
        data = CountryExport()
        server = "http://"+request.get_host()+"/media/exceltemplates/exported-country.xlsx"
        return Response({"file":server})

from .excel import CountryRequirementExport
@api_view(['GET'])
def CountryBaseRequirementExport(request):
    if request.method == 'GET':
        data = CountryRequirementExport(request)
        server = "http://" + request.get_host() + "/media/exceltemplates/"+request.GET['country']+"-requirement.xlsx"
        return Response({"file": server})

# def CountryBasedRequirement(request)


@api_view(['POST'])
def SearchRequirement(request):
    if request.method == 'POST':
        data = list(db.additional_requirement.find({"requirement":{'$regex': request.data['requirement']}}))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)


from .excel import FactoryExport
@api_view(['GET'])
def FactoryExcel(request):
    if request.method =='GET':
        data = FactoryExport()
        server = "http://"+request.get_host()+"/media/files/exported-factory.xlsx"
        return Response({"file":server})

@api_view(['GET'])
def CountryrequirementDropdownvalues(request):
    if request.method == 'GET':
        req = []
        values = list(db.additional_requirement.find({"country":{"$ne":"All"}}))
        value =[]
        for i in values:
            req.append({"label":i["requirement"],"value":i['_id']})
        js = json.dumps(req, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)

id = openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
country = openapi.Parameter('country', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(method='POST', request_body=CountryRequirementSerializers)
@swagger_auto_schema(method='DELETE', request_body=DeleteCountryRequirementSerializer)
@api_view(['POST','DELETE'])
def AddCountryRequirement(request):
    if request.method == 'POST':
        serializer = CountryRequirementSerializers(data=request.data)
        if serializer.is_valid():
            requirement = list(db.additional_requirement.find({"_id":ObjectId(request.data['id'])}))
            try:
                for i in requirement:
                    for j in i['country']:
                        if j == request.data['country']:
                            message ={"message":"requirement already exist"}
                            return Response(data=message,status=204)
                        else:
                            pass
                db.additional_requirement.update_one({"_id":ObjectId(request.data['id'])}, { "$push": {"country":request.data['country']}})
                message = {"message": "requirement added"}
                return Response(data=message, status=200)
            except:
                return Response(status=404)
        else:
            return Response(serializer.errors, status=400)

    if request.method == 'DELETE':
        for i in request.data['id']:
            try:
                data = list(db.additional_requirement.find({"_id": ObjectId(i)}))
                if data[0]['country'] == 'All':
                    return Response(data={"message": "Basic Requiremrnt cannot delete"}, status=200)
            except:
                pass
            data = db.additional_requirement.update_one({"_id": ObjectId(i)},{ "$pull": { "country":request.data['country'] }})
        if data.acknowledged:
            return Response(data={"message":"Requirement Removed"}, status=200)
        return Response(data={"message":"Requirement not Removed"}, status=200)


from .serializers import RequirementImportSerializer
from .excel import RequirementExport,ImportRequirement
class RequirementImportExport(GenericAPIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = RequirementImportSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            excel = ImportRequirement(data)
            #if response code is 200 requirement import has duplicate values
            if excel['code'] == 200:
                return Response(data=excel['data'], status=200)
            # if response code is 201 requirement master code not present in database
            elif excel['code'] == 201:
                return Response(data=excel['data'], status=201)
            # if response code is 201 requirement import is successful
            elif excel['code'] == 208:
                return Response(data=excel['data'], status=208)
            # if response code is 201 requirement country not present in database
            elif excel['code'] == 204:
                return Response(data=excel['data'], status=202)
        return Response({'success': "False"}, status=400)
    def get(self,request):
        data = RequirementExport(request)
        server = "http://"+request.get_host()+"/media/exceltemplates/exported-requirements.xlsx"
        return Response({"file":server})

from .serializers import RequirementImportSerializer
from .excel import BlendRequirementExport,ImportBlendRequirement
class BlendRequirementImportExport(GenericAPIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = RequirementImportSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            excel = ImportBlendRequirement(data)
            #if response code is 200 requirement import has duplicate values
            if excel['code'] == 200:
                return Response(data=excel['data'], status=200)
            # if response code is 201 requirement master code not present in database
            elif excel['code'] == 201:
                return Response(data=excel['data'], status=201)
            # if response code is 201 requirement import is successful
            elif excel['code'] == 208:
                return Response(data=excel['data'], status=208)
            # if response code is 201 requirement country not present in database
            elif excel['code'] == 204:
                return Response(data=excel['data'], status=202)
        return Response({'success': "False"}, status=400)
    def get(self,request):
        data = BlendRequirementExport(request)
        server = "http://"+request.get_host()+"/media/exceltemplates/exported-blend-requirements.xlsx"
        return Response({"file":server})


from .excel import ItemRequirementExport,ImportItemRequirement
class ItemRequirementImportExport(GenericAPIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = RequirementImportSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            excel = ImportItemRequirement(data)
            #if response code is 200 requirement import has duplicate values
            if excel['code'] == 200:
                return Response(data=excel['data'], status=200)
            # if response code is 201 requirement master code not present in database
            elif excel['code'] == 201:
                return Response(data=excel['data'], status=201)
            # if response code is 201 requirement import is successful
            elif excel['code'] == 208:
                return Response(data=excel['data'], status=208)
            # if response code is 201 requirement country not present in database
            elif excel['code'] == 204:
                return Response(data=excel['data'], status=202)
        return Response({'success': "False"}, status=400)
    def get(self,request):
        data = ItemRequirementExport(request)
        server = "http://"+request.get_host()+"/media/exceltemplates/exported-item-requirements.xlsx"
        return Response({"file":server})






from .userDetails import username
token = openapi.Parameter('token', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(method='GET', manual_parameters=[token])
@api_view(['GET'])
def UserName(request):
    return Response(username(request.auth))


@api_view(['GET'])
def IngredientsDropdownvalues(request):
    if request.method == 'GET':
        req = []
        values = db.ingredient.find()
        for i in values:
            req.append({"label":i["name"],"value":i['_id']})
        js = json.dumps(req, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)

from .serializers import BlendImportExcelSerializer
from .excel import BlendExport,ImportBlend
class BlendImportView(GenericAPIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = BlendImportExcelSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            excel = ImportBlend(data)
            print(excel)
            if excel['code'] == 200:
                return Response(data=excel['data'],status=204)
            elif excel['code'] == 204:
                return Response(data=excel['data'], status=200)
            elif excel['code'] == 208:
                return Response(data=excel['data'], status=201)
        return Response(data=serializer.errors, status=400)
    def get(self,request):
        data = BlendExport(request)
        server = "http://"+request.get_host()+"/media/exceltemplates/exported-blends.xlsx"
        return Response({"file":server})


from .excel import LegalNameExport,ImportLegalName
class LegalNameImportView(GenericAPIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = LegalNameImportExcelSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            excel = ImportLegalName(data)
            if excel['code'] == 200:
                return Response(data=excel['data'], status=200)
            elif excel['code'] == 201:
                return Response(data=excel['data'], status=201)
            elif excel['code'] == 204:
                return Response(data=excel['data'], status=204)
        return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def get(self,request):
        data = LegalNameExport(request)
        server = "http://"+request.get_host()+"/media/exceltemplates/exported-Legalname_3.xlsx"
        return Response({"file":server})

from .excel import ImportItemNo,ExportItemNo
class ItemNoImportExportView(GenericAPIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = ExcelSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            excel = ImportItemNo(data)
            if excel['code'] == 200:
                return Response(data=excel['data'], status=200)
            elif excel['code'] == 201:
                return Response(data=excel['data'], status=201)
            elif excel['code'] == 204:
                return Response(data=excel['data'], status=204)
        return Response(data={"status": "Failed"}, status=status.HTTP_400_BAD_REQUEST)
    def get(self,request):
        data = ExportItemNo(request)
        server = "http://"+request.get_host()+"/media/exceltemplates/itemNumber.xlsx"
        return Response({"file":server})

from .excel import ImportRegistrationNo,ExportRegistrationNo
class RegNoImportExportView(GenericAPIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = ExcelSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data
            excel = ImportRegistrationNo(data)
            if excel['code'] == 200:
                return Response(data=excel['data'], status=200)
            elif excel['code'] == 201:
                return Response(data=excel['data'], status=201)
            elif excel['code'] == 204:
                return Response(data=excel['data'], status=204)
        return Response(data={"status": "Failed"}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        item_no = request.GET['itemNo']
        data = ExportRegistrationNo(item_no)
        server = "http://" + request.get_host() + "/media/exceltemplates/RegistrationNumber"+str(request.GET['itemNo'])+".xlsx"
        return Response({"file": server})
#api for grid managementdropdown values
@api_view(['GET'])
def GridValuesDropDown(request):
    name = username(request.auth)
    if request.method == 'GET':
        legal_name = list(db.legal_name.find())
        blend_name_black = list(db.blend.find({"range":"Black tea"}))
        blend_name_green = list(db.blend.find({"range":"Green tea"}))
        blend_name_herbal = list(db.blend.find({"range":"Herbal tea"}))
        blend_name_natural = list(db.blend.find({"range":"Natural Benefit"}))
        factory_name = list(db.factory.find())
        no_of_teabag = list(db.no_of_tea_bag.find())
        tea_form = list(db.tea_form.find())
        weight = list(db.weight.find())
        countries = list(db.country.find())
        country = []
        language = []
        no_of_teabags = []
        legal_names = []
        requirements = []
        blend_names_black = []
        blend_names_green = []
        blend_names_herbal = []
        blend_names_natural = []
        factory_names = []
        weights =[]
        tea_forms = []
        try:
            for i in legal_name:
                legal_names.append({"label":i["name"],"value":i['translation']})
        except:pass
        try:
            for j in blend_name_green:
                blend_names_green.append({"label":j["name"],"value":j['_id']})
        except:pass
        try:
            for b in blend_name_black:
                blend_names_black.append({"label":b["name"],"value":b['_id']})
        except:pass
        try:
            for h in blend_name_herbal:
                blend_names_herbal.append({"label":h["name"],"value":h['_id']})
        except:pass
        try:
            for b in blend_name_natural:
                blend_names_natural.append({"label":b["name"],"value":b['_id']})
        except:pass
        try:
            for k in factory_name:
                factory_names.append(k['location'])
        except:pass
        try:
            for l in no_of_teabag:
                no_of_teabags.append({"label": l["no_of_teabags"], "value": l['no_of_teabags']})
        except:
            pass
        try:
            for w in weight:
                weights.append({"label": w["weight"], "value": w['weight']})
        except:
            pass
        try:
            for t in tea_form:
                tea_forms.append({"label": t["tea_form"], "value": t['tea_form']})
        except:
            pass
        try:
            for j in countries:
                country.append({"label": j["name"], "value": j['code']})
        except:
            pass
        data = {"no_of_teabag": no_of_teabags, "blend_name_black": blend_names_black,
                'blend_name_green': blend_names_green,
                'blend_name_herbal': blend_names_herbal,
                'blend_name_natural': blend_names_natural,
                "weight": weights, "tea_form": tea_forms,
                "legal_name": legal_names, "factory": factory_names, "country": country}
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)

user_group= openapi.Parameter('user_group', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(method='GET', manual_parameters=[user_group])
@api_view(['GET'])
def userGroupedView(request):
    name = username(request.auth)
    if request.method == 'GET':
        if request.GET['user_group'] == 'all':
            userList = []
            users = list(db.myapp_customuser.find({},{"id":1,"_id":0,"first_name":1,"last_name":1,"date_joined":1, "user_group":1}))
            js = json.dumps(users, default=json_util.default)
            json_data = json.loads(js)
            return Response(data=json_data)
        elif request.GET['user_group'] == 'viewer':
            userList = []
            users = db.myapp_customuser.find({"user_group":'Viewer'})
            for i in users:
                myDict = {"first_name": i["first_name"], "last_name": i["last_name"], "date_joined": i["date_joined"],
                         "user_group": i['user_group'], "id": i["id"]}
                userList.append(myDict)
            js = json.dumps(userList, default=json_util.default)
            json_data = json.loads(js)
            return Response(data=json_data)
        elif request.GET['user_group'] == 'admin':
            userList = []
            users = db.myapp_customuser.find({"user_group": 'Admin'})
            for i in users:
                myDict = {"first_name": i["first_name"], "last_name": i["last_name"],
                          "date_joined": i["date_joined"],
                          "user_group": i['user_group'], "id": i["id"]}
                userList.append(myDict)
            js = json.dumps(userList, default=json_util.default)
            json_data = json.loads(js)
            return Response(data=json_data)
        elif request.GET['user_group'] == 'editor':
            userList = []
            users = db.myapp_customuser.find({"user_group": 'Editor'})
            for i in users:
                myDict = {"first_name": i["first_name"], "last_name": i["last_name"],
                          "date_joined": i["date_joined"],
                          "user_group": i['user_group'], "id": i["id"]}
                userList.append(myDict)
            js = json.dumps(userList, default=json_util.default)
            json_data = json.loads(js)
            return Response(data=json_data)
        elif request.GET['user_group'] == 'language':
            userList = []
            users = db.myapp_customuser.find({"user_group": 'Language Approver'})
            for i in users:
                myDict = {"first_name": i["first_name"], "last_name": i["last_name"],
                          "date_joined": i["date_joined"],
                          "user_group": i['user_group'], "id": i["id"]}
                userList.append(myDict)
            js = json.dumps(userList, default=json_util.default)
            json_data = json.loads(js)
            return Response(data=json_data)
        elif request.GET['user_group'] == 'graphics':
            userList = []
            users = db.myapp_customuser.find({"user_group": 'Graphics Team'})
            for i in users:
                myDict = {"first_name": i["first_name"], "last_name": i["last_name"],
                          "date_joined": i["date_joined"],
                          "user_group": i['user_group'], "id": i["id"]}
                userList.append(myDict)
            js = json.dumps(userList, default=json_util.default)
            json_data = json.loads(js)
            return Response(data=json_data)
        elif request.GET['user_group'] == 'uksales':
            userList = []
            users = db.myapp_customuser.find({"user_group": 'UK Sales'})
            for i in users:
                myDict = {"first_name": i["first_name"], "last_name": i["last_name"],
                          "date_joined": i["date_joined"],
                          "user_group": i['user_group'], "id": i["id"]}
                userList.append(myDict)
            js = json.dumps(userList, default=json_util.default)
            json_data = json.loads(js)
            return Response(data=json_data)


@api_view(['GET'])
def FactorydropDown(request):
    if request.method == 'GET':
        myList = []
        try:
            factory = list(db.factory.find({},{"location":1,"_id":0}))
            for i in factory:
                myList.append(i['location'])
            return Response(data=myList,status=201)
        except:
            return Response(data=[],status=201)
@api_view(['GET'])
def testGrid(request):
    if request.method == 'GET':
        myList1 = []
        myList2 = []
        myList3 = []
        duplicate = []
        mydict = {}
        mydict1 = {}
        key = []
        langs = ['']
        grid = list(db.grids.find({"varient":"var003"}))
        lan =  grid[0]['version'][0]['grid']
        print(lan)
        j = {}
        for i in lan:
            for lang in i:
                langs.append(lang)
            j = i.values()
            for k in j:
                # key = k.keys()
                for val in k:
                    if val not in key:
                        key.append(val)
                myList2.append(k.values())
        myList2.insert(0,key)
        # print(myList2)
        new_list = list(zip(*myList2))
        return Response(data={"data":new_list,"lanuages":langs})
        # print(new_list)

varient= openapi.Parameter('varient', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(method='GET', manual_parameters=[varient])
@api_view(['GET'])
def GridHistory(request):
    if request.method == 'GET':
        var = request.GET["varient"]
        history = list(db.grid_history.find({"varient":var}).sort("_id",-1))
        js = json.dumps(history, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)


@api_view(['GET'])
def GraphData(request):
    if request.method == 'GET':
        # module wise count
        language = db.language.find().count()
        master = db.master_code.find().count()
        countries = db.country.find().count()
        factory = db.factory.find().count()
        requirement = db.additional_requirement.find().count()
        asset= db.myapp_asset.find().count()
        blends = db.blend.find().count()
        translation = 0

        # user data
        admin = db.myapp_customuser.find({"user_group":"Admin"}).count()
        sales = db.myapp_customuser.find({"user_group":"UK Sales"}).count()
        lang = db.myapp_customuser.find({"user_group":"Language Approver"}).count()
        viewers = db.myapp_customuser.find({"user_group":"Viewer"}).count()
        editor = db.myapp_customuser.find({"user_group":"Editor"}).count()
        graphic = db.myapp_customuser.find({"user_group":"Graphics Team"}).count()

        # grid data
        certified = db.log_grid_module.find({"flag":1,"status":"Certified"}).count()
        published = db.log_grid_module.find({"flag":1,"status":"Published"}).count()
        created =db.log_grid_module.find({"flag":1,"status":"Created"}).count()
        modified = db.log_grid_module.find({"flag":1,"status":"Modified"}).count()
        duplicated = db.log_grid_module.find({"flag":1,"status":"Duplicated"}).count()
        approved = db.log_grid_module.find({"flag":1,"status":"Approved"}).count()
        rejected = db.log_grid_module.find({"flag":1,"status":"Rejected"}).count()
        design = db.log_grid_module.find({"flag": 1, "status": "Design Completed"}).count()
        artwork = db.log_grid_module.find({"flag": 1, "status": "Artwork Completed"}).count()
        acknowledged = db.log_grid_module.find({"flag": 1, "status": 'Acknowledged'}).count()

        try:
            translations = list(db.translations.find())
            for i in translations:
                translation += len(i['translation'])
                print(translation)
        except:
            translation = 0

        module_data = [
            {"name": "Languages", "numbers": language},
            {"name": "Master Codes", "numbers": master},
            {"name": "Countries", "numbers": countries},
            {"name": "Factories", "numbers": factory},
            {"name": "Requirements", "numbers": requirement},
            {"name": "Blends","numbers": blends},
            {"name": "Assets", "numbers":asset},
            {"name": "Translations", "numbers":translation},
        ]
        user_data = [admin,editor,viewers,lang,sales,graphic]
        grid_data = [created, approved,rejected,certified,published,modified,duplicated,design,artwork,acknowledged]
        data = {"module":module_data,"userdata":user_data,"grid":grid_data}
        return Response(data=data)


@api_view(['POST'])
def AddComment(request):
    if request.method == 'POST':
        history = db.grid_history.insert_one(
            {"user": request.data['user'], "varient": request.data['varient'],
             "date": datetime.datetime.now(),
             "action": request.data['comment']})
        return Response(data = history.acknowledged)


from .gridview import AddLanguage
@api_view(['POST'])
def GridNewLanguage(request):
    if request.method == 'POST':
        newGrid =  AddLanguage(request)
    return Response(data=newGrid,status=200)


from .gridview import AddGridRequirement,check_present
@api_view(['POST'])
def GridNewRequirement(request):
    if request.method == 'POST':
        data = request.data['grid']
        requirement = request.data['requirement']
        if check_present(requirement, data):
            return Response(data="Requirement already present in grid",status=400)
        newGrid = AddGridRequirement(request)
    return Response(data=newGrid,status=200)

@api_view(['GET',])
def get_fonts(request):
    if request.method == 'GET':
        fontlist = []
        languages = list(db.language.find({}).sort("code",1))
        for i in languages:
            if db.myapp_fonts.find({"language":i['code']}).count() > 0:
                font = list(db.myapp_fonts.find({"language":i['code']}))
                dict = {'language':i['code'],"name":font[0]['name'],"file":font[0]['font']}
                fontlist.append(dict)
            else:
                dict = {'language': i['code'], "name":'', "file": ''}
                fontlist.append(dict)
        js = json.dumps(fontlist, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)

from .serializers import UpdateUserSerializer
@api_view(['POST','GET'])
def UpdateUser(request):
    user = username(request.auth)
    if request.method == 'GET':
        userdetails = list(db.myapp_customuser.find({"id":user['id']},{"password":0}))
        js = json.dumps(userdetails, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data, status=200)
    if request.method == 'POST':
        serializer = UpdateUserSerializer(data=request.data)
        if serializer.is_valid():
            userdetails = db.myapp_customuser.update_one({"id": user['id']},{"$set":{"first_name": serializer.data['firstname'],
                                    "username":serializer.data['username'],"last_name":serializer.data['lastname']}})
            return Response(data=userdetails.acknowledged,status=201)
        else:
            return Response(serializer.errors)
@api_view(['GET'])
def CustomConditonDropdown(request):
    if request.method=="GET":
        language = list(db.language.find())
        country  = list(db.country.find())
        legalname= list(db.legal_name.find())
        factory  = list(db.factory.find())
        requirement = list(db.additional_requirement.find({"type":"Translation-ID"}))
        blend    = [{'label':"black tea","value":"black tea"},{"label":"green tea","value":"green tea"},{"label":"herbal tea","value":"herbal tea"},{"label":"natural benefit","value":"natural benefit"}]
        type     = [{"label":"standard","value":"standard"},{"label":"promo pack","value":"promo pack"},
                    {"label":"selection pack","value":"selection pack"}]
        Range    = [{'label':"black tea","value":"black tea"},{"label":"green tea","value":"green tea"},{"label":"herbal tea","value":"herbal tea"},{"label":"natural benefit","value":"natural benefit"}]
        teaform  = list(db.tea_form.find())
        no_of_teabag = list(db.no_of_tea_bag.find())
        category   = [{"label":"loose tea","value":"loose tea"},{"label":"tea bag","value":"tea bag"}]
        languages  = []
        countries  = []
        legalnames = []
        requirements =[]
        factories  = []
        teaforms    = []
        no_of_teabags = []
        try:
            for i in language:
                mydict = {"label":i['name'],"value":i['code']}
                languages.append(mydict)
        except:pass
        try:
            for c in country:
                mydict = {"label": c['name'], "value": c['code']}
                countries.append(mydict)
        except:pass
        try:
            for l in legalname:
                legalnames.append({"label": l["name"], "value": l['translation']})
        except:pass
        try:
            for r in requirement:
                requirements.append({"label": r['requirement'], "value": r['requirement']})
        except:
            pass
        try:
            for k in factory:
                factories.append(k["location"])
        except:pass
        try:
            for t in teaform:
                teaforms.append({"label": t["tea_form"], "value": t['tea_form']})
        except:pass
        try:
            for n in no_of_teabag:
                no_of_teabags.append({"label": n["no_of_teabags"], "value": n['no_of_teabags']})
        except:pass
        return Response(data={"no_of_teabag": no_of_teabags, "blend": blend,"type":type,"requirement":requirements,
                              "tea_form": teaforms,"language":languages,"category":category,"range":Range,
                              "legal_name": legalnames, "factory": factories, "country": countries})

class GridCommentAndFileAttachments(viewsets.ModelViewSet):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AttachmentSerializer
    queryset = Attachment
    def create(self, request):
        querysets = Attachment
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                asset = Attachment.objects.create(
                    comment=request.POST['comment'],
                    user=request.POST['user'],
                    varient=request.POST['varient'],
                    attachment=request.FILES['attachment'],
                    datetime=datetime.datetime.now()
                )
            except KeyError:
                asset = Attachment.objects.create(
                    comment=request.POST['comment'],
                    user=request.POST['user'],
                    varient=request.POST['varient'],
                    datetime=datetime.datetime.now()
                )
            history = db.grid_history.insert_one(
            {"user": request.POST['user'], "varient": request.POST['varient'],
             "date":datetime.datetime.now(),
             "action": "added comment" + request.POST['comment']})
            return Response(serializer.data, status=204)
        else:
            return Response(serializer.errors, status=400)

@api_view(['POST'])
def gridCommentAttachmentView(request):
    if request.method == 'POST':
        request.data['varient']
        try:
            commets = list(db.myapp_attachment.find({"varient":request.data['varient']}))
            js = json.dumps(commets, default=json_util.default)
            json_data = json.loads(js)
            return Response(data=json_data)
        except Exception as e:
            print("test",e)
            return Response(status=400)


@api_view(['GET'])
def TaskGraphData(request):
    if request.method == 'GET':
        user = username(request.auth)
        user_group = user['user_group']
        pending =db.pending_task.find({"usergroup":user_group}).count()
        completed = db.completed_task.find({"usergroup": user_group}).count()
        data = [pending,completed]
        return Response(data=data)
@swagger_auto_schema(method='POST', request_body=ChatSerializer)
@api_view(['GET','POST','PUT'])
def Chat(request):
    if request.method == 'POST':
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            try:
                if db.chat.find({"varient":request.data['varient']}).count() > 0:
                    chat = db.chat.update_one({"varient":request.data['varient']},{"$push":{"chat":request.data['message'],"user":request.data['user'],"time":datetime.datetime.now}})
                    return Response(data=chat.matchCount)
                else:
                    chat = db.chat.insert_one({"varient":varient,"chat":request.data['chat'],"user":request.data['user'],"time":datetime.datetime.now})
                    return Response(data=chat.acnowledged)
            except Exception as e:
                return Response(data=e,status=400)
        else:
            return Response(serializer.errors, status=400)
import os
class GridDocumentAttachments(viewsets.ModelViewSet):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = DocumentSerializer
    queryset = Document
    def create(self, request):
        user = username(request.auth)
        querysets = Document
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                document = Document.objects.create(
                    user=user['name'],
                    varient=request.POST['varient'],
                    attachment=request.FILES['attachment'],
                    datetime=datetime.datetime.now(tz=timezone.utc)
                )
                history = db.grid_history.insert_one(
                    {"user":user[0]['name'], "varient": request.POST['varient'],
                     "date": datetime.datetime.now(),
                     "action":"test atttachment file"})
            except KeyError:
               pass

            return Response(serializer.data, status=204)
        else:
            return Response(serializer.errors, status=400)

varient= openapi.Parameter('varient', openapi.IN_QUERY, type=openapi.TYPE_STRING)
id= openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_STRING)
@swagger_auto_schema(method='GET', manual_parameters=[varient])
@swagger_auto_schema(method='DELETE', manual_parameters=[varient])
@api_view(['GET','DELETE'])
def ViewDocuments(request):
    if request.method == 'GET':
        my_list = []
        documents = list(db.myapp_document.find({"varient": request.GET['varient']}))
        for i in documents:
            file_name = os.path.basename(i['attachment'])
            link = "http://" + request.get_host() + "/media/" + i['attachment']
            mydict = {"file":link,"name":file_name,"id":i["_id"],"user":i["user"],"date":i['datetime']}
            my_list.append(mydict)
        js = json.dumps(my_list, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)
    if request.method == 'DELETE':
        id = request.GET['id']
        print(id)
        delete = db.myapp_document.delete_one({"_id":ObjectId(id)})
        try:
            if delete.deleted_count > 0:
                return Response(data="deleted",status=200)
            else:
                return Response(data='no document found',status=202)
        except:
            return Response(data='error',status=400)

from .reports import serach_task
varient = openapi.Parameter('varient', openapi.IN_QUERY, description="varient code ", type=openapi.TYPE_STRING,default='')
item = openapi.Parameter('item', openapi.IN_QUERY, description="item number", type=openapi.TYPE_INTEGER,default='')
fromdate = openapi.Parameter('fromdate', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
todate = openapi.Parameter('todate', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
table = openapi.Parameter('type', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_INTEGER,default='')
usergroup = openapi.Parameter('usergroup', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(method='post', manual_parameters=[varient,item,fromdate,todate,table,usergroup])
@api_view(['POST'])
def task_list_search(request):
    if request.method == 'POST':
        data = serach_task(request)
        return Response(data=data)

value = openapi.Parameter('value', openapi.IN_QUERY, description="search input value", type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(method='post', manual_parameters=[value])
@api_view(['POST'])
def search_user(request):
    if request.method == 'POST':
        search = request.GET['value']
        search_result = []
        if search != '':
            data = list(db.myapp_customuser.find({"first_name":{"$regex":search}}))
            print(data)
            for i in data:
                name = i['first_name']+ " "+i['last_name']
                avatar =i['first_name'][0] + i['last_name'][0]
                my_dict = {"user":name,"id":i['id'],"avatar":avatar}
                search_result.append(my_dict)
            js = json.dumps(search_result, default=json_util.default)
            json_data = json.loads(js)
            return Response(data=json_data)
        else:
            return Response(data=[])

from .userDetails import AuthorizeAdmin
@api_view(['GET'])
def CheckAuthorizedAdmin(request):
    if request.method == 'GET':
        authorized = AuthorizeAdmin(request.auth)
        return Response(data=authorized)

from .userDetails import AuthorizeUser
@api_view(['GET'])
def CheckAuthorized(request):
    if request.method == 'GET':
        authorized = AuthorizeUser(request.auth)
        return Response(data=authorized)

#api for exporting translation for specific master code id
from .excel import MaterCodeTranslationExport
@api_view(['POST'])
def MasterCodeTranslations(request):
    if request.method == 'POST':
        translations = MaterCodeTranslationExport(request)
        server = "http://" + request.get_host() + "/media/files/masterCode_translations.xlsx"
        return Response({"file": server})


from .customCondition import CountryCustomConditonView
class CountryBasedCustomConditionView(APIView):
    def get(self, request, country, format=None):
        country = country
        pipeline = [
            {"$unwind": "$statement"},
            {"$match": {"$and":[{"statement.category": "country"},{ "statement.value": country}]}},
            {"$project": {"_id": 1}}
        ]
        data = list(db.custom_condition.aggregate(pipeline))
        ob_ids = [i['_id'] for i in data ]
        conditions = list(db.custom_condition.find({"_id":{"$in":ob_ids}}))
        js = json.dumps(conditions, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)


lan = openapi.Parameter('lan', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
trans_id = openapi.Parameter('trans_id', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(method='post', manual_parameters=[lan,trans_id])
@api_view(['POST'])
def get_traslationVersions(request):
    if request.method == 'POST':
        lan = request.GET['lan']
        trans_id = request.GET['trans_id']
        pipeline = [
            {
                "$match": {
                    "language": lan
                }
            },
            {
                "$group": {
                    "_id": {
                        "field1": "$translation.trans_id",
                    },
                    "documents": {"$push": "$traslation.versions"},
                    "count": {"$sum": 1}
                }
            },
            {
                "$match": {
                    "count": {"$gte": 1}
                }
            }
        ]
        data = list(db.translations.aggregate(pipeline))
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)

from .excel import MaterCodeTranslationExport
@api_view(['POST'])
def MasterCodeTranslations(request):
    if request.method == 'POST':
        translations = MaterCodeTranslationExport(request)
        server = "http://" + request.get_host() + "/media/files/masterCode_translations.xlsx"
        return Response({"file": server})


from .serializers import BlendRequirementSerializer
from .history import BlendRequirementHistory

blend = openapi.Parameter('blend', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(method='post', request_body=BlendRequirementSerializer)
@swagger_auto_schema(method='get', manual_parameters=[blend])
@swagger_auto_schema(method='put', request_body=BlendRequirementSerializer)
@swagger_auto_schema(method='delete', manual_parameters=[id])
@api_view(['POST','GET','DELETE','PUT'])
def blend_requirements(request):
    name = username(request.auth)
    log_no = logNo("blend_requirement")
    if request.method == 'GET':
        blend_id = request.GET['blend']
        blend_query = {"_id": ObjectId(blend_id)}
        data = db.blend_requirements.find({"blend": blend_id})
        requirements = []
        for i in data:
            if i['type'] == 'Translation-ID':
                text = db.master_code.find({"id": i['value']})
                dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],"code":i['value'],
                               "value": text[0]['id'] + "-" + text[0]['text'], "country": i['country'],"category":i['category']}
                requirements.append(dict_values)
            elif i['type'] == 'Asset':
                image = db.myapp_asset.find({'id': int(i['value'])})
                dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],
                               "value": image[0]['name'],"code":i['value'],
                               "photo": "http://" + request.get_host() + "/media/" + image[0]['photo'],
                               "country": i['country'],"category":i['category']}
                requirements.append(dict_values)
            else:
                dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'], "value": i['value'],
                               "country": i['country'],"category":i['category']}
                requirements.append(dict_values)
        js = json.dumps(requirements, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)
    if request.method =='POST':
        serializer  = BlendRequirementSerializer(data=request.data)
        if serializer.is_valid():
            post = db.blend_requirements.insert_one(serializer.data)
            if post.acknowledged:
                data = db.log_input_module.insert_one({"user": name['name'],
                                                       "action": "added new blend requirement " + request.data[
                                                           'requirement'],
                                                       "blend":request.data['blend'],
                                                       "module": "blend_requirement", "date": datetime.datetime.utcnow(),
                                                       "log_no": log_no})
                return Response(status=200,data={"message":"Requirement added "})
            else:
               return Response(status=200,data={"message":"Faliled adding requirement"})
        else:
            return Response(status=400,data=serializer.errors)
    if request.method == 'PUT':
        serializer = BlendRequirementSerializer(data=request.data)
        if serializer.is_valid():
            blend = list(db.blend_requirements.find({"_id": ObjectId(request.data['_id'])}))
            put = db.blend_requirements.update_one({"_id":ObjectId(request.data['_id'])},{"$set":{
                "requirement":request.data['requirement'],"type":request.data['type'],"value":request.data['value'],
                "blend":request.data['blend'],"country":request.data['country'],"category":request.data['category']
            }})
            if put.acknowledged:
                action = BlendRequirementHistory(request.data,blend[0])
                data = db.log_input_module.insert_one({"user": name['name'],
                                                       "action": action,
                                                       "blend": request.data['blend'],
                                                       "module": "blend_requirement",
                                                       "date": datetime.datetime.utcnow(),
                                                       "log_no": log_no})
                return Response(status=200, data={"message": "Requirement updated "})
            else:
                return Response(status=200, data={"message": "Failed updating requirement"})
        else:
            return Response(status=400, data=serializer.errors)
    if request.method == 'DELETE':
        ID = request.data['id']
        for i in ID:
            blend = list(db.blend_requirements.find({"_id": ObjectId(i)}))
            delete = db.blend_requirements.delete_one({"_id":ObjectId(i)})
            data = db.log_input_module.insert_one({"user": name['name'],
                                                   "action":"deleted requirement "+ blend[0]['requirement'],
                                                   "blend": blend[0]['blend'],
                                                   "module": "blend_requirement",
                                                   "date": datetime.datetime.utcnow(),
                                                   "log_no": log_no})
        if delete .acknowledged:
            return Response(status=200, data={"message": "Requirement Deleted"})
        else:
            return Response(status=200, data={"message": "Failed deleting requirement"})
from .models import ArtWorks
from .serializers import ArtWorkSerializer
class ArtWorkViewSet(viewsets.ModelViewSet):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser)
    queryset = ArtWorks.objects.all()
    serializer_class = ArtWorkSerializer
    def create(self,request):
        serializer = ArtWorkSerializer(data=request.data)
        if serializer.is_valid():
            asset = ArtWorks.objects.create(
                varient=request.POST['varient'],
                job=request.POST['job'],
                item=request.POST['item'],
                attachment=request.FILES['attachment']
                )
            return Response(serializer.data, status=204)
        else:
            return Response(serializer.errors, status=400)

var = openapi.Parameter('var', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(method='get', manual_parameters=[var])
@api_view(['GET'])
def retrieve_artwork(request):
    var = request.GET['var']
    if db.myapp_artworks.find({"varient":var}).count() >0:
        data = db.myapp_artworks.find({"varient":var})
        attachment = data[0]['attachment']
        return Response(data={"status":True,"file": "http://" + request.get_host() + "/media/"+attachment})
    return Response(data={"status":False})

from .updatedValue import get_updated_values
from .serializers import ItemNoSerializers
from .history import itemNumberHistory
@swagger_auto_schema(method='post', request_body=ItemNoSerializers)
@swagger_auto_schema(method='put', request_body=ItemNoSerializers)
@swagger_auto_schema(method='delete', manual_parameters=[id])
@api_view(['POST','GET','DELETE','PUT'])
def ItemNoModule(request):
    name = username(request.auth)
    if request.method == 'GET':
        documents = list(db.itemNo.find({}))
        js = json.dumps(documents, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)
    if request.method == 'POST':
        log_no = logNo("itemNo")
        serializer = ItemNoSerializers(data=request.data)
        if serializer.is_valid():
            if db.itemNo.find({"item":serializer.data['item']}).count() >0:
                return Response(data={"message": "Item number already present "})
            else:
                data = db.itemNo.insert_one(serializer.data)
                log = db.log_input_module.insert_one(
                    {"user": name['name'], "action": "added new item number " + str(serializer.data['item']),
                     "module": "itemNo", "date": datetime.datetime.utcnow(), "log_no": log_no})
                if data.acknowledged:
                    return Response(data={"message":"Item number added"})
                else:
                    return Response(data={"message":"Item number adding failed"})
        else:
            return Response(data=serializer.errors,status=400)
    if request.method =='PUT':
        log_no = logNo("itemNo")
        serializer = ItemNoSerializers(data=request.data)
        if serializer.is_valid():
            noTeabag = ''
            if (serializer.data['noTeabag']):
                noTeabag = serializer.data['noTeabag']
            else:
                noTeabag= ''
            item = list(db.itemNo.find({"_id": ObjectId(request.data['id'])}))
            reg =  db.registrationNo.update({"item": item[0]['item']}, {"$set": {
                "item": request.data['item']}})
            query ={"$set": {
                "item": request.data['item'],
                "blend_name": request.data['blend_name'], "category": request.data['category'],"noTeabag":noTeabag
            }}
            action = itemNumberHistory(request.data,item[0])
            put = db.itemNo.update_one( {"_id": ObjectId(request.data['id'])},query)
            log = db.log_input_module.insert_one(
                {"user": name['name'], "action":action,
                 "module": "itemNo", "date": datetime.datetime.utcnow(), "log_no": log_no})
            if put.acknowledged:
                return Response(status=200, data={"message": "Item number updated "})
            else:
                return Response(status=200, data={"message": "Failed updating Item number"})
        else:
            return Response(data=serializer.errors,status=400)
    if request.method =='DELETE':
        log_no = logNo("itemNo")
        ID = request.data['id']
        for i in ID:
            item = list(db.itemNo.find({"_id": ObjectId(i)}))
            delete = db.itemNo.delete_one({"_id": ObjectId(i)})
            log = db.log_input_module.insert_one(
                {"user": name['name'], "action": "deleted item number:" + str(item[0]['item']),
                 "module": "itemNo", "date": datetime.datetime.utcnow(), "log_no": log_no})
        if delete.acknowledged:
            return Response(status=200, data={"message": "Item number Deleted"})
        else:
            return Response(status=200, data={"message": "Failed deleting Item number"})

from .serializers import RegistrationNoSerializer
from .history import regnumberHistory
item = openapi.Parameter('item', openapi.IN_QUERY, description=" manual param", type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(method='post', request_body=RegistrationNoSerializer)
@swagger_auto_schema(method='put', request_body=RegistrationNoSerializer)
@swagger_auto_schema(method='delete', manual_parameters=[id])
@swagger_auto_schema(method='get', manual_parameters=[item])
@api_view(['POST','GET','DELETE','PUT'])
def RegistrationNo(request):
    name = username(request.auth)
    if request.method=='GET':
        documents = list(db.registrationNo.find({"item": request.GET['item']}))
        js = json.dumps(documents, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)
    if request.method=='POST':
        log_no = logNo("registrationNo")
        serialiser = RegistrationNoSerializer(data=request.data)
        if serialiser.is_valid():
            if db.registrationNo.find({"country":serialiser.data['country'],"item":serialiser.data['item']}).count() >0:
                return Response(data={"message": "Registration number already present for the country"})
            else:
                data = db.registrationNo.insert_one(serialiser.data)
                log = db.log_input_module.insert_one(
                    {"user": name['name'], "action": "Added new registration number " + str(serialiser.data['registration']),
                     "module": "registrationNo","registration": serialiser.data['registration'],"item":str(serialiser.data['item']),"date": datetime.datetime.utcnow(), "log_no": log_no})
                if data.acknowledged:
                    if data.acknowledged:
                        return Response(data={"message": "Registration number added"})
                    else:
                        return Response(data={"message": "Registration number adding failed"})
        else:
            return Response(data=serialiser.errors,status=400)
    if request.method=='PUT':
        log_no = logNo("registrationNo")
        serializer = RegistrationNoSerializer(data=request.data)
        if serializer.is_valid():
            registraion = list(db.registrationNo.find({"_id": ObjectId(request.data['id'])}))
            put = db.registrationNo.update_one({"_id": ObjectId(request.data['id'])}, {"$set": {
                "item": request.data['item'], "country": request.data['country'],
                "registration": request.data['registration'],
            }})
            action = regnumberHistory(request.data,registraion[0])
            log = db.log_input_module.insert_one(
                {"user": name['name'], "action": action,
                 "module": "registrationNo","item":str(serializer.data['item']), "registration": str(serializer.data['registration']),
                 "date": datetime.datetime.utcnow(), "log_no": log_no})
            if put.acknowledged:
                return Response(status=200, data={"message": "Registration number updated "})
            else:
                return Response(status=200, data={"message": "Failed updating Registration Number"})
        else:
            return Response(data=serializer.errors, status=400)

    if request.method=='DELETE':
        log_no = logNo("registrationNo")
        ID = request.data['id']
        for i in ID:
            try:
                name = list(db.registrationNo.find({"_id": ObjectId(i)}))
                delete = db.registrationNo.delete_one({"_id": ObjectId(i)})
                log = db.log_input_module.insert_one(
                    {"user": name['name'], "action": "deleted registration number " + name[0]['registration'],
                     "module": "registrationNo", "item": str(name[0]['item']),
                     "date": datetime.datetime.utcnow(), "log_no": log_no})
            except:
                pass
        if delete.acknowledged:
            return Response(status=200, data={"message": "Registration number Deleted"})
        else:
            return Response(status=200, data={"message": "Registration number deleting failed"})

from .models import SalesReport
from .serializers import SalesReportSerializer
class SalesReportViewSet(viewsets.ModelViewSet):
    parser_classes = [parsers.FormParser, parsers.MultiPartParser, parsers.FileUploadParser]
    queryset = SalesReport.objects.all()
    serializer_class = SalesReportSerializer
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']
    def create(self, request, *args, **kwargs):
        serializer = SalesReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Save the validated data
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)

    def list(self, request, *args, **kwargs):
        varient = request.query_params.get('varient')
        if varient is None:
            return Response({"message": "Varient Code required"}, status=400)
        queryset = SalesReport.objects.filter(varient=varient)
        serializer = SalesReportSerializer(queryset, many=True)
        return Response(serializer.data)

    def delete(self, request, *args, **kwargs):
        varient = request.query_params.get('varient')
        if varient is None:
            return Response({"message": "Varient Code required"}, status=400)
        obj = db.myapp_salesreport.delete_one({"varient":varient})
        if obj.acknowledged:
            return Response(data={"message": "Record deleted successfully"},status=201)
        else:
            return Response(data={"message": "Record deleted successfully"},status=400)

from .excel import ExportReport
@api_view(['POST'])
def get_report(request):
    if request.method == 'POST':
        data = ExportReport(request.data['data'])
        server = "http://"+request.get_host()+"/media/exceltemplates/Report.xlsx"
        return Response({"file":server})


from .serializers import ItemRequirementSerializer
from .history import ItemRequirementHistory
item_no = openapi.Parameter('item_no', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(method='post', request_body=ItemRequirementSerializer)
@swagger_auto_schema(method='get', manual_parameters=[item_no])
@swagger_auto_schema(method='put', request_body=ItemRequirementSerializer)
@swagger_auto_schema(method='delete', manual_parameters=[id])
@api_view(['POST','GET','DELETE','PUT'])
def item_requirements(request):
    name = username(request.auth)
    if request.method == 'GET':
        item_id = request.GET['item_no']
        # item_query = {"_id": ObjectId(item_id)}
        data = db.item_no_requirements.find({"item": item_id})
        requirements = []
        for i in data:
            if i['type'] == 'Translation-ID':
                text = db.master_code.find({"id": i['value']})
                dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],"code":i['value'],
                               "value": text[0]['id'] + "-" + text[0]['text'], "country": i['country']}
                requirements.append(dict_values)
            elif i['type'] == 'Asset':
                image = db.myapp_asset.find({'id': int(i['value'])})
                dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'],
                               "value": image[0]['name'],"code":i['value'],
                               "photo": "http://" + request.get_host() + "/media/" + image[0]['photo'],
                               "country": i['country']}
                requirements.append(dict_values)
            else:
                dict_values = {"_id": i['_id'], "requirement": i['requirement'], "type": i['type'], "value": i['value'],
                               "country": i['country']}
                requirements.append(dict_values)
        js = json.dumps(requirements, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)
    if request.method =='POST':
        serializer = ItemRequirementSerializer(data=request.data)
        if serializer.is_valid():
            post = db.item_no_requirements.insert_one(serializer.data)
            if post.acknowledged:
                log_no = logNo("Item_requirement")
                log = db.log_input_module.insert_one(
                    {"user": name['name'], "action": "added requirement "+serializer.data['requirement'],
                     "module": "Item_requirement", "item": str(serializer.data['item']),
                     "date": datetime.datetime.utcnow(), "log_no": log_no})
                return Response(status=200,data={"message":"Requirement added "})
            else:
               return Response(status=200,data={"message":"Faliled adding requirement"})
        else:
            return Response(status=400,data=serializer.errors)
    if request.method == 'PUT':
        serializer = ItemRequirementSerializer(data=request.data)
        if serializer.is_valid():
            item = list(db.item_no_requirements.find({"_id": ObjectId(request.data['_id'])}))
            put = db.item_no_requirements.update_one({"_id":ObjectId(request.data['_id'])},{"$set":{
                "requirement":request.data['requirement'],"type":request.data['type'],"value":request.data['value'],
                "item":request.data['item'],"country":request.data['country']
            }})
            if put.acknowledged:
                action = ItemRequirementHistory(request.data, item[0])
                log_no = logNo("Item_requirement")
                log = db.log_input_module.insert_one(
                    {"user": name['name'], "action": action,
                     "module": "Item_requirement", "item": str(serializer.data['item']),
                     "date": datetime.datetime.utcnow(), "log_no": log_no})
                return Response(status=200, data={"message": "Requirement updated "})
            else:
                return Response(status=200, data={"message": "Failed updating requirement"})
        else:
            return Response(status=400, data=serializer.errors)
    if request.method == 'DELETE':
        ID = request.data['id']
        for i in ID:
            log_no = logNo("Item_requirement")
            item = list(db.item_no_requirements.find({"_id": ObjectId(i)}))
            delete = db.item_no_requirements.delete_one({"_id":ObjectId(i)})
            log = db.log_input_module.insert_one(
                {"user": name['name'], "action": "deleted requirement "+item[0]['requirement'],
                 "module": "Item_requirement", "item": str(item[0]['item']),
                 "date": datetime.datetime.utcnow(), "log_no": log_no})
        if delete .acknowledged:
            return Response(status=200, data={"message": "Requirement Deleted"})
        else:
            return Response(status=200, data={"message": "Failed deleting requirement"})


from .serializers import GroupedTranslation
@swagger_auto_schema(method='delete', manual_parameters=[id])
@api_view(['POST','GET','DELETE','PUT'])
def groupdeTranslations(request):
    if request.method == 'GET':
        data = list(db.grouped_translation.find())
        js = json.dumps(data, default=json_util.default)
        json_data = json.loads(js)
        return Response(data=json_data)
    if request.method =='POST':
        serializer = GroupedTranslation(data=request.data)
        if serializer.is_valid():
            post = db.grouped_translation.insert_one(serializer.data)
            if post.acknowledged:
                return Response(status=200, data={"message": "grouped translation added"})
            else:
                return Response(status=200, data={"message": "grouped translation adding failed"})
        else:
            return Response(status=400, data=serializer.errors)
    if request.method =='PUT':
        serializer = GroupedTranslation(data=request.data)
        if serializer.is_valid():
            put = db.grouped_translation.update_one({"_id": ObjectId(request.data['_id'])}, {"$set": {
                "requirement": request.data['requirement'], "id": request.data['id'],
                                     }})
            if put.acknowledged:
                return Response(status=200, data={"message": "Grouped translation updated "})
            else:
                return Response(status=200, data={"message": "Falied updating grouped translation"})
        else:
            return Response(status=400, data=serializer.errors)
    if request.method =='DELETE':
        ID = request.data['id']
        for i in ID:
            delete =  db.grouped_translation.delete_one({"_id": ObjectId(i)})
        if delete.acknowledged:
            return Response(status=200, data={"message": "Requirement Deleted"})
        else:
            return Response(status=200, data={"message": "Failed deleting requirement"})


module = openapi.Parameter('module', openapi.IN_QUERY, description="test manual param", type=openapi.TYPE_STRING,default='')
@swagger_auto_schema(method='post', manual_parameters=[module])
@api_view(['POST'])
def deleteModule(request):
    if request.method == 'POST':
        module = request.GET["module"]
        param = request.GET['param']
        if module =="translations":
            delete = db[module].delete_many({"language":param})
            if delete.acknowledged:
                return Response(data="delete success",status=200)
        elif module == 'blend_requirements':
            delete = db[module].delete_many({"blend":param})
            if delete.acknowledged:
                return Response(data="delete success",status=200)
        elif module == 'item_no_requirements':
            delete = db[module].delete_many({"item": str(param)})
            if delete.acknowledged:
                return Response(data="delete success",status=200)
        elif module == 'language':
            delete = db.translations.delete_many({})
            delete = db.language.delete_many({})
            if delete.acknowledged:
                return Response(data="delete success",status=200)
        elif module == 'country':
            delete = db.country.delete_many({})
            delete = db.additional_requirement.update_many({},{"$set":{"country":""}})
            if delete.acknowledged:
                return Response(data="delete success",status=200)
        elif module == 'blend':
            delete = db.blend.delete_many({})
            delete = db.blend_requirements.delete_many({})
            if delete.acknowledged:
                return Response(data="delete success",status=200)
        elif module =='tasklist':
            delete = db.pending_task.delete_many({})
            delete = db.completed_task.delete_many({})
            if delete.acknowledged:
                return Response(data="delete success",status=200)
        elif module == 'itemNo':
            delete = db.itemNo.delete_many({})
            delete = db.item_no_requirements.delete_many({})
            if delete.acknowledged:
                return Response(data="delete success",status=200)
        elif module == 'master_code':
            if db.translations.find().count() > 0:
                return Response(data="Delete canceled master code present in translation module",status=203)
            elif db.item_no_requirements.find().count() > 0:
                delete = db.item_no_requirements.delete_many({})
                delete = db.master_code.delete_many({})
                if delete.acknowledged:
                    return Response(data="delete success",status=200)
            elif db.blend_requirements.find().count()  > 0:
                delete = db.blend_requirements.delete_many({})
                delete = db.master_code.delete_many({})
                if delete.acknowledged:
                    return Response(data="delete success",status=200)
            elif db.legal_name.find().count()  >0:
                return Response(data="Delete canceled master code present in legal name  module",status=203)
            elif db.factory.find().count()  >0:
                return Response(data="Delete canceled master code present in factory module",status=203)
            else:
                delete = db.master_code.delete_many({})
                if delete.acknowledged:
                    return Response(data="delete success",status=200)
        else:
            delete = db[module].delete_many({})
            if delete.acknowledged:
                return Response(data="delete success",status=200)
