from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('localhost',27017)
print("connection success",client)
db = client.mongodbSchema

def CustomCondition(data,lan):
    ranges = data['range']
    # print(ranges)
    category = data['category']
    country = data['countries']
    factory = data['factory']['value']
    no_of_bags = data['no_of_bags']
    # blends = data['blends']
    try:
        legalName = data['legal_name']
    except KeyError:
        legalName = data['legalname']
    type = data['type']
    teaform = data['tea_form']
    output = ''
    mydict = {}
    conditions = list(db.custom_condition.find({"state":True}))
    for c in conditions:
        # print(i)
        subLogic = c['subLogic']
        mainLogic = c['mainLogc']
        statements= c['statement']
        output = c['output']
        status = ''
        isTrue = ''
        language = ''
        setFirst =''
        setSecond = ''
        if len(mainLogic) > 1:
            for i in range(len(subLogic)):
                status = ''
                for statement in statements[i]:
                    if statement['category'] == 'category':
                        if statement['condition'] == "is":
                            if statement['value'] == category:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != category:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'language':
                        if statement['condition'] == "is":
                            if statement['value'] == lan:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != lan:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'blend':
                        if statement['condition'] == "is":
                            if statement['value'] == ranges:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != ranges:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'no_of_bags':
                        if statement['condition'] == "is":
                            if statement['value'] == no_of_bags:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != no_of_bags:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'legal_name':
                        if statement['condition'] == "is":
                            if statement['value'] == legalName:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != legalName:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'type':
                        if statement['condition'] == "is":
                            if statement['value'] == type:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != type:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'tea_form':
                        if statement['condition'] == "is":
                            if statement['value'] == teaform:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != teaform:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'factory':
                        if statement['condition'] == "is":
                            if statement['value'] == factory:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != factory:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'country':
                        if statement['condition'] == "is":
                            if country.count(statement['value']) > 0:
                                print("test",subLogic[i])
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if country.count(statement['value']) < 0:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                setSecond = setFirst
                setFirst = status
                # print(status,c['name'])
                if setSecond != '':
                    if mainLogic[i-1] == 'and':
                        # print(mainLogic[i-1],setFirst,setSecond)
                        isTrue = checkIsTrue(setFirst,setSecond)
                    elif mainLogic[i-1] == 'or':
                        isTrue = checkIsNotTrue(setFirst,setSecond)
        elif len(subLogic) > 0:
            for i in range(len(subLogic)):
                for statement in statements[i]:
                    if statement['category']=='category':
                        if statement['condition'] == "is":
                            if statement['value'] == category:
                                status = checkIs(subLogic[i],status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        else:
                            if statement['category'] != category:
                                pass
                            else:
                                pass
                    if statement['category'] == 'language':
                        if statement['condition'] == "is":
                            if statement['value'] == lan:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != lan:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'blend':
                        if statement['condition'] == "is":
                            if statement['value'] == ranges:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != ranges:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'no_of_bags':
                        if statement['condition'] == "is":
                            if statement['value'] == no_of_bags:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != no_of_bags:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'legal_name':
                        if statement['condition'] == "is":
                            if statement['value'] == legalName:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != legalName:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'type':
                        if statement['condition'] == "is":
                            if statement['value'] == type:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != type:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'tea_form':
                        if statement['condition'] == "is":
                            if statement['value'] == teaform:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != teaform:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'factory':
                        if statement['condition'] == "is":
                            if statement['value'] == factory:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if statement['value'] != factory:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                    if statement['category'] == 'country':
                        if statement['condition'] == "is":
                            if country.count(statement['value']) > 0:
                                status = checkIs(subLogic[i], status)
                            else:
                                status = checkIsNot(subLogic[i], status)
                        elif statement['condition'] == "not":
                            if country.count(statement['value']) < 0:
                                status = checkIs(subLogic[i], status)
                                print(status)
                            else:
                                status = checkIsNot(subLogic[i], status)
            isTrue = status
        else:
            for statement in statements[0]:
                if statement['category'] == 'category':
                    if statement['condition'] == "is":
                        if statement['value'] == category:
                            status = True
                        else:
                            status = False
                    elif statement['condition'] == "not":
                        if statement['value'] != category:
                            status = True
                        else:
                            status = False
                if statement['category'] == 'language':
                    if statement['condition'] == "is":
                        if statement['value'] == lan:
                            status = True
                        else:
                            status = False
                    elif statement['condition'] == "not":
                        if statement['value'] != lan:
                            status = True
                        else:
                            status = False
                if statement['category'] == 'blend':
                    if statement['condition'] == "is":
                        if statement['value'] == ranges:
                            status = True
                        else:
                            status = False
                    elif statement['condition'] == "not":
                        if statement['value'] != ranges:
                            status = True
                        else:
                            status = False
                if statement['category'] == 'no_of_bags':
                    if statement['condition'] == "is":
                        if statement['value'] == no_of_bags:
                            status = True
                        else:
                            status = False
                    elif statement['condition'] == "not":
                        if statement['value'] != no_of_bags:
                            status = True
                        else:
                            status = False
                if statement['category'] == 'legal_name':
                    if statement['condition'] == "is":
                        if statement['value'] == legalName:
                            status = True
                        else:
                            status = False
                    elif statement['condition'] == "not":
                        if statement['value'] != legalName:
                            status = True
                        else:
                            status = False
                if statement['category'] == 'type':
                    if statement['condition'] == "is":
                        if statement['value'] == type:
                            status = True
                        else:
                            status = False
                    elif statement['condition'] == "not":
                        if statement['value'] != type:
                            status = True
                        else:
                            status = False
                if statement['category'] == 'tea_form':
                    if statement['condition'] == "is":
                        if statement['value'] == teaform:
                            status = True
                        else:
                            status = False
                    elif statement['condition'] == "not":
                        if statement['value'] != teaform:
                            status = True
                        else:
                            status = False
                if statement['category'] == 'factory':
                    if statement['condition'] == "is":
                        if statement['value'] == factory:
                            status = True
                        else:
                            status = False
                    elif statement['condition'] == "not":
                        if statement['value'] != factory:
                            status = True
                        else:
                            status = False
                if statement['category'] == 'country':
                    if statement['condition'] == "is":
                        if country.count(statement['value']) > 0:
                            status = True
                        else:
                            status = False
                    elif statement['condition'] == "not":
                        if country.count(statement['value']) < 0:
                            status = True
                        else:
                            status = False
            isTrue = status
        if isTrue == True:
            mydict[output['requirement']] = output['value']
        else:
            pass
    # print(mydict)
    return mydict


def checkIs(logic,status):
    if logic == 'and' and status == True:
        status = True
    elif logic == 'and' and status == False:
        status = False
    elif logic == 'or' and status == True:
        status = True
    elif logic == 'or' and status == False:
        status = True
    elif status == '':
        status = True
    elif logic == False:
        status = True
    return status
def checkIsNot(logic,status):
    if logic == 'and' and status == True:
        status = False
    elif logic == 'and' and status == False:
        status = False
    elif logic == 'or' and status == True:
        status = True
    elif logic == 'or' and status == False:
        status = False
    elif status == '':
        status = False
    elif logic == False:
        status = False
    return status

def checkIsTrue(isTrue,status):
    if isTrue == True and status == True:
        isTrue = True
    elif isTrue == True and status == False:
        isTrue = False
    if isTrue == False and status == True:
        isTrue = False
    elif isTrue == False and status == False:
        isTrue = False
    elif isTrue == '' and  status == True:
        isTrue = True
    elif isTrue == '' and  status == False:
        isTrue = True
    return isTrue
def checkIsNotTrue(isTrue,status):
    if isTrue == True or status == True:
        isTrue = True
    elif isTrue == True or status == False:
        isTrue = True
    if isTrue == False or status == True:
        isTrue = True
    elif isTrue == False or status == False:
        isTrue = False
    elif isTrue == '' or status == True:
        isTrue = True
    elif isTrue == '' or  status == False:
        isTrue = False
    return isTrue



class CountryCustomConditonView():

    def __init__(self, country):
        self.country = country
    def find_condition(self):
        print(self.country)
        condition = db.custom_condition.aggregate({"$unwind":"$statement"},
                                      {"$match":{"statement.category":"country","statement.value":"ES"}},
                                      {"$project":{ "_id":1, "matched_document":"$$ROOT"}})
        # print(conditions)