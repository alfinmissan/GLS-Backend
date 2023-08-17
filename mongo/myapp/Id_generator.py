import re
from pymongo import MongoClient

from .mastercodedata import masterCodeId

client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema

def translationId(lan):
    try:
        data = db.translations.find({"language": lan})
        for i in data[0]['translation']:
            string = i['trans_id']
        s = [int(s) for s in re.findall(r'-?\d+\.?\d*', string)]
        print(s)
        return lan + str(s[0] + 1)
    except:
        return lan + str(0)
def versionId(var):
    try:
        data = list(db.grids.find({"varient": var}, {'_id': 0, "version": 1}))
        for i in data:
            for id in i['version']:
                print(id)
                v_id = id['v_no']
        v_id = v_id + 1
        return v_id
    except Exception as e:
        return e

def incr_chr(c):
    return chr(ord(c) + 1) if c != 'Z' else 'A'
def incr_str(s):
    lpart = s.rstrip('Z')
    num_replacements = len(s) - len(lpart)
    new_s = lpart[:-1] + incr_chr(lpart[-1]) if lpart else 'A'
    new_s += 'A' * num_replacements
    return new_s
def transVersionId(lan,master_id):
    data = list(db.translations.find({"language":lan,"translation.master_id":master_id}))
    for i in data[0]['translation']:
        if i['master_id'] == master_id:
            for j in i['versions']:
                trn_id = j['tran_id']
            try:
                if int(trn_id[-1]) or int(trn_id[-1]) ==0:
                    trn_id = trn_id + 'a'
            except ValueError:
                trn_id = incr_str(trn_id)
    print(trn_id)
    return trn_id


def transVersion(lan, master_id):
    data = list(db.translations.find({"language": lan, "translation.master_id": master_id}))
    for i in data[0]['translation']:
        if i['master_id'] == master_id:
            for j in i['versions']:
                trn_id = j['version']
    return trn_id + 1

def grid_log_id(var):
    data = list(db.log_grid_module.find({"varient":var}))
    try:
        for i in data:
            log = i['log'] + 1
        return log
    except:
        log = 0
        return log

def logNo(module):
    data = list(db.log_input_module.find({"module":module}))
    try:
        for i in data:
            no = i['log_no'] + 1
        return no
    except:
        log_no = 0
        return log_no

def subtranslation_id(master_id):
    start_with_integer = master_id  # Example: Find documents where "id" starts with 10

    # Construct the regular expression pattern
    pattern = re.compile(r'^{}[a-zA-Z]*$'.format(start_with_integer))
    data = list(db.master_code.find({"id": {"$regex": pattern}}, {"_id": 0, "id": 1}).sort("id", 1))
    print(data)
    forid = data[len(data) - 1]
    master_id = forid['id']
    print(master_id)
    try:
        if int(master_id):
            id = str(master_id) + 'a'
    except:
        id = incr_str(master_id)
    print(id)
    return str(id)


def master_Traslation_import_id(request):
        data = db.master_code.find({"text": request})
        for i in data:
            if i['text'] == request:
                res = {'id':i['id'],"value":True}
                return res
            else:
                res = {"value": False}
        return res

def GridVersion(var):
    data = list(db.grids.find({"varient":var}))
    leng = len(data[0]['version']) + 1
    print(leng)
    return leng


