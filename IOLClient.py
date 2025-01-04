from typing import Dict, Any
import pandas as pd
import yfinance as yf
from CommonBroker import CommonBroker

class IOLClient(CommonBroker):
    def __init__(self):
        super().__init__()
    
    def _obtener_simbolo(self, row) -> str:
        """Procesa el símbolo para tener un formato consistente"""
        simbolo = str(row['Simbolo']).split()[0]
        print("Simbolo a operar:", simbolo)
        print("Moneda:", row['Moneda'])
        if str(row['Moneda']).upper() == "US$":
            # caso Citigroup "C.D"
            if simbolo.endswith(".D"):
                return simbolo[:-2]
            # Elimina la "D" de los tickers de Cedears en dólares
            # Ej "NVDAD" en dolares -> NVDA en dolares
            # Si no hacemos esto, veremos el portfolio con tickers repetidos, NVDA y NVDAD por ejemplo
            if simbolo.endswith("D"):
                return simbolo[:-1]
        return simbolo


    def _process_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Procesa las transacciones y calcula el portfolio actual"""
        print("Columnas disponibles:", df.columns.tolist())
        
        # Convertir columnas numéricas - sin modificar los separadores decimales
        df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce')
        df['Precio Ponderado'] = pd.to_numeric(df['Precio Ponderado'], errors='coerce')
        
        # Evitar notación científica
        pd.set_option('display.float_format', lambda x: '%.2f' % x)
        
        # Convertir precios a USD si están en ARS
        df['Precio USD'] = df.apply(
            lambda row: self.pesosToUsdCCL(row['Precio Ponderado']) 
            if row['Moneda'].upper() == 'AR$' 
            else row['Precio Ponderado'], 
            axis=1
        )
        
        df['Monto'] = df['Cantidad'] * df['Precio USD']
        
        # Ajustar cantidades según tipo de transacción
        df['Cantidad_Ajustada'] = df.apply(lambda row: 
            -row['Cantidad'] if row['Tipo Transacción'] in ['Venta', 'Rescate FCI']
            else row['Cantidad'], axis=1)
        
        # Procesar símbolos y filtrar cauciones
        df['Simbolo'] = df.apply(self._obtener_simbolo, axis=1)
        df = df[~df['Simbolo'].str.contains('Caución', na=False, case=False)]
        
        # Crear DataFrame solo con compras para calcular precio promedio
        compras_df = df[df['Tipo Transacción'].isin(['Compra', 'Suscripción FCI'])].copy()
        
        # Calcular precio promedio ponderado de compras en USD
        precios_promedio = (compras_df.groupby('Simbolo')
                          .agg({
                              'Monto': 'sum',
                              'Cantidad': 'sum'
                          })
                          .assign(Precio_Promedio=lambda x: x['Monto'] / x['Cantidad'])
                          ['Precio_Promedio'])
        
        # Calcular posiciones actuales
        positions = df.groupby('Simbolo').agg({
            'Descripción': 'first',
            'Cantidad_Ajustada': 'sum',
            'Mercado': 'first'
        }).reset_index()
        
        # Agregar precio promedio de compra a las posiciones
        positions = positions.merge(
            precios_promedio.reset_index(),
            on='Simbolo',
            how='left'
        ).rename(columns={
            'Cantidad_Ajustada': 'Quantity',
            'Precio_Promedio': 'Price (USD)',
            'Descripción': 'Name'
        })
        
        # Filtrar solo posiciones actuales con cantidad distinta de 0
        positions = positions[positions['Quantity'] != 0]
        
        print("\nPosiciones actuales (valores exactos):")
        for _, row in positions.iterrows():
            print(f"{row['Simbolo']}: {row['Quantity']} @ {row['Price (USD)']}")
            
        return positions

    def _calculate_portfolio(self, positions: pd.DataFrame) -> pd.DataFrame:
        """Convierte las posiciones al formato estándar"""
        portfolio = pd.DataFrame(columns=self.PORTFOLIO_COLUMNS)
        
        for _, row in positions.iterrows():
            portfolio = pd.concat([portfolio, pd.DataFrame([{
                'Ticker': row['Simbolo'],
                'Name': row['Name'],
                'Price (USD)': row['Price (USD)'],
                'Quantity': row['Quantity'],
                'Price Change (USD)': 0,
                'Price Change (%)': 0,
                'Total Value (USD)': row['Price (USD)'] * row['Quantity'],
                'Market': row['Mercado']
            }])], ignore_index=True)
        
        return portfolio

    def _obtener_precio_actual(self, ticker: str, market: str) -> tuple:
        """Obtiene el precio actual y previous close de un ticker"""
        try:
            if market.upper() == 'BCBA':
                ticker = f"{ticker}.BA"
            stock = yf.Ticker(ticker)
            current_price = stock.fast_info.get('lastPrice')
            prev_close = stock.fast_info.get('previousClose')
            return float(current_price), float(prev_close)  # type: ignore
        except Exception as e:
            print(f"Error obteniendo precio para {ticker}: {e}")
            return 0.0, 0.0
        

    def _set_price_changes(self, portfolio: pd.DataFrame) -> pd.DataFrame:
        """Setea los cambios de precio (% y USD) en el portfolio"""
        for index, row in portfolio.iterrows():
            # Obtener precio actual según el mercado y convertir a USD si es necesario
            current_price, prev_close = self._obtener_precio_actual(row['Ticker'], row['Market'])
            print(f"Precio actual de {row['Ticker']}: {current_price}")
            
            if current_price > 0:
                # Convertir a USD solo si el precio viene del mercado BCBA
                if row['Market'].upper() == 'BCBA':
                    current_price = self.pesosToUsdCCL(current_price)
                    prev_close = self.pesosToUsdCCL(prev_close)
                
            intraday_change_usd = current_price - prev_close
            intraday_change_pct = (intraday_change_usd / prev_close) * 100 if prev_close > 0 else 0
            
            # Calcular cambio desde la compra original
            original_price = row['Price (USD)']
            print(f"Precio original en USD de {row['Ticker']}: {original_price}")
            
            #price_change_usd = current_price - original_price
            #price_change_pct = (price_change_usd / original_price) * 100 if original_price > 0 else 0
            
            portfolio.at[index, 'Price (USD)'] = current_price
            #portfolio.at[index, 'Price Change (USD)'] = price_change_usd
            #portfolio.at[index, 'Price Change (%)'] = price_change_pct
            portfolio.at[index, 'Price Change (USD)'] = intraday_change_usd
            portfolio.at[index, 'Price Change (%)'] = intraday_change_pct
            portfolio.at[index, 'Total Value (USD)'] = current_price * row['Quantity']
    
        return portfolio.drop('Market', axis=1)

    def getPortfolio(self, file_path: str) -> pd.DataFrame:
        """Lee y procesa un archivo de operaciones de IOL"""
        df = self.read_file(file_path)
        positions = self._process_transactions(df)
        
        # Convertir a formato estándar
        portfolio = self._calculate_portfolio(positions)
        
        return self._set_price_changes(portfolio)











