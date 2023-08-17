from pymongo import MongoClient
from bson import ObjectId
from .customCondition import CustomCondition
client = MongoClient('localhost',27017)
db = client.mongodbSchema



weight_list = ["5-50", "51-200", "201-1000", "1000"]
def BasicRequirement(request):
    # print(request)
    dicts = {}
    for i in request:
        dicts[i['requirement']] = ''
    return dicts

def GroupedRequirement():
    data = list(db.additional_requirement.find({"static":True}).sort("order",1))
    dicts = {}
    for i in data:
        dicts[i['requirement']] = []
    return dicts
def AdditionalRequirement(request):
    data = db.additional_requirement.find({"country": {"$in":request},"static": False}).sort("order",1)
    dicts = {}
    for i in data:
        dicts[i['requirement']] = ''
    return dicts
def get_country_requirements(name):
    data = list(db.additional_requirement.find({"country": {"$in": [name]}, "static": True}).sort("order",1))
    return data
def get_country_additional_requirements(name):
    data = list(db.additional_requirement.find({"country": {"$in": [name]}, "static": False}).sort("order",1))
    return data
def get_item_number_requirement(item):
    data = list(db.item_no_requirements.find({"item":item}))
    dicts = {}
    for i in data:
        dicts[i['requirement']] = ''
    print(dicts)
    return dicts
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
    groupedtranslation = GroupedRequirement()
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
    if Grid['type'] != 'standard':
        static.pop('Ingredients', None)
        static.pop('Blend name/Legal name', None)
    # static.update(AdditionalRequirement(Grid['countries']))
    # print(static)
    try:
        static.update(BlendReqAdd(blends,Grid['countries'],Grid['category']))
    except:
        static.update(BlendReqAdd([blends], Grid['countries'],Grid['category']))
    # print(ingredient,blend,tea_origin)
    # country_requirement = Add_Country_requirements(static, Grid['countries'])
    static.update(get_item_number_requirement(Grid['item']))
    for i in languageList:
        requirements = static.copy()
        for req in language_requirenents[i]:
            if req['type'] == 'Translation-ID':
                # print(req)

                if db.translations.find({"language": i, "translation.master_id": req['value']}).count() > 0:
                    translation = list(db.translations.find({"language":i,"translation.master_id":req['value']}))
                    # print(translation)
                    for trans in translation:
                        for tran in trans['translation']:
                            if req['value'] == tran['master_id']:
                                for version in tran['versions']:
                                    if version['currentVersion'] == True:
                                        if version['version'] > 1:
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
                else:
                    requirements[req['requirement']] = False
            elif req['type'] == 'Asset':
                try:
                    asset = db.myapp_asset.find({"id": req['value']})
                    for ast in asset:
                        requirements[req['requirement']] = "http://"+host+"/media/"+ast['photo']
                except Exception as e:
                    requirements[req['requirement']] = ""
            elif req['type'] == 'Plain-text':
                try:
                    requirements[req['requirement']] = req['value']
                except Exception as e:
                    requirements[req['requirement']] = ""
        if check_net_weight(language_requirenents[i]):
            matching_range = is_weight_range_match(weight, weight_list)

            if matching_range is not None:
                if '-' in matching_range:
                    requirements["Net weight sizes"] = weight_to_size[matching_range]
                else:
                    if int(weight.split('-')[0]) > 1000:
                        requirements["Net weight sizes"] = '6mm'
            else:
                if '-' in weight:
                    test_lower = int(weight.split('-')[0])
                    if test_lower > 1000:
                        requirements["Net weight sizes"] = '6mm'
                else:
                    if int(weight) > 1000:
                        requirements["Net weight sizes"] = '6mm'


        # blend translation
        if Grid['type'] == 'standard':
            Checkvalues = check_blend_name(language_requirenents[i])
            if Checkvalues[1] == True:
                if db.translations.find({"language": i, "translation.master_id": blend}).count() > 0:
                    translation = db.translations.find({'language': i,'translation.master_id': blend})
                    for trans in translation:
                        for tran in trans['translation']:
                            if tran['master_id'] == blend:
                                for version in tran['versions']:
                                    if version['currentVersion'] == True:
                                        if version['version'] > 1:
                                            translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                        else:
                                            translation_id = tran['trans_id']
                                        requirements["Blend name/Legal name"] = translation_id
                                        translation_values[translation_id] = version['trans']
                                        myList = [translation_id, version['trans']]
                                        try:
                                            groupedtranslation["Blend name/Legal name"].append(myList)
                                        except:
                                            pass
                                    else:
                                        pass
                            else:
                                pass
                else:
                    requirements["Blend name/Legal name"] = False
            if Checkvalues[0] == True:       
                if db.translations.find({"language": i, "translation.master_id":ingredient}).count() > 0:
                    translation = db.translations.find({'language': i,'translation.master_id': ingredient})
                    for trans in translation:
                        for tran in trans['translation']:
                            if tran['master_id'] == ingredient:
                                for version in tran['versions']:
                                    if version['currentVersion'] == True:
                                        if version['version'] > 1:
                                            translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                        else:
                                            translation_id = tran['trans_id']
                                        requirements['Ingredients'] = translation_id
                                        translation_values[translation_id] = version['trans']
                                        myList = [translation_id, version['trans']]
                                        try:
                                            groupedtranslation['Ingredients'].append(myList)
                                        except:
                                            pass
                                    else:
                                        pass
                            else:
                                pass
                else:
                    requirements['Ingredients'] = False
          
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
   
            values = check_blend_name(language_requirenents[i])
            promopack = promoPack(requirements, i,blends, translation_values,Grid['category'],groupedtranslation,host,values,True)
        elif Grid['type'] == 'selection pack':
            values = check_blend_name(language_requirenents[i])
            promopack = promoPack(requirements, i,blends, translation_values,Grid['category'],groupedtranslation,host,values,False)
            selectionpack = SelctionPack(requirements, i,legal_name, translation_values,values)
        # if db.translations.find({"language": i, "translation.master_id": tea_origin}).count() > 0:
        #     translation = db.translations.find({'language': i, 'translation.master_id': tea_origin})
        #     for trans in translation:
        #         for tran in trans['translation']:
        #             if tran['master_id'] == tea_origin:
        #                 for version in tran['versions']:
        #                     if version['currentVersion'] == True:
        #                         if version['version'] > 1:
        #                             translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
        #                         else:
        #                             translation_id = tran['trans_id']
        #                         requirements['Tea Origin'] =  translation_id
        #                         translation_values[translation_id] = version['trans']
        #                     else:
        #                         pass
        #             else:
        #                 pass
        # else:
        #     try:
        #         if requirements['Tea Origin']:
        #             pass
        #         elif requirements['Tea Origin'] == False:
        #             pass
        #         else:
        #             requirements['Tea Origin'] = ""
        #     except:
        #         pass

                            # requirements["No of teabags"] = no_of_tea_bag
        if Grid['type'] == 'promo pack':
                requirements.update(promopack[0])
                translation_values.update(promopack[1])
                groupedtranslation.update(promopack[2])
                requirements.pop('Ingredients', None)
                requirements.pop('Blend name/Legal name', None)
        if Grid['type'] == 'selection pack':
                translation_values.update(promopack[1])
                groupedtranslation.update(promopack[2])
                requirements.update(selectionpack[0])
                requirements.update(promopack[0])
                requirements.pop('Ingredients', None)
                requirements.pop('Blend name/Legal name', None)
        # fetching factory address translation
        # factorytranlation = factoryTranslation(requirements,i,factoryLoacation,translation_values)
        # requirements.update(factorytranlation[0])

        reg = registration_numbers(requirements,i,Grid['item'],Grid['countries'])
        requirements.update(reg)

        # custom = CustomCondition(Grid, i)
        # new_custom = custom_condition_language_base(custom, language_requirenents[i])
        # custom_conditions = customTranslation(new_custom,i,translation_values,groupedtranslation)
        # requirements.update(custom_conditions[0])
        # translation_values.update(custom_conditions[1])
        # groupedtranslation.update(custom_conditions[2])

        #adding factory address translation value to grid
        # translation_values.update(factorytranlation[1])

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
            # for re in req:
            #     requirement[re['requirement']] = ''
            # print(requirement)
    for l in languageList:
        lang_req = requirement.copy()
        for re in language_requirements[l]:
            if re['type'] == 'Translation-ID':
                if db.translations.find({"language": l, "translation.master_id": re['value']}).count() > 0:
                    translation = db.translations.find(
                        {"language": l, "translation.master_id": re['value']})
                    # print(translation)
                    for trans in translation:
                        for tran in trans['translation']:
                            if re['value'] == tran['master_id']:
                                for version in tran['versions']:
                                    if version['currentVersion'] == True:
                                        if version['version'] > 1:
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
                    lang_req[re['requirement']] = ""
            elif re['type'] == 'Plain-text':
                try:
                    lang_req[re['requirement']] = re['value']
                except Exception as e:
                    lang_req[re['requirement']] = ""
            # print(lang_req)
            additional_grid.append({l: lang_req.copy()})
            # print(additional_grid)
            lang_req.clear()

        # custom = CustomCondition(Grid, l)
        # new_custom = custom_condition_language_base(custom,language_requirements[l])
        # custom_conditions = customTranslation(new_custom, l, translation_values, groupedtranslation)
        # additional_grid.append({l:custom_conditions[0]})
        # print({l:custom_conditions[0]})
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
    main_grid = add_item_requirement(base_grid,Grid['countries'],host,translation_values,Grid['item'], groupedtranslation)
    update_data = custom_condition_update(main_grid[0], Grid, main_grid[1], main_grid[2])
    return(update_data[0],update_data[1],Grid, update_data[2])

def GridPreview(request):
    myList2 = []
    data = request
    key = []
    langs = ['']
    j = {}
    output = []

    # Extract the keys
    keys = list(data[0].values())[0].keys()

    # Iterate over the keys and extract values for each key
    for key in keys:
        values = [list(d.values())[0].get(key, '') for d in data]
        output.append((key, *values))

    for i in request:
        for lang in i:
            langs.append(lang)
        j = i.values()

    #     for k in j:
    #         for val in k:
    #             print(val)
    #             if val not in key:
    #                 key.append(val)
    #         myList2.append(k.values())
    # myList2.insert(0,key)
    # new_list = list(zip(*myList2))
    # # print(new_list)
    # modified = make_duplicate_empty(new_list)
    data = {"data":output , "languages": langs}
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

def promoPack(requirements,language,blends,translation_values,category,groupedtranslation,host,values,pack):
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
                blend = ""
                ingredient = ""
        elif category == 'loose tea':
            try:
                ingredient = blendsValues[0]['ingredient_loose']
                blend = blendsValues[0]['blend_loose']
            except:
                blend = ""
                ingredient = ""
            try:
                tea_origin = blendsValues[0]['tea_origin']
            except:
                tea_origin = None
        if pack:
            blend_req = 'Blend Name-' + ' ('+ blendsValues[0]['name'] + ')'
            value = {blend_req: ''}
            requirement.update(value)
            if blend_req in groupedtranslation:
                pass
            else:
                value = {blend_req: []}
                groupedtranslation.update(value)
            if values[1] == True:
                if db.translations.find({"language":language, "translation.master_id": blend}).count() > 0:
                    translation = db.translations.find({'language': language, 'translation.master_id': blend})
                    for trans in translation:
                        for tran in trans['translation']:
                            if tran['master_id'] == blend:
                                for version in tran['versions']:
                                    if version['currentVersion'] == True:
                                        if version['version'] > 1:
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
                else:
                    requirement[blend_req] = False
                       

        ing_req = 'Ingredients-'+blendsValues[0]['name']
        value = {ing_req:""}
        requirement.update(value)
        if ing_req in groupedtranslation:
            pass
        else:
            value = {ing_req: []}
            groupedtranslation.update(value)
        if values[0] == True:
            if db.translations.find({"language": language, "translation.master_id": ingredient}).count() > 0:
                translation = list(db.translations.find({'language': language, 'translation.master_id': ingredient}))
                for trans in translation:
                    for tran in trans['translation']:
                        if tran['master_id'] == ingredient:
                            for version in tran['versions']:
                                if version['currentVersion'] == True:
                                    if version['version'] > 1:
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
            else: 
                requirement[ing_req] = False
              
                # requirement[ing_req] = ''
    return (requirement,translation_values,groupedtranslation)
def SelctionPack(requirements,language,legal_name,translation_values,values):
    requirement = requirements.copy()
    name = list(db.legal_name.find({"translation":legal_name}))
    if values[1] ==True:
        if db.translations.find({'language': language, 'translation.master_id':name[0]['translation']}).count() > 0:
            translation = db.translations.find({'language': language, 'translation.master_id':name[0]['translation']})
            for trans in translation:
                for tran in trans['translation']:
                    if tran['master_id'] == name[0]['translation']:
                        for version in tran['versions']:
                            if version['currentVersion'] == True:
                                if version['version'] > 1:
                                    translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                else:
                                    translation_id = tran['trans_id']
                                requirement['Blend name/Legal name'] = translation_id
                                translation_values[translation_id] = version['trans']
                            else:
                                pass
                    else:
                        pass
        else:
            if name[0]['translation'] != '':
                requirement['Blend name/Legal name'] = False
            else:
                requirement['Blend name/Legal name'] = ''
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
    if db.translations.find({'language': lan, 'translation.master_id': factory[0]}).count() >0:
        packed_in = db.translations.find({'language': lan, 'translation.master_id':factory[0]})
        for trans in packed_in:
            for tran in trans['translation']:
                if tran['master_id'] == factory[0]:
                    for version in tran['versions']:
                        if version['currentVersion'] == True:
                            if version['version'] > 1:
                                translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                            else:
                                translation_id = tran['trans_id']
                            requirements['Packed in/Shipping Country/Country of origin'] = translation_id
                            translationvalues[translation_id] = version['trans']
                        else:
                            pass
                else:
                    pass
    else:
        requirements['Packed in/Shipping Country/Country of origin'] = False
    if db.translations.find({'language': lan, 'translation.master_id': factory[1]}).count() > 0:
        address = db.translations.find({'language': lan, 'translation.master_id': factory[1]})
        for trans in address:
            for tran in trans['translation']:
                if tran['master_id'] == factory[1]:
                    for version in tran['versions']:
                        if version['currentVersion'] == True:
                            if version['version'] > 1:
                                translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                            else:
                                translation_id = tran['trans_id']
                            requirements['Factory Address'] = translation_id
                            translationvalues[translation_id] = version['trans']
                        else:
                            pass
                else:
                    pass
    else:
        requirements['Factory Address'] = False
    return (requirements,translationvalues)
def AddLanguage(request):
    static = {}
    lan = request.data['language']
    groupedtranslation = GroupedRequirement()
    data = list(db.additional_requirement.find({"static":True}).sort("order",1))
    country = list(db.country.find({"language": {"$in": [lan]}}))
    try:
        country = country[0]['code']
    except:
        country = lan
    requirements = get_country_requirements(country)
    static.update(BasicRequirement(data))
    Grid = request.data['values']
    grouped = request.data['grouped_translation']
    language_tran = request.data['language_translations']
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
        static.pop('Ingredients', None)
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
    for i in requirements:
        if i['type'] == 'Translation-ID':
            if db.translations.find({"language": lan, "translation.master_id": i['value']}).count() > 0:
                translation = list(db.translations.find({"language": lan, "translation.master_id": i['value']}))
                for trans in translation:
                    for tran in trans['translation']:
                        if i['value'] == tran['master_id']:
                            for version in tran['versions']:
                                if version['currentVersion'] == True:
                                    if version['version'] > 1:
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
            else:
                if i['value'] != '':
                    static[i['requirement']] = False
                else:
                    static[i['requirement']] = ''
        elif i['type'] == 'Asset':
            try:
                asset = db.myapp_asset.find({"id": i['value']})
                for ast in asset:
                    static[i['requirement']] = "http://" + request.get_host() + "/media/" + ast['photo']
            except Exception as e:
                static[i['requirement']] =""
        elif i['type'] == 'Plain-text':
            try:
                static[i['requirement']] = i['value']
            except Exception as e:
                static[i['requirement']] = ""
        if check_net_weight(requirements):
            matching_range = is_weight_range_match(weight, weight_list)

            if matching_range is not None:
                if '-' in matching_range:
                    static["Net Weight Sizes"] = weight_to_size[matching_range]
                else:
                    if int(weight.split('-')[0]) > 1000:
                        static["Net Weight Sizes"] = '6mm'
            else:
                if '-' in weight:
                    test_lower = int(weight.split('-')[0])
                    if test_lower > 1000:
                        static["Net Weight Sizes"] = '6mm'
                else:
                    if int(weight) > 1000:
                        static["Net Weight Sizes"] = '6mm'

        # blend translation
        if Grid['type'] == 'standard':
            Checkvalues =  check_blend_name(requirements)
            if Checkvalues[1] == True:
                if db.translations.find({"language": lan, "translation.master_id": blend}).count() > 0:
                    translation = db.translations.find({'language': lan, 'translation.master_id': blend})
                    for trans in translation:
                        for tran in trans['translation']:
                            if tran['master_id'] == blend:
                                for version in tran['versions']:
                                    if version['currentVersion'] == True:
                                        if version['version'] > 1:
                                            translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                        else:
                                            translation_id = tran['trans_id']
                                        static["Blend name/Legal name"] = translation_id
                                        translation_values[translation_id] = version['trans']
                                    else:
                                        pass
                            else:
                                pass
                else:
                    static["Blend name/Legal name"]=False
            if  Checkvalues[0] == True :         
                if db.translations.find({"language": lan, "translation.master_id": ingredient}).count() > 0:
                    translation = db.translations.find({'language': lan, 'translation.master_id': ingredient})
                    for trans in translation:
                        for tran in trans['translation']:
                            if tran['master_id'] == ingredient:
                                for version in tran['versions']:
                                    if version['currentVersion'] == True:
                                        if version['version'] > 1:
                                            translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                                        else:
                                            translation_id = tran['trans_id']
                                        static['Ingredients'] = translation_id
                                        translation_values[translation_id] = version['trans']
                                    else:
                                        pass
                            else:
                                pass
                else:
                    requirements['Ingredients'] = False
                 
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
            ingredient_value = ""
            blend_value = ""
            if requirements["Blend name/Legal name"] == False:
                ingredient_value = False
            if requirements['Ingredients'] == False:
                blend_value = False
            values = check_blend_name(requirements)
            promopack = promoPack(static, lan, blends, translation_values, Grid['category'], groupedtranslation, request.get_host(),values,True)
        elif Grid['type'] == 'selection pack':
            values = check_blend_name(requirements)
            promopack = promoPack(static, lan, blends, translation_values, Grid['category'], groupedtranslation, request.get_host(),values,False)
            selectionpack = SelctionPack(static, lan, legalName, translation_values,values)

        # if db.translations.find({"language": lan, "translation.master_id": tea_origin}).count() > 0:
        #     translation = db.translations.find({'language': i, 'translation.master_id': tea_origin})
        #     for trans in translation:
        #         for tran in trans['translation']:
        #             if tran['master_id'] == tea_origin:
        #                 for version in tran['versions']:
        #                     if version['currentVersion'] == True:
        #                         if version['version'] > 1:
        #                             translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
        #                         else:
        #                             translation_id = tran['trans_id']
        #                         static['Tea Origin'] = translation_id
        #                         translation_values[translation_id] = version['trans']
        #                     else:
        #                         pass
        #             else:
        #                 pass
        # else:
        #     try:
        #         if static['Tea Origin']:
        #             pass
        #         if static['Tea Origin'] == False:
        #             pass
        #         else:
        #             static['Tea Origin'] = ""
        #     except:
        #         pass
    # static["No of teabags"] = no_of_tea_bag
    if Grid['type'] == 'promo pack':
        static.pop('Ingredients', None)
        static.pop('Blend name/Legal name', None)
        static.update(promopack[0])
        translation_values.update(promopack[1])
        groupedtranslation.update(promopack[2])
    if Grid['type'] == 'selection pack':
        static.update(selectionpack[0])
        static.update(promopack[0])
        translation_values.update(promopack[1])
        groupedtranslation.update(promopack[2])
    # fetching fractory address translation
    # factorytranlation = factoryTranslation(static, lan, factoryLoacation, translation_values, )
    # static.update(factorytranlation[0])
    # translation_values.update(factorytranlation[1])
    host = request.get_host()

    additionalRequirements = LanAdditionalRequirements(lan,translation_values,groupedtranslation,host)
    groupedtranslation.update(additionalRequirements[2])
    translation_values.update(additionalRequirements[1])
    static.update(additionalRequirements[0])

    arg ={
            "language":lan,
            "countries":Grid['countries'],
            "host":host,
            "translationValues":translation_values,
            "item":Grid['item'],
            "grouped":groupedtranslation
            }
    item_req = ItemRequirements(arg)
    static.update(item_req.requirementvalues)
    translation_values.update(item_req.translation_values)
    groupedtranslation.update(item_req.grouped)

    custom = CustomCondition(Grid, lan)
    new_custom = custom_condition_language_base(custom,requirements)
    custom_conditions = customTranslation(new_custom , lan, translation_values, groupedtranslation)
    static.update(custom_conditions[0])
    translation_values.update(custom_conditions[1])
    groupedtranslation.update(custom_conditions[2])
    # print(translation_values,static)


    updated_grid = UpdatedGrid(request, static, translation_values, groupedtranslation)
    grouped_trans = GroupedTranslation(updated_grid[1],grouped)
    lan_trans = languageTranslation(updated_grid[2],language_tran)
    language_translation = filter_data_lanuage(lan_trans , updated_grid[0])
    grouped = filter_grouped_translation(grouped_trans, updated_grid[0])
    return (updated_grid[0],grouped ,language_translation)

def LanAdditionalRequirements(lan, translation_values, groupedtranslation, host):
    additional = {}
    translation_values = translation_values
    groupedtranslation = groupedtranslation
    country = db.country.find_one({"language": lan})
    if country:
        country = country['code']
    else:
        country = lan

    requirements = get_country_additional_requirements(country)

    translations = db.translations.find({"language": lan})
    translations_by_master_id = {t['translation'][0]['master_id']: t for t in translations}

    for requirement in requirements:
        if requirement['type'] == 'Translation-ID':
            translation = translations_by_master_id.get(requirement['value'])
            if translation:
                for tran in translation['translation']:
                    if requirement['value'] == tran['master_id']:
                        version = next((v for v in tran['versions'] if v['currentVersion'] and v['version'] > 1), None)
                        if version:
                            translation_id = tran['trans_id'] + ' [' + str(version['version']) + ']'
                            additional[requirement['requirement']] = translation_id
                            translation_values[translation_id] = version['trans']
                            if requirement['requirement'] in groupedtranslation:
                                myList = [translation_id, version['trans']]
                                if myList not in groupedtranslation[requirement['requirement']]:
                                    groupedtranslation[requirement['requirement']].append(myList)
                        else:
                            pass
            else:
                if requirement['value'] != '':
                    additional[requirement['requirement']] = False
                else:
                    additional[requirement['requirement']] = ""
        elif requirement['type'] == 'Asset':
            try:
                asset = db.myapp_asset.find_one({"id": requirement['value']})
                if asset:
                    additional[requirement['requirement']] = "http://" + host + "/media/" + asset['photo']
                else:
                    additional[requirement['requirement']] = ""
            except Exception as e:
                additional[requirement['requirement']] = ""
        elif requirement['type'] == 'Plain-text':
            additional[requirement['requirement']] = requirement['value']

    return additional, translation_values, groupedtranslation


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
                                    if version['version'] > 1:
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
                if requirement[0]['value'] != '':
                    additional_requirement.append(False)
                else:
                    additional_requirement.append("")
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
      print(custom)
    for i in custom:
        if db.translations.find({"language": lan, "translation.master_id": custom[i]}).count() > 0:
            translation = list(db.translations.find({"language": lan, "translation.master_id": custom[i]}))
            # print(translation)
            for trans in translation:
                for tran in trans['translation']:
                    if custom[i] == tran['master_id']:
                        for version in tran['versions']:
                            if version['currentVersion'] == True:
                                if version['version'] > 1:
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
        else:
            if custom[i] != '':
                myDict[i] = False
            if custom[i] == '':
                myDict[i] = ''

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
                            if j['version'] > 1:
                                trans_id = result[0]['matchedDocument'][0]['trans_id']+' ['+str(j['version'])+']'
                            else:
                                trans_id = result[0]['matchedDocument'][0]['trans_id']
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
    if len(country) > 0:
        for i in country:
            if i['code'] in countries:
                reg = i
    if reg:
        try:
            registration = list(db.registrationNo.find({"item":item_no,"country":reg['code']}))
            requirement['Registration number'] = registration[0]['registration']
        except:
            pass
    # print(requirement)
    return requirement


def filter_data_lanuage(lan, preview):
    data = lan.copy()
    for i in range(len(data)):
        for j in range(len(data[i])):
            search_string = data[i][j][0]
            present = any(search_string in t for t in preview)
            if present:
                pass
            else:
                data[i][j] = []
    # for i in data:
    #     print(i)
    # values = [[subsublist for subsublist in sublist if subsublist] for sublist in data if sublist]
    return data

# def filter_data_lanuage(lan, preview):
#     data = [sublist[:] for sublist in lan]  # Make a copy of the nested list
#     for sublist in data:
#         for subsublist in sublist:
#             search_string = subsublist[0] if subsublist else None
#             if search_string not in preview:
#                 subsublist.clear()  # Clear the subsublist if the condition is not met
#     values = [sublist for sublist in data if any(sublist) or not sublist]
#     return values



def check_present(requirement,data):
    for i in data:
        if i[0] == requirement['label']:
            return True

def custom_condition_language_base(condition,requirements):
    # Keys from the 'custom' dictionary
    custom_keys = set(condition.keys())

    # Extract 'requirement' values from the nested dictionaries in 'requirements'
    requirement_values = {req_dict.get('requirement') for req_dict in requirements}

    # Find keys in 'custom' that are not present in 'requirement_values'
    keys_to_remove = custom_keys - requirement_values

    # Remove keys from 'custom' that are not present in 'requirement_values'
    for key in keys_to_remove:
        condition.pop(key, None)
    return condition

def check_blend_name(requirements):
    MyDict = {"Blend name/Legal name":"","Ingredients":""}
    ingredient = True
    blend = True
    custom_keys = set(MyDict.keys())
    requirement_values = {req_dict.get('requirement') for req_dict in requirements}
    keys_to_remove = custom_keys - requirement_values
    if "Blend name/Legal name"  in keys_to_remove:
        blend = False
    if "Ingredients" in keys_to_remove:
        ingredient = False
    return (ingredient,blend)
def check_net_weight(requirements):
    MyDict = {"Net weight sizes":""}
    netWeight = True
    custom_keys = set(MyDict.keys())
    requirement_values = {req_dict.get('requirement') for req_dict in requirements}
    keys_to_remove = custom_keys - requirement_values
    if "Net weight sizes"  in keys_to_remove:
         return False
    return True
class ItemRequirements:
    def __init__(self, request):
        self.language = request['language']
        self.countries = request['countries']
        self.item = request['item']
        self.host = request['host']
        self.grouped = request['grouped']
        self.translation_values = request['translationValues']
        self.requirements = self.find_requirement()
        self.requirementvalues = self.find_translation()

    def find_requirement(self):
        country = list(db.country.find({"language": self.language}))
        reg = False
        if len(country) > 0:
            for i in country:
                if i['code'] in self.countries:
                    reg = i
        item_requirements = []
        if reg:
            requirements = list(db.item_no_requirements.find({"item":self.item}))

            for i in requirements:
                for j in i['country']:
                    lan = list(db.country.find({"code":j}))
                    if self.language in lan[0]['language']:
                        item_requirements.append(i)
        # print(item_requirements)
        return item_requirements

    def find_translation(self):
        mydict = {}
        for i in self.requirements:
            if i['type'] == 'Plain-text':
                mydict[i['requirement']]= i['value']
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
                            if j['version'] > 1:
                                trans_id = result[0]['matchedDocument'][0]['trans_id']+' ['+str(j['version'])+']'
                            else:
                                trans_id = result[0]['matchedDocument'][0]['trans_id']
                            mydict[i['requirement']] = trans_id
                            self.translation_values[trans_id] = j['trans']
                            if i['requirement'] in self.grouped:
                                myList = [trans_id, j['trans']]
                                self.grouped[i['requirement']].append(myList)
                except:
                    mydict[i['requirement']] = False
            elif i['type'] == 'Asset':
                try:
                    asset = db.myapp_asset.find({"id": i['value']})
                    for ast in asset:
                        mydict[i['requirement']] = "http://"+self.host+"/media/"+ast['photo']
                except Exception as e:
                    mydict[i['requirement']] = False
        return mydict

def add_item_requirement(grid,countries,host,translations,item,grouped):
    for i in grid:
        for j in i:
            arg = {
                "language":j,
                "countries":countries,
                "host":host,
                "translationValues":translations,
                "item":item,
                "grouped":grouped
            }
            item_req = ItemRequirements(arg)
            # print(blend_req.requirementvalues)
            i[j].update(item_req.requirementvalues)
            # print(item_req.requirementvalues)
            translations.update(item_req.translation_values)
            grouped.update(item_req.grouped)
    return (grid,translations,grouped)

def custom_condition_update(grid,data,language_translation,grouped):
    language_requirements = find_language_requirement(data['countries'])
    for i in grid:
        for j in i:
            custom = CustomCondition(data, j)
            new_custom = custom_condition_language_base(custom, language_requirements[j])
            custom_conditions = customTranslation(new_custom,j,language_translation,grouped)
            i[j].update(custom_conditions[0])
    return (grid,custom_conditions[1],custom_conditions[2])
    # print(grid,countries)

def find_language_requirement(country_list):
    languageList = []
    language_requirenents = {}
    for country in country_list:
        lang = list(db.country.find({"code": country}, {"_id": 0, "language": 1}))
        requirements = list(db.additional_requirement.find({"country": {"$in": [country]}, "static": True}).sort("order",1))
        for i in range(len(lang)):
            for l in lang[i]['language']:
                if l not in languageList:
                    languageList.append(l)
                    language_requirenents[l] = requirements
    return language_requirenents

def filter_grouped_translation(translation,data):
    for i in translation:

        key_to_check = i

        for item in data:
            if item[0] == key_to_check:
                for trans in translation[i]:
                    if trans[0] not in item:
                        new_list = [sublist for sublist in translation[i] if sublist != trans]
                        translation[i] = new_list
                break
        else:
            print(f"The key '{key_to_check}' is not present in the list at index 0.")
    return translation



weight_to_size = {
    "5-50": '2mm',
    "51-200": '3mm',
    "201-1000": '4mm'
}

def is_weight_range_match(test_range, ranges_list):
    if '-' in test_range:
        test_lower, test_upper = map(int, test_range.split('-'))
        for weight_range in ranges_list:
            if '-' in weight_range:
                lower, upper = map(int, weight_range.split('-'))
                if lower <= test_lower <= upper and lower <= test_upper <= upper:
                    return weight_range
    else:
        test_value = int(test_range)
        for weight_range in ranges_list:
            if '-' in weight_range:
                lower, upper = map(int, weight_range.split('-'))
                if lower <= test_value <= upper:
                    return weight_range
            else:
                if int(weight_range) == test_value:
                    return weight_range
    return None
