
import requests
from CommonBroker import CommonBroker


class IOLClient(CommonBroker):
    def __init__(self, **kwargs):
        self.usuario = kwargs.get('usuario')
        self.contrasena = kwargs.get('contrasena')
        self.access_token = None
        self.refresh_token = None
        
        
    def _init_tokens(self):
        url = "https://api.invertironline.com/token"
        payload = {
            "grant_type": "password",
            "username": self.usuario,
            "password": self.contrasena,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        tokens = response.json()
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]


    def _reset_tokens(self):
        url = "https://api.invertironline.com/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = requests.post(url, data=payload, headers=headers)
        response.raise_for_status()
        tokens = response.json()
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]


    def _asegurar_token_valido(self): # type: ignore
        if not self.access_token:
            self._init_tokens()
        try:
            return self.access_token
        except requests.exceptions.HTTPError:
            self._reset_tokens()
            return self.access_token

    def getPortfolio():
        pass
        
    
    