# Imports de la biblioteca estándar
from typing import Dict, Any

# Imports de terceros
import pandas as pd
import yfinance as yf

# Imports locales
from CommonBroker import CommonBroker

class IOLClient(CommonBroker):
    def __init__(self):
        super().__init__()
    
    def _obtener_simbolo(self, row) -> str:
        """Procesa el símbolo para tener un formato consistente"""
        simbolo = str(row['Simbolo']).split()[0]
        if str(row['Moneda']).upper() == "USD":
            # caso Citigroup "C.D"
            if simbolo.endswith(".D"):
                return simbolo[:-2]
            # Elimina la "D" de los tickers de Cedears en dólares
            # Ej "NVDAD" en dolares -> NVDA en dolares
            if simbolo.endswith("D"):
                return simbolo[:-1]
        return simbolo

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza los nombres de las columnas para el procesamiento"""
        # Los nombres ya vienen correctos del read_file, solo reemplazamos espacios por _
        df.columns = [col.replace(' ', '_') for col in df.columns]
        return df

    def _process_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Procesa las transacciones y calcula el portfolio actual"""
        # Debug: imprimir nombres de columnas
        print("Columnas disponibles:", df.columns.tolist())
        
        # Normalizar nombres de columnas
        df = self._normalize_columns(df)
        print("Columnas normalizadas:", df.columns.tolist())
        
        # Limpiar y preparar datos
        df['Cantidad'] = pd.to_numeric(df['Cantidad'], errors='coerce')
        df['Precio_Ponderado'] = pd.to_numeric(df['Precio_Ponderado'], errors='coerce')
        df['Monto'] = df['Cantidad'] * df['Precio_Ponderado']
        
        # Ajustar cantidades según tipo de transacción
        df['Cantidad_Ajustada'] = df.apply(lambda row: 
            -row['Cantidad'] if row['Tipo Transaccion'] in ['Venta', 'Rescate FCI']
            else row['Cantidad'], axis=1)
        
        # Procesar símbolos
        df['Simbolo'] = df.apply(self._obtener_simbolo, axis=1)
        
        # Crear DataFrame solo con compras para calcular precio promedio
        compras_df = df[df['Tipo_Transaccion'].isin(['Compra', 'Suscripción FCI'])].copy()
        
        # Calcular precio promedio ponderado de compras
        precios_promedio = (compras_df.groupby('Simbolo')
                          .agg({
                              'Monto': 'sum',
                              'Cantidad': 'sum'
                          })
                          .assign(Precio_Promedio=lambda x: x['Monto'] / x['Cantidad'])
                          ['Precio_Promedio'])
        
        # Ajustar cantidades según tipo de transacción para el total
        df['Cantidad_Ajustada'] = df.apply(lambda row: 
            -row['Cantidad'] if row['Tipo Transacción'] in ['Venta', 'Rescate FCI']
            else row['Cantidad'], axis=1)
        
        # Calcular posiciones actuales
        positions = df.groupby('Simbolo').agg({
            'Descripción': 'first',
            'Cantidad_Ajustada': 'sum',
            'Moneda': 'first',
            'Mercado': 'first'
        }).reset_index()
        
        # Agregar precio promedio de compra a las posiciones
        positions = positions.merge(
            precios_promedio.reset_index(),
            on='Simbolo',
            how='left'
        ).rename(columns={
            'Cantidad_Ajustada': 'Cantidad',
            'Precio_Promedio': 'Precio Ponderado'
        })
        
        # Filtrar solo posiciones actuales con cantidad distinta de 0
        positions = positions[positions['Cantidad'] != 0]
        
        return positions

    def _calculate_portfolio(self, positions: pd.DataFrame) -> pd.DataFrame:
        """Convierte las posiciones al formato estándar"""
        portfolio = pd.DataFrame(columns=self.PORTFOLIO_COLUMNS)
        
        for _, row in positions.iterrows():
            price = row['Precio Ponderado']
            if row['Moneda'].lower() == 'peso argentino':
                price = self.pesosToUsdCCL(price)
            
            total_value = price * row['Cantidad']
            
            portfolio = pd.concat([portfolio, pd.DataFrame([{
                'Ticker': row['Simbolo'],
                'Name': row['Descripción'],
                'Price (USD)': price,
                'Quantity': row['Cantidad'],
                'Price Change (USD)': 0,
                'Price Change (%)': 0,
                'Total Value (USD)': total_value,
                'Market': row['Mercado']  # Agregamos el mercado al portfolio
            }])], ignore_index=True)
        
        return portfolio

    def _obtener_precio_actual(self, ticker: str, mercado: str) -> float:
        """
        Obtiene el precio actual de un ticker según el mercado
        """
        try:
            if (mercado.upper() == 'BCBA'):
                # Ajustar ticker para acciones argentinas
                yf_ticker = f"{ticker}.BA"
                stock = yf.Ticker(yf_ticker)
                current_price = stock.info['regularMarketPreviousClose']
                return float(current_price)
            else:
                # Para otros mercados (NYSE, NASDAQ), usar el ticker directo
                stock = yf.Ticker(ticker)
                current_price = stock.info['regularMarketPreviousClose']
                return float(current_price)
        except Exception as e:
            print(f"Error obteniendo precio para {ticker}: {e}")
            return 0.0

    def _set_price_changes(self, portfolio: pd.DataFrame) -> pd.DataFrame:
        """Setea los cambios de precio (% y USD) en el portfolio"""
        for index, row in portfolio.iterrows():
            # Usar el mercado específico de cada activo
            current_price = self._obtener_precio_actual(row['Ticker'], row['Market'])
            if current_price > 0:
                if row['Moneda'].lower() == 'peso argentino':
                    current_price = self.pesosToUsdCCL(current_price)
                
                original_price = row['Price (USD)']
                price_change_usd = current_price - original_price
                price_change_pct = (price_change_usd / original_price) * 100 if original_price > 0 else 0
                
                portfolio.at[index, 'Price (USD)'] = current_price
                portfolio.at[index, 'Price Change (USD)'] = price_change_usd
                portfolio.at[index, 'Price Change (%)'] = price_change_pct
                portfolio.at[index, 'Total Value (USD)'] = current_price * row['Quantity']
        
        return portfolio.drop('Market', axis=1)  # Eliminamos la columna Market al final

    def getPortfolio(self, file_path: str) -> pd.DataFrame:
        """Lee y procesa un archivo de transacciones de IOL"""
        # Leer archivo
        df = self.read_file(file_path)
        
        # Procesar transacciones
        positions = self._process_transactions(df)
        
        # Convertir a formato estándar
        portfolio = self._calculate_portfolio(positions)
        
        # Actualizar precios y cambios
        return self._set_price_changes(portfolio)











