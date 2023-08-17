from pymongo import MongoClient
from bson import ObjectId
from .customCondition import CustomCondition
client = MongoClient('localhost',27017)
db = client.mongodbSchema


def BasicRequirement(request):
    # print(request)
    dicts = {}
    for i in request:
        dicts[i['requirement']] = ''
    return dicts
def AdditionalRequirement(request):
    data = db.additional_requirement.find({"country": {"$in":request}})
    dicts = {}
    for i in data:
        dicts[i['requirement']] = ''
    return dicts
def get_country_requirements(name):
    data = list(db.additional_requirement.find({"country": {"$in": [name]}, "static": True}))
    return data
def get_country_additional_requirements(name):
    data = list(db.additional_requirement.find({"country": {"$in": [name]}, "static": False}))
    return data

def BlendReqAdd(blends,countries,category):
    dicts = {}
    for i in blends:
        requirements = list(db.blend_requirements.find({"blend":i['value']['$oid'],"category":category}))
        for j in requirements:
            if any(elem in countries for elem in j['country']):
                dicts[j['requirement']+"-"+i['label']] =''
    return dicts
def Gridgenerator(Grid,host):
    static = {}
    groupedtranslation = {"The word Ingredients":[], "Net Weight":[],"Brew for 5minutes (HERBALS)":[],"Ingredients":[],
                          "Packing Date":[],"Brewing Instructions":[],"Storage Condition":[]}
    languageList = []
    language_requirenents = {}
    grid = []
    blends = Grid['blends']
    weight = Grid["weight"]
    factory = Grid['factory']
    blendsValues = ''
    translation_values = {}
    # print(Grid)
    factoryLoacation = FactoryLocation(factory)
    if Grid['type'] == 'standard':
        blendsValues = list(db.blend.find({"_id": ObjectId(blends['value']['$oid'])}))
        # print(blendsValues)
    else:
        static.pop('Ingredients/Black,Green,Flavoured', None)
        static.pop('Blend Name/Legal Name', None)
    if Grid['type'] == 'selection pack':
        legal_name = Grid['legal_name']
        # legal_Value =
    if Grid['category'] == 'tea bag':
        try:
            ingredient = blendsValues[0]['ingredient_tea_bag']
            blend = blendsValues[0]['blend_tea_bag']
        except:
            blend = None
            ingredient = None
        try:
            tea_origin = blendsValues[0]['tea_origin']
        except:
            tea_origin = None
        try:
            no_of_tea_bag = Grid['no_of_bags']
        except:
            no_of_tea_bag = ''
    if Grid['category'] == 'loose tea':
        try:
            ingredient = blendsValues[0]['ingredient_loose']
            blend = blendsValues[0]['blend_loose']
        except:
            blend = None
            ingredient = None
        try:
            tea_origin = blendsValues[0]['tea_origin']
        except:
            tea_origin = None
        no_of_tea_bag = ''
    for country in Grid['countries']:
        lang = list(db.country.find({"code": country}, {"_id": 0, "language": 1}))
        requirements  = get_country_requirements(country)
        for i in range(len(lang)):
            for l in lang[i]['language']:
                if l not in languageList:
                    languageList.append(l)
                    language_requirenents[l]=requirements
    # print(language_requirenents)
    data = list(db.additional_requirement.find({"static":True}).sort("order",1))
    static.update(BasicRequirement(data))
    # static.update(AdditionalRequirement(Grid['countries']))
    # print(static)
    try:
        static.update(BlendReqAdd(blends,Grid['countries'],Grid['category']))
    except:
        static.update(BlendReqAdd([blends], Grid['countries'],Grid['category']))
    # print(ingredient,blend,tea_origin)
    # country_requirement = Add_Country_requirements(static, Grid['countries'])
    for i in languageList:
        requirements = static.copy()
        for req in language_requirenents[i]:
            if req['type'] == 'Translation-ID':
                # print(req)
                try:
                    translation = list(db.translations.find({"language":i,"translation.master_id":req['value']}))
                    # print(translation)
                    for trans in translation:
                        for tran in trans['translation']:
                            if req['value'] == tran['master_id']:
                                for version in tran['versions']:
                                    if version['currentVersion'] == True:
                                        if version['version'] >= 1:
                                            translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                        else:
                                            translation_id = tran['trans_id']
                                        requirements[req['requirement']] = translation_id
                                        translation_values[translation_id] = version['trans']
                                        if req['requirement'] in groupedtranslation:
                                            myList = [translation_id ,version['trans']]
                                            groupedtranslation[req['requirement']].append(myList)

                                    else:
                                        pass
                            else:
                                pass
                except Exception as e:
                    requirements[req['requirement']] = False

            elif req['type'] == 'Asset':
                try:
                    asset = db.myapp_asset.find({"id": req['value']})
                    for ast in asset:
                        requirements[req['requirement']] = "http://"+host+"/media/"+ast['photo']
                except Exception as e:
                    requirements[req['requirement']] = False
            elif req['type'] == 'Plain-text':
                try:
                    requirements[req['requirement']] = req['value']
                except Exception as e:
                    requirements[req['requirement']] = False
        if weight == "5-50":
            requirements["Net Weight Sizes"] = '2mm'
        elif weight == "51-200":
            requirements["Net Weight Sizes"] = '3mm'
        elif weight == "201-1000":
            requirements["Net Weight Sizes"] = '4mm'
        else:
            requirements["Net Weight Sizes"] = '6mm'
        # blend translation
        if Grid['type'] == 'standard':
            translation = db.translations.find({'language': i,'translation.master_id': blend})
            try:
                for trans in translation:
                    for tran in trans['translation']:
                        if tran['master_id'] == blend:
                            for version in tran['versions']:
                                if version['currentVersion'] == True:
                                    if version['version'] >= 1:
                                        translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                    else:
                                        translation_id = tran['trans_id']
                                    requirements["Blend Name/Legal Name"] =  translation_id
                                    translation_values[translation_id] = version['trans']
                                else:
                                    pass
                        else:
                            pass
            except Exception as e:
                requirements["Blend Name/Legal Name"] = False
            translation = db.translations.find({'language': i,'translation.master_id': ingredient})
            try:
                for trans in translation:
                    for tran in trans['translation']:
                        if tran['master_id'] == ingredient:
                            for version in tran['versions']:
                                if version['currentVersion'] == True:
                                    if version['version'] >= 1:
                                        translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                    else:
                                        translation_id = tran['trans_id']
                                    requirements['Ingredients/Black,Green,Flavoured'] = translation_id
                                    translation_values[translation_id] = version['trans']
                                else:
                                    pass
                        else:
                            pass
            except Exception as e:
                requirements['Ingredients/Black,Green,Flavoured'] = False
            arg = {
                "language": i,
                "blend": blends['value']['$oid'],
                "name": blends['label'],
                "translationValues": translation_values,
                "category":Grid['category'],
                "host":host
            }
            blend_req = BlendRequirements(arg)
            # print(blend_req.requirementvalues)
            requirements.update(blend_req.requirementvalues)
            translation_values.update(blend_req.translation_values)
        elif Grid['type'] == 'promo pack':
            promopack = promoPack(requirements, i,blends, translation_values,Grid['category'],groupedtranslation,host)
        elif Grid['type'] == 'selection pack':
            promopack = promoPack(requirements, i,blends, translation_values,Grid['category'],groupedtranslation,host)
            selectionpack = SelctionPack(requirements, i,legal_name, translation_values)
        translation = db.translations.find({'language': i, 'translation.master_id': tea_origin})
        try:
            for trans in translation:
                for tran in trans['translation']:
                    if tran['master_id'] == tea_origin:
                        for version in tran['versions']:
                            if version['currentVersion'] == True:
                                if version['version'] >= 1:
                                    translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                else:
                                    translation_id = tran['trans_id']
                                requirements['Tea Origin'] =  translation_id
                                translation_values[translation_id] = version['trans']
                            else:
                                pass
                    else:
                        pass
        except Exception as e:
            requirements['Tea Origin'] = False
        # requirements["No of teabags"] = no_of_tea_bag
        if Grid['type'] == 'promo pack':
            requirements.update(promopack[0])
            translation_values.update(promopack[1])
            groupedtranslation.update(promopack[2])
        if Grid['type'] == 'selection pack':
            translation_values.update(promopack[1])
            groupedtranslation.update(promopack[2])
            requirements.update(selectionpack[0])
            requirements.update(promopack[0])
        factorytranlation = factoryTranslation(requirements,i,factoryLoacation,translation_values)
        requirements.update(factorytranlation[0])
        custom = CustomCondition(Grid,i)
        reg = registration_numbers(requirements,i,Grid['item'],Grid['countries'])
        requirements.update((reg))
        custom_conditions = customTranslation(custom,i,translation_values,groupedtranslation)
        requirements.update(custom_conditions[0])
        translation_values.update(factorytranlation[1])
        translation_values.update(custom_conditions[1])
        groupedtranslation.update(custom_conditions[2])
        grid.append({i: requirements.copy()})
        requirements.clear()
    # print(grid)
    # print(translation_values)
    # print(groupedtranslation)
    return (grid,translation_values,groupedtranslation)
def additionalRequirements(Grid,host):
    grid_generator = Gridgenerator(Grid,host)
    base_grid = grid_generator[0]
    groupedtranslation = grid_generator[2]
    translation_values = grid_generator[1]
    requirement = {}
    languageList = []
    language_requirements ={}
    countryLanguageList = []
    country_requirements = []
    additional_grid = []
    requirement.update(AdditionalRequirement(Grid['countries']))
    for country in Grid['countries']:
        lang = list(db.country.find({"code": country}, {"_id": 0, "language": 1}))
        additional_requirement = get_country_additional_requirements(country)
        for i in range(len(lang)):
            for l in lang[i]['language']:
                if l not in languageList:
                    languageList.append(l)
                    language_requirements[l] = additional_requirement

        req = list(db.additional_requirement.find({"country":country}))
        if len(req) > 0:
            for countries in req:
                for value in countries['country']:
                    lang = list(db.country.find({"code": value}, {"_id": 0, "language": 1}))
                    # print(lang)
                    for lan in lang:
                        for langs in lan['language']:
                            if langs not in countryLanguageList:
                                countryLanguageList.append(langs)
                # print(lang[i]['language'],countries)
            # print(countryLanguageList)
            country_requirements.append({l:req})
            for re in req:
                requirement[re['requirement']] = ''
            # print(requirement)
    print(language_requirements)
    for language in languageList:
        lang_req = requirement.copy()
        for country in Grid['countries']:
            req = list(db.additional_requirement.find({"country": country}))
            for i in req:
                for val in i['country']:
                    lang = list(db.country.find({"code": val}, {"_id": 0, "language": 1}))
                    for i in range(len(lang)):
                        # lang_req = requirement.copy()
                        for l in lang[i]['language']:
                            if language == l:
                                for re in req:
                                    if re['type'] == 'Translation-ID':
                                        count = db.translations.find(
                                            {"language": l, "translation.master_id": re['value']}).count()
                                        if count > 0:
                                            translation = db.translations.find(
                                                {"language": l, "translation.master_id": re['value']})
                                            # print(translation)
                                            for trans in translation:
                                                for tran in trans['translation']:
                                                    if re['value'] == tran['master_id']:
                                                        for version in tran['versions']:
                                                            if version['currentVersion'] == True:
                                                                if version['version'] >= 1:
                                                                    translation_id = tran['trans_id'] + ' ['+ str(version['version'])+']'
                                                                else:
                                                                    translation_id = tran['trans_id']
                                                                lang_req[re['requirement']] = translation_id
                                                                translation_values[translation_id] = version['trans']
                                                                if re['requirement'] in groupedtranslation:
                                                                    myList = [translation_id, version['trans']]
                                                                    if myList not in groupedtranslation[re['requirement']]:
                                                                        groupedtranslation[re['requirement']].append(myList)
                                                            else:
                                                                pass
                                                    else:
                                                        pass
                                        else:
                                            lang_req[re['requirement']] = False

                                    elif re['type'] == 'Asset':
                                        try:
                                            asset = db.myapp_asset.find({"id": re['value']})
                                            for ast in asset:
                                                lang_req[re['requirement']] = "http://"+host+"/media/"+ast['photo']
                                        except Exception as e:
                                            lang_req[re['requirement']] = False
                                    elif re['type'] == 'Plain-text':
                                        try:
                                            lang_req[re['requirement']] = re['value']
                                        except Exception as e:
                                            lang_req[re['requirement']] = False
                                    # print(lang_req)
                                    additional_grid.append({l: lang_req.copy()})
                                    # print(additional_grid)
                                    lang_req.clear()
                                custom = CustomCondition(Grid, language)
                                custom_conditions = customTranslation(custom, language, translation_values, groupedtranslation)
                                additional_grid.append({l:custom_conditions[0]})
                                # print({l:custom_conditions[0]})
    # print(additional_grid,"test")
    try:
        for i in countryLanguageList:
            languageList.remove(i)
    except:
        pass
    # for i in languageList:
    #     additional_grid.append({i: requirement.copy()})
    # check  = check_requirement(additional_grid,base_grid,requirement)
    for grd in base_grid:
        for gr in additional_grid:
            for j in gr:
                for i in grd:
                    if i == j:
                        key = grd[i].keys()
                        grd[i].update(gr[j].copy())
    # print(base_grid)
    return (base_grid,translation_values,Grid, groupedtranslation)

def GridPreview(request):
    myList2 = []
    key = []
    langs = ['']
    j = {}
    for i in request:
        for lang in i:
            langs.append(lang)
        j = i.values()
        for k in j:
            for val in k:
                if val not in key:
                    key.append(val)
            myList2.append(k.values())
    myList2.insert(0,key)
    new_list = list(zip(*myList2))
    modified = make_duplicate_empty(new_list)
    data = {"data":modified , "languages": langs}
    return data

def LanguageTranslation(translation,languages):
    language = languages.copy()
    language.remove('')
    groupTranslation = []

    for i in language:
        lis = []
        for j in translation:
            if i in j:
                lis.append([j,translation[j]])
        groupTranslation.append(lis)
    return groupTranslation
    # print(translation,languages)

def promoPack(requirements,language,blends,translation_values,category,groupedtranslation,host):
    requirement = requirements.copy()
    for i in blends:
        arg = {
            "language":language,
            "blend":i['value']['$oid'],
            "name":i['label'],
            "translationValues":translation_values,
            "host":host,
            "category":category
        }
        blend_req = BlendRequirements(arg)
        # print(blend_req.requirementvalues)
        requirement.update(blend_req.requirementvalues)
        translation_values.update(blend_req.translation_values)
        blendsValues = list(db.blend.find({"_id": ObjectId(i['value']['$oid'])}))
        if category == 'tea bag':
            try:
                ingredient = blendsValues[0]['ingredient_tea_bag']
                blend = blendsValues[0]['blend_tea_bag']
                # print()
            except:
                blend = None
                ingredient = None
        elif category == 'loose tea':
            try:
                ingredient = blendsValues[0]['ingredient_loose']
                blend = blendsValues[0]['blend_loose']
            except:
                blend = None
                ingredient = None
            try:
                tea_origin = blendsValues[0]['tea_origin']
            except:
                tea_origin = None
        translation = db.translations.find({'language': language, 'translation.master_id': blend})
        blend_req = 'Blend Name-' + ' ('+ blendsValues[0]['name'] + ')'
        value = {blend_req: ''}
        requirement.update(value)
        if blend_req in groupedtranslation:
            pass
        else:
            value = {blend_req: []}
            groupedtranslation.update(value)
        try:
            for trans in translation:
                for tran in trans['translation']:
                    if tran['master_id'] == blend:
                        for version in tran['versions']:
                            if version['currentVersion'] == True:
                                if version['version'] == 1:
                                    translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                else:
                                    translation_id = tran['trans_id']
                                requirement[blend_req] = translation_id
                                translation_values[translation_id] = version['trans']
                                myList = [translation_id, version['trans']]
                                groupedtranslation[blend_req].append(myList)

                            else:
                                pass
                    else:
                        pass
        except Exception as e:
            pass
            # requirement[blend_req] = ''
        translation = list(db.translations.find({'language': language, 'translation.master_id': ingredient}))
        ing_req = 'Ingredients-'+blendsValues[0]['name']
        value = {ing_req:""}
        requirement.update(value)
        if ing_req in groupedtranslation:
            pass
        else:
            value = {ing_req: []}
            groupedtranslation.update(value)
        try:
            for trans in translation:
                for tran in trans['translation']:
                    if tran['master_id'] == ingredient:
                        for version in tran['versions']:
                            if version['currentVersion'] == True:
                                if version['version'] >= 1:
                                    translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                else:
                                    translation_id = tran['trans_id']
                                requirement[ing_req] = translation_id
                                translation_values[translation_id] = version['trans']
                                myList = [translation_id, version['trans']]
                                groupedtranslation[ing_req].append(myList)
                            else:
                                pass
                    else:
                        pass
        except Exception as e:
            pass
            # requirement[ing_req] = ''
    return (requirement,translation_values,groupedtranslation)
def SelctionPack(requirements,language,legal_name,translation_values):
    requirement = requirements.copy()
    name = list(db.legal_name.find({"translation":legal_name}))
    if db.translations.find({'language': language, 'translation.master_id':name[0]['translation']}).count() > 0:
        translation = db.translations.find({'language': language, 'translation.master_id':name[0]['translation']})
        for trans in translation:
            for tran in trans['translation']:
                if tran['master_id'] == name[0]['translation']:
                    for version in tran['versions']:
                        if version['currentVersion'] == True:
                            if version['version'] >= 1:
                                translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                            else:
                                translation_id = tran['trans_id']
                            requirement['Legal Name'] = translation_id
                            translation_values[translation_id] = version['trans']
                        else:
                            pass
                else:
                    pass
    else:
        requirement['Legal Name'] = ''
    return (requirement,translation_values)
def FactoryLocation(factory):
    location = list(db.factory.find({"location.label":factory['label']}))
    try:
        packed_in = location[0]['packed_in']['value']
        address = location[0]['address']['value']
    except:
        packed_in = False
        address = False
    return (packed_in,address)
def factoryTranslation(requirements,lan,factory,translationvalues):
    packed_in = db.translations.find({'language': lan, 'translation.master_id':factory[0]})
    try:
        for trans in packed_in:
            for tran in trans['translation']:
                if tran['master_id'] == factory[0]:
                    for version in tran['versions']:
                        if version['currentVersion'] == True:
                            if version['version'] >= 1:
                                translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                            else:
                                translation_id = tran['trans_id']
                            requirements['Packed in/Shippping Country/Country of Origin'] = translation_id
                            translationvalues[translation_id] = version['trans']
                        else:
                            pass
                else:
                    pass
    except Exception as e:
        requirements['Packed in/Shippping Country/Country of Origin'] = False
    address = db.translations.find({'language': lan, 'translation.master_id': factory[1]})
    try:
        for trans in address:
            for tran in trans['translation']:
                if tran['master_id'] == factory[1]:
                    for version in tran['versions']:
                        if version['currentVersion'] == True:
                            if version['version'] >= 1:
                                translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                            else:
                                translation_id = tran['trans_id']
                            requirements['Factory Address'] = translation_id
                            translationvalues[translation_id] = version['trans']
                        else:
                            pass
                else:
                    pass
    except Exception as e:
        requirements['Factory Address'] = False
    return (requirements,translationvalues)
def AddLanguage(request):
    static = {"Size restriction": "", "The word ingredients": "", "Ingredients/Black,Green,Flavoured": "",
              "Net Weight Sizes": "",
              "Net Weight": "", "Packing Date": "", "Best Before": "", "Blend Name/Legal Name": "",
              "Tea information(Loose /TB)": "",
              "Number of Teabags": "", "No of teabags": "", "Brewing Instructions": "", "Storage Condition": "",
              # "Pour on cold water and brew for 5 minutes":"",
              "Packed in/Shippping Country/Country of Origin": "", "Factory Address": "", "Producer/Exporter": "",
              "Importer/Qulaity Issues": "", "Registration number": "", "Batch number": "", "RNPA number": "",
              "Non world wide Strapline": "", "Non world wide descriptive text": "", "Ethical Tea Partnership Logo": "",
              "Great Taste Award Logo": "",
              "Sales & Customer Service": "", "Tea Origin": "", "Copyrights": "", "Barcode": "", "Carton No": "",
              "GMO free": "", "Nutritional value": "", "Blend info": "", "e Symbol (3mm high)": "", "Logo": ""}
    groupedtranslation = {"The word Ingredients": [], "Net Weight": [], "Brew for 5minutes (HERBALS)": [],
                          "Ingredients": [],
                          "Packing Date": [], "Brewing Instructions": [], "Storage Condition": []}
    data = list(db.additional_requirement.find({"country": "All"}))
    static.update(BasicRequirement(data))
    Grid = request.data['values']
    grouped = request.data['grouped_translation']
    language_tran = request.data['language_translations']
    blends = Grid['blends']
    weight = Grid["weight"]
    factory = Grid['factory']
    blendsValues = ''
    lan = request.data['language']
    translation_values = {}
    # print(Grid)
    factoryLoacation = FactoryLocation(factory)
    if Grid['type'] == 'standard':
        blendsValues = list(db.blend.find({"_id": ObjectId(blends['value']['$oid'])}))
        # print(blendsValues)
    else:
        static.pop('Ingredients/Black,Green,Flavoured', None)
        static.pop('Blend Name/Legal Name', None)
    if Grid['type'] == 'selection pack':
        try:
            legalName = Grid['legal_name']
        except KeyError:
            legalName = Grid['legalname']
        # legal_Value =
    if Grid['category'] == 'tea bag':
        try:
            ingredient = blendsValues[0]['ingredient_tea_bag']
            blend = blendsValues[0]['blend_tea_bag']
        except:
            blend = None
            ingredient = None
        try:
            tea_origin = blendsValues[0]['tea_origin']
        except:
            tea_origin = None
        try:
            no_of_tea_bag = Grid['no_of_bags']
        except:
            no_of_tea_bag = ''
    if Grid['category'] == 'loose tea':
        try:
            ingredient = blendsValues[0]['ingredient_loose']
            blend = blendsValues[0]['blend_loose']
        except:
            blend = None
            ingredient = None
        try:
            tea_origin = blendsValues[0]['tea_origin']
        except:
            tea_origin = None
        no_of_tea_bag = ''
    for i in data:
        if i['type'] == 'Translation-ID':
            try:
                translation = list(db.translations.find({"language": lan, "translation.master_id": i['value']}))
                for trans in translation:
                    for tran in trans['translation']:
                        if i['value'] == tran['master_id']:
                            for version in tran['versions']:
                                if version['currentVersion'] == True:
                                    if version['version'] >= 1:
                                        translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                    else:
                                        translation_id = tran['trans_id']
                                    static[i['requirement']] = translation_id
                                    translation_values[translation_id] = version['trans']
                                    if i['requirement'] in groupedtranslation:
                                        myList = [translation_id, version['trans']]
                                        groupedtranslation[i['requirement']].append(myList)

                                else:
                                    pass
                        else:
                            pass
            except Exception as e:
                pass
        elif i['type'] == 'Asset':
            try:
                asset = db.myapp_asset.find({"id": i['value']})
                for ast in asset:
                    static[i['requirement']] = "http://" + request.get_host() + "/media/" + ast['photo']
            except Exception as e:
                static[i['requirement']] = False
        elif i['type'] == 'Plain-text':
            try:
                static[i['requirement']] = i['value']
            except Exception as e:
                static[i['requirement']] = False
        if weight == "5-50":
            static["Net Weight Sizes"] = '2mm'
        elif weight == "51-200":
            static["Net Weight Sizes"] = '3mm'
        elif weight == "201-1000":
            static["Net Weight Sizes"] = '4mm'
        else:
            static["Net Weight Sizes"] = '6mm'
        # blend translation
        if Grid['type'] == 'standard':
            translation = db.translations.find({'language': lan, 'translation.master_id': blend})
            try:
                for trans in translation:
                    for tran in trans['translation']:
                        if tran['master_id'] == blend:
                            for version in tran['versions']:
                                if version['currentVersion'] == True:
                                    if version['version'] >= 1:
                                        translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                    else:
                                        translation_id = tran['trans_id']
                                    static["Blend Name/Legal Name"] = translation_id
                                    translation_values[translation_id] = version['trans']
                                else:
                                    pass
                        else:
                            pass
            except Exception as e:
                static["Blend Name/Legal Name"] = False
            translation = db.translations.find({'language': lan, 'translation.master_id': ingredient})
            try:
                for trans in translation:
                    for tran in trans['translation']:
                        if tran['master_id'] == ingredient:
                            for version in tran['versions']:
                                if version['currentVersion'] == True:
                                    if version['version'] > 1:
                                        translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                    else:
                                        translation_id = tran['trans_id']
                                    static['Ingredients/Black,Green,Flavoured'] = translation_id
                                    translation_values[translation_id] = version['trans']
                                else:
                                    pass
                        else:
                            pass
            except Exception as e:
                static['Ingredients/Black,Green,Flavoured'] = False
            arg = {
                "language": lan,
                "blend": blends['value']['$oid'],
                "name": blends['label'],
                "translationValues": translation_values,
                "category":Grid['category'],
                "host": request.get_host()
            }
            blend_req = BlendRequirements(arg)
            # print(blend_req.requirementvalues)
            static.update(blend_req.requirementvalues)
            translation_values.update(blend_req.translation_values)
        elif Grid['type'] == 'promo pack':
            promopack = promoPack(static, lan, blends, translation_values, Grid['category'], groupedtranslation, request.get_host())
        elif Grid['type'] == 'selection pack':
            promopack = promoPack(static, lan, blends, translation_values, Grid['category'], groupedtranslation, request.get_host())
            selectionpack = SelctionPack(static, lan, legalName, translation_values)
        translation = db.translations.find({'language': i, 'translation.master_id': tea_origin})
        try:
            for trans in translation:
                for tran in trans['translation']:
                    if tran['master_id'] == tea_origin:
                        for version in tran['versions']:
                            if version['currentVersion'] == True:
                                if version['version'] >= 1:
                                    translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                else:
                                    translation_id = tran['trans_id']
                                static['Tea Origin'] = translation_id
                                translation_values[translation_id] = version['trans']
                            else:
                                pass
                    else:
                        pass
        except Exception as e:
            static['Tea Origin'] = False
    static["No of teabags"] = no_of_tea_bag
    if Grid['type'] == 'promo pack':
        static.update(promopack[0])
        translation_values.update(promopack[1])
        groupedtranslation.update(promopack[2])
    if Grid['type'] == 'selection pack':
        static.update(selectionpack[0])
        static.update(promopack[0])
        translation_values.update(promopack[1])
        groupedtranslation.update(promopack[2])
    factorytranlation = factoryTranslation(static, lan, factoryLoacation, translation_values, )
    static.update(factorytranlation[0])
    translation_values.update(factorytranlation[1])
    host = request.get_host()
    additionalRequirements = LanAdditionalRequirements(lan,translation_values,groupedtranslation,host)
    groupedtranslation.update(additionalRequirements[2])
    translation_values.update(additionalRequirements[1])
    static.update(additionalRequirements[0])
    custom = CustomCondition(Grid, lan)
    custom_conditions = customTranslation(custom, lan, translation_values, groupedtranslation)
    static.update(custom_conditions[0])
    translation_values.update(custom_conditions[1])
    groupedtranslation.update(custom_conditions[2])
    # print(translation_values,static)
    updated_grid = UpdatedGrid(request, static, translation_values, groupedtranslation)
    grouped_trans = GroupedTranslation(updated_grid[1],grouped)
    lan_trans = languageTranslation(updated_grid[2],language_tran)
    return (updated_grid[0],grouped_trans,lan_trans)

def LanAdditionalRequirements(lan,translation_values,groupedtranslation,host):
    additional = {}
    translation_values = translation_values
    groupedtranslation = groupedtranslation
    countries = list(db.country.find({"language":{"$in":[lan]}}))
    country = [country['code'] for country in countries]
    requirements = list(db.additional_requirement.find({"country":{"$in":country}}))
    for re in requirements :
        if re['type'] == 'Translation-ID':
            count = db.translations.find(
                {"language": lan, "translation.master_id": re['value']}).count()
            if count > 0:
                translation = db.translations.find(
                    {"language": lan, "translation.master_id": re['value']})
                # print(translation)
                for trans in translation:
                    for tran in trans['translation']:
                        if re['value'] == tran['master_id']:
                            for version in tran['versions']:
                                if version['currentVersion'] == True:
                                    if version['version'] >= 1:
                                        translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                    else:
                                        translation_id = tran['trans_id']
                                    additional[re['requirement']] = translation_id
                                    translation_values[translation_id] = version['trans']
                                    if re['requirement'] in groupedtranslation:
                                        myList = [translation_id, version['trans']]
                                        if myList not in groupedtranslation[re['requirement']]:
                                            groupedtranslation[re['requirement']].append(myList)
                                else:
                                    pass
                        else:
                            pass
            else:
                additional[re['requirement']] = False

        elif re['type'] == 'Asset':
            try:
                asset = db.myapp_asset.find({"id": re['value']})
                for ast in asset:
                    additional[re['requirement']] = "http://" + host + "/media/" + ast['photo']
            except Exception as e:
                additional[re['requirement']] = False
        elif re['type'] == 'Plain-text':
            try:
                additional[re['requirement']] = re['value']
            except Exception as e:
                additional[re['requirement']] = False
    return (additional,translation_values,groupedtranslation)

def UpdatedGrid(request,static,translation_values,groupedtranslation):
    grid = request.data['grid']
    keys = [i[0] for i in grid]
    addKey = static.keys()
    extrakey = []
    newkey = [extrakey.append(i) for i in addKey if i not in keys]
    stat = [static.update({i:''}) for i in keys if i not in addKey]
    for i in extrakey:
        leng = len(grid[0])
        val = []
        val.append(i)
        gridKey = [val.append('') for i in range(leng-1)]
        grid.append(val)
    for i in range(len(grid)):
        for j in static:
            if grid[i][0] == j:
                grid[i].append(static[j])
    # print(translation_values)
    return (grid, groupedtranslation,translation_values)
    # print(grid)
    # print(static)
        # if i[0] not in extrakey:
        #     grid.append()
    # print(request.data['grid'],static,translation_values,groupedtranslation)

def GroupedTranslation(new,old):
    for i in old:
        for j in new:
            if i == j:
                if len(new[j]) >0:
                    old[i].append(new[j][0])
    return old

def languageTranslation(new,old):
    translations = []
    for i in new:
        translations.append([i,new[i]])
    old.append(translations)
    return old

def  AddGridRequirement(request):
    req = request.data['requirement']['value']
    languages = request.data['languages']
    language = languages.copy()
    language.remove('')
    grid = request.data['grid']
    language_translations = request.data['language_translations']
    additional_requirement = []
    requirement = list(db.additional_requirement.find({"_id":ObjectId(req["$oid"])}))
    additional_requirement.append(requirement[0]['requirement'])
    n = 0
    for lan in language:
        if requirement[0]['type'] == 'Translation-ID':
            count = db.translations.find({"language": lan, "translation.master_id": requirement[0]['value']}).count()
            if count > 0:
                translation = db.translations.find({"language": lan, "translation.master_id": requirement[0]['value']})
                for trans in translation:
                    for tran in trans['translation']:
                        if requirement[0]['value'] == tran['master_id']:
                            for version in tran['versions']:
                                if version['currentVersion'] == True:
                                    if version['version'] >= 1:
                                        translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                    else:
                                        translation_id = tran['trans_id']
                                    additional_requirement.append(translation_id)
                                    language_translations[n].append([translation_id,version['trans']])
                                    # translation_values[translation_id] = version['trans']
                                else:
                                    pass
                        else:
                            pass
            else:
                additional_requirement.append(False)
        elif requirement[0]['type'] == 'Asset':
            try:
                asset = db.myapp_asset.find({"id": requirement[0]['value']})
                for ast in asset:
                     additional_requirement.append("http://" + request.get_host() + "/media/" + ast['photo'])
            except Exception as e:
                additional_requirement.append(False)
        elif requirement[0]['type'] == 'Plain-text':
            try:
                additional_requirement.append(requirement[0]['value'])
            except Exception as e:
                additional_requirement.append(False)
        n += 1
    grid.append(additional_requirement)
    return (grid,language_translations)

def customTranslation(custom,lan,translation_values,groupedtranslation):
    myDict = {}
    for i in custom:
      myDict[i] = ''
    for i in custom:
        try:
            translation = list(db.translations.find({"language": lan, "translation.master_id": custom[i]}))
            # print(translation)
            for trans in translation:
                for tran in trans['translation']:
                    if custom[i] == tran['master_id']:
                        for version in tran['versions']:
                            if version['currentVersion'] == True:
                                if version['version'] >= 1:
                                    translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                else:
                                    translation_id = tran['trans_id']
                                myDict[i] = translation_id
                                translation_values[translation_id] = version['trans']
                                if i in groupedtranslation:
                                    myList = [translation_id, version['trans']]
                                    if myList not in groupedtranslation[i]:
                                        groupedtranslation[i].append(myList)
                            else:
                                pass
                    else:
                        pass
        except Exception as e:
            myDict[i] = False
    # print(myDict)
    return (myDict,translation_values,groupedtranslation)

class BlendRequirements:
    def __init__(self, request):
        self.language = request['language']
        self.blend = request['blend']
        self.name = request['name']
        self.host = request['host']
        self.category = request['category']
        self.translation_values = request['translationValues']
        self.requirements = self.find_requirement()
        self.requirementvalues = self.find_translation()
    def find_requirement(self):
        requirements = list(db.blend_requirements.find({"blend":self.blend,"category":self.category}))
        blend_requirements = []
        for i in requirements:
            for j in i['country']:
                lan = list(db.country.find({"code":j}))
                if self.language in lan[0]['language']:
                    blend_requirements.append(i)
        return blend_requirements

    def find_translation(self):
        mydict = {}
        for i in self.requirements:
            if i['type'] == 'Plain-text':
                mydict[i['requirement']+'-'+self.name]= i['value']
            elif i['type'] == 'Translation-ID':
                pipeline = [
                    {
                        "$match": {
                            "language": self.language,
                            "translation.master_id": i['value']
                        }
                    },
                    {
                        "$project": {
                            "matchedDocument": {
                                "$filter": {
                                    "input": "$translation",
                                    "as": "trans",
                                    "cond": {"$eq": ["$$trans.master_id", i['value']]}
                                }
                            }
                        }
                    }
                ]
                result = list(db.translations.aggregate(pipeline))
                try:
                    for j in result[0]['matchedDocument'][0]['versions']:
                        if j['currentVersion']:
                            trans_id = result[0]['matchedDocument'][0]['trans_id']+' ['+str(j['version'])+']'
                            mydict[i['requirement'] + '-' + self.name] = trans_id
                            self.translation_values[trans_id] = j['trans']
                except:
                    mydict[i['requirement'] + '-' + self.name] = ''
            elif i['type'] == 'Asset':
                try:
                    asset = db.myapp_asset.find({"id": i['value']})
                    for ast in asset:
                        mydict[i['requirement']+ '-' + self.name] = "http://"+self.host+"/media/"+ast['photo']
                except Exception as e:
                    mydict[i['requirement']+ '-' + self.name] = False
        return mydict
def make_duplicate_empty(data):
    seen_elements = set()
    modified_data = []
    for tuple_ in data:
        modified_tuple = tuple('' if element in seen_elements else element for element in tuple_)
        modified_data.append(modified_tuple)
        seen_elements.update(modified_tuple)
    return modified_data

def registration_numbers(requirements,language,item_no,countries):
    requirement = requirements.copy()
    country = list(db.country.find({"language":language}))
    reg = False
    if len(country)>0:
        for i in country:
            if i['code'] in countries:
                reg = i
    if reg:
        try:
            registration = list(db.registrationNo.find({"item":item_no,"country":reg['code']}))
            requirement['Registration number'] = registration[0]['registration']
        except:
            pass
    return requirement

def Add_Country_requirements(requirements,country):
    print(requirements,country)

