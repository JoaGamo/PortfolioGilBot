import requests
from CommonBroker import CommonBroker


class IOLClient(CommonBroker):
    def __init__(self, **kwargs):
        self.usuario = kwargs.get('usuario')
        self.contrasena = kwargs.get('contrasena')
        self.CUENTA_USA = kwargs.get('CUENTA_USA') or False
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

    def request_portfolio(self, usa: bool = False):
        url = "https://api.invertironline.com/api/v2/portafolio/argentina"
        if usa:
            url = "https://api.invertironline.com/api/v2/portafolio/estados_Unidos"
        headers = {
            "Authorization": f"Bearer {self._asegurar_token_valido()}"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def _process_asset(self, activo):
        """Procesa un activo individual y retorna el formato estandarizado"""
        # Determinar si necesitamos convertir la moneda
        needs_conversion = activo['titulo']['moneda'].lower() == 'peso_argentino'
        
        # Convertir precios si es necesario
        price = activo['ultimoPrecio']
        total_value = activo['valorizado']
        
        if needs_conversion:
            price = self.pesosToUsdCCL(price)
            total_value = self.pesosToUsdCCL(total_value)
            
        price_change_usd = price * (activo['variacionDiaria'] / 100)
        
        return {
            'Ticker': activo['titulo']['simbolo'],
            'Name': activo['titulo']['descripcion'],
            'Price (USD)': price,
            'Quantity': activo['cantidad'],
            'Price Change (USD)': price_change_usd,
            'Price Change (%)': activo['variacionDiaria'],
            'Total Value (USD)': total_value
        }

    def _process_portfolio(self, portfolio):
        """Procesa una cartera completa y retorna lista de activos en formato estandarizado"""
        result = []
        if portfolio and 'activos' in portfolio:
            for activo in portfolio['activos']:
                result.append(self._process_asset(activo))
        return result

    def getPortfolio(self):
        """Obtiene y combina los portfolios de Argentina y USA"""
        portfolio = self.request_portfolio()
        portfolio_usa = self.request_portfolio(usa=self.CUENTA_USA)
        
        result = []
        result.extend(self._process_portfolio(portfolio))
        result.extend(self._process_portfolio(portfolio_usa))
        
        return result






