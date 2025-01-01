
from abc import ABC, abstractmethod
import requests

class CommonBroker(ABC):
    
    @abstractmethod
    def getPortfolio(self):
        """Retorna el portafolio del broker"""
        """El formato es Ticker,Name,Price (USD),Quantity,Price Change (USD),Price Change (%),Total Value (USD)"""
        pass
    
    def pesosToUsdCCL(self, pesos):
        """Convierte los pesos argentinos a CCL con precio de HOY (de compra)"""
        url = 'https://dolarapi.com/v1/dolares/contadoconliqui'

        response = requests.get(url)
        response.raise_for_status()
        dolar = response.json()['compra']
        return pesos / dolar


if __name__ == '__main__':
    raise Exception('No puedes ejecutar este archivo directamente. Impleméntalo')

