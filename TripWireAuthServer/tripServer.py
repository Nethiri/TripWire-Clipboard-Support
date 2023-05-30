from http.server import HTTPServer ,BaseHTTPRequestHandler
import urllib.parse as urlparse
import json, sys, configparser, uuid, requests


config = configparser.ConfigParser()
config.read("serverConfig.ini")

PORT = int(config.get("BASE", "PORT"))
HOST = config.get("BASE", "HOST")
CLIENT_ID = config.get("MyApp", "CLIENT_ID")
CLIENT_SECRET = config.get("MyApp", "CLIENT_SEACRET")
REDIRECT_URL = config.get("MyApp", "CALLBACK_URL")
TOKEN_URL = config.get("MyApp", "TOKEN_URL")
VERIFY_URL = config.get("MyApp", "VERIFY_URL")
SCOPES = " ".join([x[1] for x in config.items("SCOPES")])


validKeys = ["init", "getlocation"]

class TripWireService(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse.urlparse(self.path)
        
        payload = urlparse.parse_qs(url.query)
         #["code"][0]["code"][0]
        keys = payload.keys()
        # test link: http://localhost:8899/?code=TPWxshEQSgdwvOPF7loN9cZSv_TTG84w0iBJyUWZKQz9jpJ3bs2lnZuIXugVZoHt
        print(keys)
        print(type(keys))
        print(len(keys))
                
        self.wfile.write(f"Payload: {payload}".encode())
        self.send_response(200)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        payload = urlparse.parse_qs(body.decode('utf-8'))
        
        #check for the type of post, weather its an init or a request for a token, ...
        modelist = payload.get("mode")

        if("init" in modelist): self.init_character(payload)
        elif("token" in modelist): self.send_token(payload)
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'No valid mode detected')
        return
    
    def init_character(self, in_payload):
        #create a new user, and use the authtoken to get 20min and refresh token for the user
        #that way, i dont have to share client_seacret
        authtoken = ""
        try:
            authtoken = in_payload.get("authtoken")[0]
        except:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'No authtoken in data')
            return
        
        #generate unique user id:
        user_id = str(uuid.uuid4())
        
        users = []   
        try: 
            with open("data.json", "r") as file:
                users = json.load(file)
        except json.decoder.JSONDecodeError:
            print("The data.json file so far is empty, creating 1st user")
                    
        #check if user_id already exists...
        for user in users:
            if user["user_id"] == user_id:
                #user could not be created because uuid gave the same id twice...
                #UNLIKELY... but fuck it... I check anyway...
                #retry til we get a new id :D
                #I wont even throw an error for that and JUST try again... like... this unlikely...
                return self.init_character(self, in_payload)

        #prepare request to eve to generate refresh- and temp-token
        token_params = {
            "grant_type": "authorization_code",
            "code": authtoken,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URL,
        }
        #do the request and respond if there is an error
        response = requests.post(TOKEN_URL, data=token_params)
        if(response.status_code != 200): 
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'An error occured: {response.text}'.encode())
            return
        
        access_token = None
        refresh_token = None
        
        try:
            access_token = response.json()["access_token"]
            refresh_token = response.json()["refresh_token"]
        except: 
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Extracting access and refresh token was not possible?!')
            return
        
        verify_headers = {
            'Authorization': 'Bearer ' + access_token
        }
        response = requests.get(VERIFY_URL, headers=verify_headers)
        if(response.status_code != 200):
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'Could not Verify token. An error occured: {response.text}'.encode())
            return
        
        character_id = None
        character_name = None
        
        try:
            character_id = response.json()["CharacterID"]
            character_name = response.json()["CharacterName"]
        except:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Verifying Token was not possible No CharacterID or CharacterName in response?!')
            return
        
        new_user = {
        "user_id": user_id,
        "CharacterID": character_id, 
        "CharacterName": character_name,
        "original_auth_token": authtoken, 
        "refresh_token": refresh_token,
        "last_access_token": access_token
        }
        
        #add new user to users database
        users.append(new_user)
        
        with open("data.json", "w") as file:
            json.dump(users, file)      

        self.send_response(201) #server succesfully created a new resource based on the request
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        payload = {
            "user_id": user_id,
            "CharacterID": character_id,
            "CharacterName": character_name,
            "access_token": access_token
        }      
        
        self.wfile.write(json.dumps(payload).encode())
        return
    
    
    def send_token(self, payload):
        #client contacts the server to recieve a token he can use for 20 minutes to make api requests
        user_id = None
        try:
            user_id = payload.get("user_id")[0]
        except:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'No user_id provided')
            return
        #load exisiting users
        with open("data.json", "r") as file:
            users = json.load(file)
        
        request_user = None
        for user in users: 
            if user["user_id"] == user_id:
                request_user = user
                break
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Invalid user_id provided')    

        #prepare payload to get new token for the user   
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": request_user["refresh_token"],
            "client_id": CLIENT_ID, 
            "scope": SCOPES
        }
        #do request to eve servers, if not 200 end here
        response = requests.post(TOKEN_URL, data=payload)
        if(response.status_code != 200):
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'An error occured: {response.text}'.encode())
            return
        
        #try to take appart response to get a possible new refresh token and the access token        
        try:
            for user in users: 
                if user["user_id"] == user_id:
                    user["refresh_token"] = response.json()["refresh_token"]
                    user["last_access_token"] = response.json()["access_token"]
                    break
            #save both refresh- and access-token in database
            with open("data.json", "w") as file:
                json.dump(users, file)
        except: 
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Extracting access and refresh token was not possible?!')
            return

        #send response to client with the new access token
        self.send_response(200) 
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        payload = {
            "user_id": user_id,
            "access_token": response.json()["access_token"]
        }      
        self.wfile.write(json.dumps(payload).encode())
        return
    
    
def server_shutdown(server):
    server.server_close()
    sys.exit(0)


def main(): 
    server_instance = HTTPServer((HOST, PORT), TripWireService)
    print('Server running on port %s.' % PORT)
    try:
        server_instance.serve_forever()
    except KeyboardInterrupt:
        server_shutdown(server_instance)
        pass

if __name__ == "__main__":
    main()    