import requests
import webbrowser
import configparser
from flask import Flask, request, redirect
import requests
from urllib.parse import urlencode
import json
import time
import callbackserver
import traceback

config = configparser.ConfigParser()
config.read("myappinfo.ini")

# Your client ID and secret obtained from the EVE online ESI developer portal
CLIENT_ID = config.get("MyApp", "CLIENT_ID")
CLIENT_SECRET = config.get("MyApp", "CLIENT_SEACRET")
# The URL that the EVE online ESI will redirect to after authorization
REDIRECT_URL = config.get("MyApp", "CALLBACK_URL")

# The scopes you want to request access for
SCOPES = " ".join([x[1] for x in config.items("SCOPES")])

# OAuth 2.0 endpoints
AUTHORIZATION_URL = "https://login.eveonline.com/oauth/authorize"
TOKEN_URL = "https://login.eveonline.com/oauth/token"
ID_URL = "https://esi.evetech.net/latest/universe/ids/?datasource=tranquility&language=en"

TRIPWIRE_CONNECTOR_URL = "http://localhost:8899"

class Character: 
    #Character based on my server response
    _user_id = None
    _character_id = None
    _character_name = None
    _access_token = None   
    _access_token_timer = None
    
    def _get_access_token(self): 
        payload= {
            "mode": "token",
            "user_id": self._user_id
        }
        
        response = requests.post(TRIPWIRE_CONNECTOR_URL, data=payload)
        if(response.status_code != 200):
            print("Error when trying to get access token")
            print(response.text)
            return None
        
        if(self._user_id != response.json()["user_id"]):
            print("No idea how, but you got the response from another user! This should NEVER have happened! Pls contact administrator")
            return None        
        return response.json()["access_token"]

    def _createNewUser(self):
        authorization_params = {
            "response_type": "code",
            "client_id": CLIENT_ID,
            "scope": SCOPES,
            "redirect_uri": REDIRECT_URL,
        }
        authorization_url = f"{AUTHORIZATION_URL}?{urlencode(authorization_params)}" 
        #open EVE login dialogue
        webbrowser.open(authorization_url)
        # Wait for the user to authorize the application
        authorization_code = callbackserver.getAuthToken() 
        if(authorization_code == None):
            print("Callback server returned invalid argument!")
            return None
        
        payload = {
            "mode": "init",
            "authtoken": authorization_code 
        }    
        
        try: 
            response = requests.post(TRIPWIRE_CONNECTOR_URL, data=payload)
            if(response.status_code != 201): 
                print("An error occured on the server")
                print(response.text)
                return
        except Exception as e:
            print("An error occured:", str(e))
            traceback.print_exc()

        try:
            self._user_id = response.json()["user_id"]
            self._character_id = response.json()["CharacterID"]
            self._character_name = response.json()["CharacterName"]
            self._access_token = response.json()["access_token"]
            self._access_token_timer = time.time()
        except: 
            print("Server responeded with 201, but payload did not contain all or any required data!")
            return None
        
        users = []
        try: 
            with open("data.json", "r") as file:
                users = json.load(file)
        except json.decoder.JSONDecodeError:
            print("The data.json file so far is empty, creating 1st user")
        
        user = {
            "user_id": self._user_id,
            "character_id": str(self._character_id),
            "character_name": self._character_name
        }
        
        users.append(user)
        with open("data.json", "w") as file:
            json.dump(users, file)   
        return
        
    def _loadUser_with_id(self, character_id):
        with open("data.json", "r") as file:
            users = json.load(file)
            
        for user in users:
            if(user["character_id"] == character_id):
                self._user_id = user["user_id"]
                self._character_id = user["character_id"]
                self._character_name = user["character_name"]
                self._access_token = self.access_token()
                self._access_token_timer = time.time()
                print(f"Loaded character: {self._character_name}")
                return 1 
        else: 
            print("Did not find character!")
            return None

    def _loadUser_with_name(self, character_name):
        with open("data.json", "r") as file:
            users = json.load(file)
            
        for user in users:
            if(user["character_name"] == character_name):
                self._user_id = user["user_id"]
                self._character_id = user["character_id"]
                self._character_name = user["character_name"]
                self._access_token = self.access_token()
                self._access_token_timer = time.time()
                print(f"Loaded character: {self._character_name}")
                return 1 
        else: 
            print("Did not find character!")
            return None

    def loadUser(self, character_id=None, character_name=None):
        if(character_id != None): 
            try:
                return self._loadUser_with_id(character_id=character_id)
            except Exception as e:
                print("An error occured:", str(e))
                traceback.print_exc()
                return None
        elif(character_name != None):
            try:
                return self._loadUser_with_name(character_name=character_name)
            except Exception as e:
                print("An error occured:", str(e))
                traceback.print_exc()
                return None
        elif(character_id==None and character_name==None):
            return self._createNewUser()
        else:
            print("Load user happened something that aint supposed to happen!")
            return None

    def access_token(self): #todo - check that this aint looping to death!!! - server has to return more information for this though...
        #if no timer is set, get new access token
        if(self._access_token_timer == None):
            self._access_token = self._get_access_token()
            self._access_token_timer = time.time()
            return self.access_token()
        
        elapsed_time = time.time() - self._access_token_timer
        if(elapsed_time > 18*60):
            #variable expired / almost expired
            self._access_token = self._get_access_token()
            self._access_token_timer = time.time()
            return self.access_token()
        else: 
            return self._access_token
    
    def get_char_id(self):
        try:
            return self._character_id
        except:
            print("No Character defined!")
            return None
    
    def get_char_name(self):
        try:
            return self._character_name
        except:
            print("No Character defined")
            return None
    
    def getLocation(self):
        char_id = self.get_char_id()
        token = self.access_token() 
        if char_id is None or token is None:
            print("Get location abborted!")
            print(f"Character_id: {char_id}")
            print(f"Access_token: {token}")
            return None
        
        LOCATION_URL = f"https://esi.evetech.net/latest/characters/{char_id}/location/?datasource=tranquility&token={token}"
        
        response = requests.get(LOCATION_URL)
        if(response.status_code == 200): 
            return response.json()["solar_system_id"]
        else:
            print("Could not get location")
            print(response.status_code)
            return self.getLocation()
