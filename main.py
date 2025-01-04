from IOLClient import IOLClient

def create_client(client_type="IOL"):
    if client_type == "IOL":
        return IOLClient()
    # if client_type == "PPI": Acá se puede ir agregando más...
    # else: Leer archivo CSV si no hay otros proveedores
    raise Exception("Broker no soportado")

def process_portfolio_file(file_path: str, broker_type: str = "IOL"):
    """Procesa un archivo de portfolio"""
    if broker_type == "IOL":
        client = IOLClient()
    else:
        raise ValueError(f"Broker {broker_type} no soportado")
    
    return client.getPortfolio(file_path)

if __name__ == "__main__":
    # Ejemplo de uso. Inserta un archivo testing.xls en el directorio actual
    # TODO: Generar un archivo de pruebas
    file_path = "testing.xls"
    portfolio_df = process_portfolio_file(file_path, "IOL")
    print(portfolio_df)