import configparser
from flask import request, redirect
from urllib.parse import urlencode
import urllib.parse as urlparse
import http.server
import socketserver

config = configparser.ConfigParser()
config.read("myappinfo.ini")

CLIENT_ID = config.get("MyApp", "CLIENT_ID")
REDIRECT_URI = config.get("MyApp", "CALLBACK_URL")

SCOPE = " ".join([x[1] for x in config.items("SCOPES")])

PORT = 8000

class AuthorizationHandler(http.server.SimpleHTTPRequestHandler):
    authorization_code = None
        
    def do_GET(self):
        # Extract the authorization code from the query parameters  
        url = self.path
        print(url)
        parsed = urlparse.urlparse(url)
        captured_value = urlparse.parse_qs(parsed.query)['code'][0]
        
        self.authorization_code = captured_value
        
        # Send a response to the browser
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body><p>Authorization successful. You can close this window now.</p></body></html>")
        self.server.authorization_code = self.authorization_code
        self.server.server_close()
        
def getAuthToken(): 
    with socketserver.TCPServer(("", PORT), AuthorizationHandler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except:
            pass      
        print("Server has been shut down!")
    return httpd.authorization_code 

# will normally never happen!
if __name__ == "__main__":
    print("Auth Token: " + getAuthToken())