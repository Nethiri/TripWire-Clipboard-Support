import requests
import configparser

import signatures

LOGIN_URL = "https://tripwire.synde.space/login.php"
REFRESH_URL = "https://tripwire.synde.space/refresh.php"

config = configparser.ConfigParser()
config.read("myappinfo.ini")

class Tripwire:
    _Cookie = None
    _Auth_Response = None
    _Session = None
    _Usrn = None
    _Pasw = None
    
    #Loggin into Tripwire Client, with username and password
    def login(self, usrn, pasw):
        self._Usrn = usrn
        self._Pasw = pasw
        return self._login()
    
    #Loggin in while username and password already exist
    def _login(self):
        payload = {
            "mode": "login",
            "username": self._Usrn,
            "password": self._Pasw
        }
        
        headers = {
            "Referer": LOGIN_URL,
            "User-Agent": config.get("MyApp", "APP_NAME"),
            "Accept-Encoding": "gzip, deflate, br"
        }
        
        response = requests.post(LOGIN_URL, data=payload, headers=headers)
        
        if(response.status_code == 200): 
            #Trip-Response
            if(response.text == ""):
                print("Payload Error!!!")
                return 0
            try:
                print("Error: " + response.json()["error"])
                return 0
            except:
                print("Login successful, Cookie saved")
                self._Cookie = response.cookies
                self._Auth_Response = response
                return 1
            
        print("Wrong server Response, Error code: " + response.status_code)
        return 0
    
    #generating a new session, with access token (in form of cookie) to auth later html requests
    def createSession(self):
        if(self._Cookie == None):
            print("Error, No Login-cookie")
            return 0
        session = requests.Session()
        session.cookies.update({"PHPSESSID": self._Cookie.get("PHPSESSID")})
        self._Session = session
    
    #creating a new session as old one might have died
    def _getNewSession(self):
        if(self._login(self) == 0):
            print("Could not log in successful!")
            return 0
        if(self.createSession(self) == 0): 
            print("Could not create Session!")
            return 0
        return 1
        
    #retrive a list of all signatures from the mapper in the given system
    def getSystemSignatures(self, system_id):
        if(self._Session == None): self.createSession(self)
        
        payload = {
            "mode": "refresh", 
            "systemID": system_id
        }
        
        response = self._Session.post(REFRESH_URL, data=payload)
        if(response.status_code == 200):
            if(response.json()["signatures"] == []): return [] #no signatures found
            global_signatures = [{"systemID": x["systemID"], "type": x["type"], "id": x["id"], "signatureID": x["signatureID"], "name": x["name"]} for x in response.json()["signatures"].values()]
            system_sigs = [{"systemID": x["systemID"], "type": x["type"], "id": x["id"], "signatureID": x["signatureID"], "name": x["name"]} for x in global_signatures if x["systemID"]==payload["systemID"]]
            return system_sigs
        else:
            print("Session token no longer valid... creating new one")
            if(self._getNewSession() == 0): 
                print("Could not fetch System Signatures")
                return None #HANDLE None RETURN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            return self.getSystemSignatures(system_id)
    
    #update signatures on tripwire
    def updateSignatures(self, system_id, sigs_add, sigs_rem):
        #prepare payload preamble      
        payload = {
            "systemID": str(system_id),
            "mode": "refresh",            
        }
        
        #add all signatures which need to be added on tripwire into the request payload
        sig_counter = 0
        for sig in sigs_add:
            payload[f"signatures[add][{sig_counter}][signatureID]"]  = sig["signatureID"]
            payload[f"signatures[add][{sig_counter}][systemID]"]     = str(system_id)
            payload[f"signatures[add][{sig_counter}][type]"]         = sig["type"]
            payload[f"signatures[add][{sig_counter}][name]"]         = sig["name"]
            payload[f"signatures[add][{sig_counter}][lifeLength]"]   = sig["lifeLengh"]
            sig_counter = sig_counter + 1  
        #add all signatures which need to be removed on tripwire into the request payload
        sig_counter = 0
        for sig in sigs_rem:
            payload[f"signatures[remove][{sig_counter}]"]            = sig["id"]
            sig_counter = sig_counter + 1
        #doing the request        
        response = self._Session.post(REFRESH_URL, data=payload)
        if(response.status_code == 200):
            print("Signatures updated")
        else:
            print("Updating Signatures failed... creating new token to try again")
            if(self._getNewSession() == 0):
                print("Could not Update Signatures!")
                return None #HANDLE None RETURN!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            return self.updateSignatures(system_id=system_id, sigs_add=sigs_add,sigs_rem=sigs_rem)
        return 1