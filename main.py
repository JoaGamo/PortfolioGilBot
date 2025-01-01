import os
from IOLClient import IOLClient


def create_client(client_type="IOL"):
    if client_type == "IOL":
        return IOLClient(
            usuario=os.getenv("IOL_USUARIO"),
            contrasena=os.getenv("IOL_CONTRASENA"),
            CUENTA_USA=os.getenv("IOL_CUENTA_EN_USA")
        )
    # if client_type == "PPI": Acá se puede ir agregando más...
    # else: Leer archivo CSV si no hay otros proveedores
    raise Exception("Broker no soportado")

def main():
    client = create_client()
    print(client.getPortfolio())
    # Esto se prepara para skfolio
    return client.getPortfolio()