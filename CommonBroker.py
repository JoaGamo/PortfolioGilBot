
from abc import ABC, abstractmethod

class CommonBroker(ABC):
    
    @abstractmethod
    def getPortfolio():
        """Retorna el portafolio del broker"""
        """El formato es Ticker,Name,Price (USD),Quantity,Price Change (USD),Price Change (%),Total Value (USD)"""
        pass



if __name__ == '__main__':
    raise Exception('No puedes ejecutar este archivo directamente. Impleméntalo')

