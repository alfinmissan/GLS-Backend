

def blendHistory(new,old):

    action = ''
    if old['name'] != new['name']:
        if action =='':
            action = 'changed '
        action += " blend name  " +old['name'] + " to " + new['name']
    if old['blend_loose'] != new['blend_loose']:
        if action =='':
            action = 'edited '+new['name']
        else:
            action += " and "
        action += " blend loose tea  " + old['blend_loose'] + " to " + new['blend_loose']
    if old['blend_tea_bag'] != new['blend_tea_bag']:
        if action =='':
            action = 'edited '+new['name']
        else:
            action += " and "
        action += " blend loose tea  " + old['blend_tea_bag'] + " to " + new['blend_tea_bag']
    if old['ingredient_loose'] != new['ingredient_loose']:
        if action =='':
            action = 'edited '+new['name']
        else:
            action += " and "
        action += " blend loose tea  " + old['ingredient_loose'] + " to " + new['ingredient_loose']
    if old['ingredient_tea_bag'] != new['ingredient_tea_bag']:
        if action =='':
            action = 'edited '+new['name']
        else:
            action += " and "
        action += " blend loose tea  " + old['ingredient_tea_bag'] + " to " + new['ingredient_tea_bag']
    if old['tea_origin'] != new['tea_origin']:
        if action =='':
            action = 'edited '+new['name']
        else:
            action += " and "
        action += " blend loose tea  " + old['tea_origin'] + " to " + new['tea_origin']
    if old['range'] != new['range']:
        if action =='':
            action = 'edited '+new['name']
        else:
            action += " and "
        action += " Range " + old['range'] + " to " + new['range']
    return action

def countryHistory(new,old):
    action = ''
    if old['code'] != new['code']:
        if action =='':
            action = 'changed '
        action += "country " +old['code'] + " to " + new['code']
    if old['name'] != new['name']:
        if action == '':
            action = "changed "
        else:
            action += " and "
        action +=old['name'] + " to " + new['name']
    if old['language'] != new['language']:
        if action == '':
            action = 'edited modified in ' + new['code']
        else:
            action += " and modified languages"
        action +=""
    return action

def factoryHistory(new,old):
    action = ''
    if old['location'] != new['location']:
        if action == '':
            action = 'changed '
        action += "factory " + old['location']['label'] + " to " + new['location']['label']
    if old['packed_in'] != new['packed_in']:
        if action == '':
            action = " edited " + new['location']['label']
        else:
            action += " and "
        action += " packed in translation " + old['packed_in']['label'] + " to " + new['packed_in']['label']
    if old['address'] != new['address']:
        if action == '':
            action = 'edited ' + new['location']['label']
        else:
            action += " factory address translation " + old['address']['label'] + " to " + new['address']['label']
        action += ""
    return action

def legalnameHistory(new,old):
    action = ''
    if old['name'] != new['name']:
        if action == '':
            action = 'changed '
        action += "legal name " + old['name'] + " to " + new['name']
    if old['translation'] != new['translation']:
        if action == '':
            action = " edited " + new['name']
        else:
            action += " and "
        action += " english text mastercode " + old['translation'] + " to " + new['translation']
    return action

def itemNumberHistory(new,old):
    action = ''
    if old['item'] != new['item']:
        if action == '':
            action = 'changed '
        action += " item  " + str(old['item']) + " to " + str(new['item'])
    if old['category'] != new['category']:
        if action == '':
            action = 'edited item number' + str(new['item'])
        else:
            action += " and "
        action += " category " + old['category'] + " to " + new['category']
    return action

def regnumberHistory(new,old):
    action = ''
    if old['country'] != new['country']:
        if action == '':
            action = "changed "
        else:
            action += " and "
        action += " country name " + old['country'] + " to " + new['country']
    if old['registration'] != new['registration']:
        if action == '':
            action = 'changed '
        action += "regitration number of "+old['country'] +" "  + old['registration'] + " to " + new['registration']
    return action

def requirementHistory(new,old):
    action = ''
    if old['requirement'] != new['requirement']:
        if action =='':
            action = 'changed '
        action += " requirement  " +'"'+old['requirement'] +'"' + " to "+'"' + new['requirement'] +'"'
    if old['type'] != new['type']:
        if action =='':
            action = 'edited ' + new['requirement']
        else:
            action += " and "
        action += " type  "  +'"'+ old['type']  +'"'+ " to " +'"'+ new['type'] +'"'
    if old['value'] != new['value']:
        if new['type'] != 'Asset':
            if action =='':
                action = 'edited '+ new['requirement']
            else:
                action += " and "
            action += " value  " +'"' + old['value'] +'"' + " to " +'"'+ new['value']+'"'
    if old['country'] != new['country']:
        if action =='':
            action = 'edited '+new['requirement']
        else:
            action += " and "
        action += " country list  "+'"' + ",".join(old['country']) +'"'+ " to "+'"' + ",".join(new['country'])+'"'
    if old['static'] != new['static']:
        if action =='':
            action = 'changed '+new['requirement']
        else:
            action += " and "
        if old['static']:
            action += " requirement static requirement to None static requirement"
        else:
            action += " requirement None static requirement to static requirement"

    return action

def ItemRequirementHistory(new,old):
    print(old,new)
    action = ''
    if old['requirement'] != new['requirement']:
        if action == '':
            action = 'changed '
        action += " requirement  " + '"' + old['requirement'] + '"' + " to " + '"' + new['requirement'] + '"'
    if old['type'] != new['type']:
        if action == '':
            action = 'edited ' + new['requirement']
        else:
            action += " and "
        action += " type  " + '"' + old['type'] + '"' + " to " + '"' + new['type'] + '"'
    if old['value'] != new['value']:
        if action == '':
            action = 'edited ' + new['requirement']
        else:
            action += " and "
        action += " value  " + '"' + old['value'] + '"' + " to " + '"' + new['value'] + '"'
    if old['country'] != new['country']:
        if action == '':
            action = 'edited ' + new['requirement']
        else:
            action += " and "
        action += " country list  " + '"' + ",".join(old['country']) + '"' + " to " + '"' + ",".join(
            new['country']) + '"'

    return action

def BlendRequirementHistory(new,old):
    action = ''
    if old['requirement'] != new['requirement']:
        if action == '':
            action = 'changed '
        action += " requirement  " + '"' + old['requirement'] + '"' + " to " + '"' + new['requirement'] + '"'
    if old['type'] != new['type']:
        if action == '':
            action = 'edited ' + new['requirement']
        else:
            action += " and "
        action += " type  " + '"' + old['type'] + '"' + " to " + '"' + new['type'] + '"'
    if old['value'] != new['value']:
        if action == '':
            action = 'edited ' + new['requirement']
        else:
            action += " and "
        action += " value  " + '"' + old['value'] + '"' + " to " + '"' + new['value'] + '"'
    if old['category'] != new['category']:
        if action == '':
            action = 'edited ' + new['requirement']
        else:
            action += " and "
        action += "category  " + '"' + old['category'] + '"' + " to " + '"' + new['category'] + '"'
    if old['country'] != new['country']:
        if action == '':
            action = 'edited ' + new['requirement']
        else:
            action += " and "
        action += " country list  " + '"' + ",".join(old['country']) + '"' + " to " + '"' + ",".join(
            new['country']) + '"'

    return action