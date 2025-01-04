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
        """Lee el portafolio desde un archivo y retorna un DataFrame normalizado.

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
            return pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx')):
            try:
                return pd.read_excel(file_path)
            except ValueError as e:
                # El "XLS" de IOL en realidad es un HTML/XML
                # Definimos las columnas que sabemos que tiene el archivo
                cols = [
                    'Fecha Transaccion',
                    'Fecha Liquidacion',
                    'Boleto',
                    'Mercado',
                    'Tipo Transaccion',
                    'Numero Cuenta',
                    'Descripcion',
                    'Especie',
                    'Simbolo',
                    'Cantidad',
                    'Moneda',
                    'Precio Ponderado',
                    'Monto',
                    'Comision',
                    'Iva',
                    'Total'
                ]
                # Leemos la tabla y asignamos los nombres de columnas
                df = pd.read_html(file_path, encoding='utf-8')[1]  # La tabla que queremos es la segunda (índice 1)
                df.columns = cols
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

