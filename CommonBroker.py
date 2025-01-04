from abc import ABC, abstractmethod
import pandas as pd
import requests

class CommonBroker(ABC):
    PORTFOLIO_COLUMNS = [
        'Ticker', 'Name', 'Price (USD)', 'Quantity', 
        'Price Change (USD)', 'Price Change (%)', 'Total Value (USD)'
    ]
    
    @abstractmethod
    def getPortfolio(self, file_path: str) -> pd.DataFrame:
        """Lee el portafolio desde un archivo y retorna un DataFrame.

        Args:
            file_path (str): Ruta al archivo de portafolio (CSV/XLS)

        Returns:
            pd.DataFrame: DataFrame con las siguientes columnas:
                - Ticker (str): Símbolo del instrumento
                - Name (str): Nombre descriptivo del instrumento
                - Price (USD) (float): Precio actual en dólares
                - Quantity (float): Cantidad de unidades
                - Price Change (USD) (float): Cambio absoluto del precio en USD
                - Price Change (%) (float): Cambio porcentual del precio
                - Total Value (USD) (float): Valor total de la posición en USD
        """
        pass
    
    def read_file(self, file_path: str) -> pd.DataFrame:
        """Lee un archivo CSV o XLS y retorna un DataFrame"""
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path, decimal=',', thousands='.')
        elif file_path.endswith(('.xls', '.xlsx')):
            try:
                return pd.read_excel(file_path, decimal=',', thousands='.')
            except ValueError as e:
                # El "XLS" de IOL en realidad es un HTML
                # Definimos las columnas que sabemos que tiene el archivo
                # TODO: Podríamos, en realidad, preguntar al usuario de qué broker es el archivo
                # Y, en base a esa información, saber qué columnas esperar
                cols = [
                    'Fecha Transacción',
                    'Fecha Liquidación',
                    'Boleto',
                    'Mercado',
                    'Tipo Transacción',
                    'Numero de Cuenta',
                    'Descripción',
                    'Especie',
                    'Simbolo',
                    'Cantidad',
                    'Moneda',
                    'Precio Ponderado',
                    'Monto',
                    'Comisión y Derecho de Mercado',
                    'Iva Impuesto',
                    'Total'
                ]
                df = pd.read_html(file_path, encoding='utf-8', decimal=',', thousands='.')[0]
                df.columns = cols
                print(df)
                return df
                
        raise ValueError("Formato de archivo no soportado. Use CSV o XLS/XLSX")

    def pesosToUsdCCL(self, pesos: float) -> float:
        """Convierte pesos argentinos a USD CCL"""
        url = 'https://dolarapi.com/v1/dolares/contadoconliqui'
        response = requests.get(url)
        response.raise_for_status()
        dolar = response.json()['compra']
        return pesos / dolar


if __name__ == '__main__':
    raise Exception('No puedes ejecutar este archivo directamente. Impleméntalo')

