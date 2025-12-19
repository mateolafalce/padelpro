import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def obtener_tipo_cambio():
    """
    Obtiene el tipo de cambio del dólar oficial desde dolarapi.com.
    Retorna el valor de venta o None si hay un error.
    """
    try:
        print("Consultando tipo de cambio del dólar oficial...")
        response = requests.get("https://dolarapi.com/v1/dolares/oficial")
        response.raise_for_status()
        
        data = response.json()
        tipo_cambio = float(data.get('venta', 0))
        
        if tipo_cambio > 0:
            print(f"Tipo de cambio (venta): ${tipo_cambio:.2f} ARS\n")
            return tipo_cambio
        else:
            print("Error: No se pudo obtener el tipo de cambio")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener tipo de cambio: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado al obtener tipo de cambio: {e}")
        return None

def obtener_facturas_por_cliente():
    """
    Obtiene las facturas de DigitalOcean, suma los montos y los convierte a pesos argentinos.
    Imprime el resultado por pantalla.
    """
    # Obtener las variables de entorno
    api_token = os.getenv('DIGITAL_OCEAN_API_KEY')
    
    # Validar que las variables existan
    if not api_token:
        print("Error: DIGITAL_OCEAN_API_KEY no está configurada en el archivo .env")
        return
    
    # Configurar la petición a la API
    url = "https://api.digitalocean.com/v2/customers/my/invoices"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_token}"
    }
    
    try:
        # Realizar la petición GET
        print("Consultando facturas de DigitalOcean...")
        response = requests.get(url, headers=headers)
        
        # Verificar si la petición fue exitosa
        response.raise_for_status()
        
        # Obtener los datos de la respuesta
        data = response.json()
        
        # La API puede devolver 'invoices' o 'invoice_preview'
        invoices = []
        
        if 'invoices' in data:
            invoices = data['invoices']
        elif 'invoice_preview' in data:
            # Si es invoice_preview, lo convertimos en una lista
            invoices = [data['invoice_preview']]
        else:
            print("Respuesta de la API:")
            print(data)
            print("\nError: No se encontraron facturas en la respuesta")
            return
        
        if not invoices:
            print("No hay facturas disponibles")
            return
        
        # Sumar todos los montos de las facturas
        total_amount = 0
        print(f"\nFacturas encontradas: {len(invoices)}")
        print("-" * 50)
        
        for invoice in invoices:
            amount = float(invoice.get('amount', 0))
            total_amount += amount
            invoice_id = invoice.get('invoice_uuid', 'N/A')
            invoice_period = invoice.get('invoice_period', 'N/A')
            print(f"Factura {invoice_id} (Período: {invoice_period}): ${amount:.2f}")
        
        # Obtener tipo de cambio
        tipo_cambio = obtener_tipo_cambio()
        
        # Imprimir resultados
        print("\n" + "="*50)
        print(f"Monto total de facturas (USD): ${total_amount:.2f}")
        
        if tipo_cambio:
            total_ars = total_amount * tipo_cambio
            print(f"Tipo de cambio (venta): ${tipo_cambio:.2f} ARS")
            print(f"Monto total en pesos (ARS): ${total_ars:.2f}")
        else:
            print("No se pudo calcular el monto en pesos")
        
        print("="*50)
        
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP: {e}")
        print(f"Respuesta del servidor: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error en la petición: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

if __name__ == "__main__":
    obtener_facturas_por_cliente()

