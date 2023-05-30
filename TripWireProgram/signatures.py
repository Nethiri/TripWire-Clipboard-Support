VALID_SIG_PREAMBLE = {
    #English (en-us)
    "Cosmic Signature": "Cosmic Signature" ,
    "Cosmic Anomaly": "Cosmic Anomaly",

    #French (fr)
    "Signature cosmique": "Cosmic Signature",
    "Anomalie cosmique": "Cosmic Anomaly",

    #German (de)
    "Kosmische Anomalie": "Cosmic Signature",
    "Kosmische Signatur": "Cosmic Anomaly",

    #Japanese (ja)
    "宇宙の特異点": "Cosmic Signature",
    "宇宙のシグネチャ": "Cosmic Anomaly",

    #Korean (ko)
    "코즈믹 시그니처": "Cosmic Signature",
    "코즈믹 어노말리": "Cosmic Anomaly",

    #Russian (ru)
    "Скрытый сигнал": "Cosmic Signature",
    "Космическая аномалия": "Cosmic Anomaly",
}

VALID_TYPES = {
    #general
    "": "unknown",
    
    #English (en-us)
    "Combat Site": "Combat",
    "Data Site": "Data",
    "Gas Site": "Gas",
    "Ore Site": "Ore",
    "Relic Site": "Relic",
    "Wormhole": "Wormhole",

    #French (fr)
    "Site de combat": "Combat",
    "Site de données": "Data",
    "Site de collecte de gaz": "Gas",
    "Site de minerai": "Ore",
    "Site de reliques": "Relic",
    "Trou de ver": "Wormhole",

    #German (de)
    "Kampfgebiet": "Combat",
    "Datengebiet": "Data",
    "Gasgebiet": "Gas",
    "Mineraliengebiet": "Ore",
    "Reliktgebiet": "Relic",
    "Wurmloch": "Wormhole",

    #Japanese (ja)
    "戦闘サイト": "Combat",
    "データサイト": "Data",
    "ガスサイト": "Gas",
    "鉱石サイト": "Ore",
    "遺物サイト": "Relic",
    "ワームホール": "Wormhole",

    #Korean (ko)
    "전투 사이트": "Combat",
    "데이터 사이트": "Data",
    "가스 사이트": "Gas",
    "채광 사이트": "Ore",
    "유물 사이트": "Relic",
    "웜홀": "Wormhole",

    #Russian (ru)
    "Боевой район": "Combat",
    "Информационный район": "Data",
    "Газовый район": "Gas",
    "Астероидный район": "Ore",
    "Археологический район": "Relic",
    "Червоточина": "Wormhole",
}
#parse constants
TABLE = {
    "signatureID": 0,
    "cosmic": 1,
    "type": 2,
    "name": 3,
    "scanpercent": 4,
    "distance": 5    
}



def parseClipboard(dump):
    lines = dump.split("\n")
    table = [l.split("\t") for l in lines]
    return table
    
#converts one signature from the parse list into a usable form
def convParse(sig, SystemID): 
    try: #type might be something wonky like ship or deployable... then it should return 0
        lifeDuration = 172800
        if(VALID_TYPES[sig[TABLE["type"]]] == "Combat"): lifeDuration = 259200
        name = None
        if(sig[TABLE["name"]] != ""): name = sig[TABLE["name"]]
        x,y = sig[TABLE["signatureID"]].split("-")
        sigId = str.lower(x) + y

        ret = {
            "signatureID": sigId,
            "systemID": str(SystemID),
            "type": VALID_TYPES[sig[TABLE["type"]]],
            "name": name,
            "lifeLengh": lifeDuration
        }
        return ret
    except: return None 

#converts a tripwire signature into a usable form
def convertTrigSig(sig):
    ret = {
        "signatureID": sig["signatureID"],
        "systemID": sig["systemID"],
        "type": sig["type"],
        "name": sig["name"],
        "id": sig["id"]
    }
    return ret


def prepareUploadData(tripwireSignatures, clipboardParse, SystemID):
    SigsToAdd = []
    SigsToRemove = []
    SigsToIgnore = []
    
    tripSig_list = []
    clipboardParse_list = []
    
    for tripSig in tripwireSignatures: 
        tripSig_list.append(convertTrigSig(tripSig))
    for clipSig in clipboardParse:
        sig = convParse(clipSig, SystemID)
        if(sig == None): continue #whatever has been found, is not a valid signature
        clipboardParse_list.append(sig)
        
    for clipSig in clipboardParse_list:
        sigFound = False
        for trigSig in tripSig_list:
            if(trigSig["signatureID"] == "None"): 
                #no touchy!!! This is a signature (most likely wormhole) which has not been scanned down and asigned a signtature... someone was lazy... dont touch! But get someone there to scan propperly... Or scan faster... either way!
                SigsToIgnore.append(trigSig)
                tripSig_list.remove(trigSig)            
                continue
            
            if(clipSig["signatureID"] == trigSig["signatureID"]): 
                #found signature exists already on the mapper
                sigFound = True
                SigsToIgnore.append(trigSig)
                tripSig_list.remove(trigSig)
                clipboardParse_list.remove(clipSig)                
                break
        #clipboard signature could not be mapped onto a tripwire signature... add signature
        if(sigFound == False):    
            SigsToAdd.append(clipSig)
            clipboardParse_list.remove(clipSig)
    #any tripwire signature still in tripSig_list is not found on the clipboard... hence is no longer existing (collapsed/despawned) - remove
    SigsToRemove = tripSig_list
           
    return SigsToAdd, SigsToRemove, SigsToIgnore


    
    
    
    
    

    #tripwireSignatures: 
    #[{'systemID': '31002437',  'type': 'data',  'id': '1182765',  'signatureID': 'zrv050'},
    # {'systemID': '31002437',  'type': 'data',  'id': '1182766',  'signatureID': 'fly444'},
    # {'systemID': '31002437',  'type': 'data',  'id': '1183971',  'signatureID': 'kxe728'},
    # {'systemID': '31002437',  'type': 'wormhole',  'id': '1183976',  'signatureID': 'gtl552'},
    # {'systemID': '31002437',  'type': 'wormhole',  'id': '1184903',  'signatureID': 'qvh916'},
    # {'systemID': '31002437',  'type': 'data',  'id': '1185246',  'signatureID': 'tka965'},
    # {'systemID': '31002437',  'type': 'wormhole',  'id': '1186018',  'signatureID': None}]
    #clipboardParse
    #[['KOO-320',  'Cosmic Anomaly',  'Ore Site',  'Average Frontier Deposit',  '100,0%',  '12,47 AU'],
    # ['OVL-932',  'Cosmic Anomaly',  'Ore Site',  'Common Perimeter Deposit',  '100,0%',  '24,63 AU'],
    # ['ZDI-470',  'Cosmic Anomaly',  'Combat Site',  'Core Bastion',  '100,0%',  '10,92 AU'],
    # ['GZF-860',  'Cosmic Anomaly',  'Combat Site',  'Core Bastion',  '100,0%',  '12,68 AU'],
    # ['NNK-992',  'Cosmic Anomaly',  'Combat Site',  'Core Bastion',  '100,0%',  '12,10 AU'],
    # ['IFY-438',  'Cosmic Anomaly',  'Combat Site',  'Core Bastion',  '100,0%',  '12,34 AU'],
    # ['DKV-487',  'Cosmic Anomaly',  'Combat Site',  'Core Bastion',  '100,0%',  '24,73 AU'],
    # ['ZYP-387',  'Cosmic Anomaly',  'Combat Site',  'Core Bastion',  '100,0%',  '9,56 AU'],
    # ['SXO-616',  'Cosmic Anomaly',  'Combat Site',  'Core Citadel',  '100,0%',  '10,27 AU'],
    # ['ZRV-050', 'Cosmic Signature', '', '', '0,0%', '12,19 AU'],
    # ['GTL-552', 'Cosmic Signature', '', '', '0,0%', '14,02 AU'],
    # ['FLY-444', 'Cosmic Signature', '', '', '0,0%', '26,83 AU'],
    # ['QVH-916', 'Cosmic Signature', '', '', '0,0%', '13,44 AU'],
    # ['BFZ-162', 'Cosmic Signature', '', '', '0,0%', '14,89 AU'],
    # ['KXE-728', 'Cosmic Signature', '', '', '0,0%', '13,40 AU'],
    # ['TKA-965', 'Cosmic Signature', '', '', '0,0%', '13,25 AU'],
    # ['JNT-486',  'Cosmic Anomaly',  'Combat Site',  'Strange Energy Readings',  '100,0%',  '14,41 AU'],
    # ['GYY-850',  'Cosmic Anomaly',  'Combat Site',  'Strange Energy Readings',  '100,0%',  '14,30 AU'],
    # ['KSC-524',  'Cosmic Anomaly',  'Combat Site',  'Strange Energy Readings',  '100,0%',  '3,95 AU'],
    # ['ZUX-348',  'Cosmic Anomaly',  'Combat Site',  'Strange Energy Readings',  '100,0%',  '10,93 AU'],
    # ['FKT-480',  'Cosmic Anomaly',  'Combat Site',  'The Mirror',  '100,0%',  '10,16 AU'],
    # ['YTR-024',  'Cosmic Anomaly',  'Combat Site',  'The Mirror',  '100,0%',  '11,20 AU']]
        
    
        
    
    
    # function that turns this
    
    #"ZGF-267\tCosmic Signature\t\t\t0,0%\t90,55 AU\nNFV-001\tCosmic Signature\t\t\t0,0%\t41,98 AU\nRVA-175\tCosmic Signature\t\t\t0,0%\t40,80 AU\nOAD-234\tCosmic Signature\t\t\t0,0%\t42,98 AU"
    
    # into this
    
    #ZGH-045	Cosmic Signature			0,0%	14,81 AU
    #VKU-242	Cosmic Signature			0,0%	14,01 AU
    #FLY-444	Cosmic Signature	Data Site	Unsecured Core Emergence 	100,0%	25,85 AU
    
    #to this
    #"signatures[add][0][signatureID]":	"ZRV050",
    #"signatures[add][0][systemID]":	"31001746",
    #"signatures[add][0][type]":	"unknown",
    #"signatures[add][0][lifeLength]":	"172800",
    
    #"signatures[add][1][signatureID]": "VKU242",
    #"signatures[add][1][systemID]": "31001746",
    #"signatures[add][1][type]":	"unknown",
    #"signatures[add][1][lifeLength]": "172800",
    
    #"signatures[add][2][signatureID]": "FLY444",
    #"signatures[add][2][systemID]": "31001746",
    #"signatures[add][2][type]":	"Data",
    #"signatures[add][2][name]":	"Unsecured Core Emergence", #"Unsecured+Core+Emergence"
    #"signatures[add][2][lifeLength]":"172800",
    