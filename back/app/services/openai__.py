import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()   

API_KEY = os.getenv("OPENAI_ADMIN_KEY")
PROYECTO = os.getenv("OPENAI_PROJECT_NAME")
url = "https://api.openai.com/v1/organization/costs"

end_date = datetime.now()
start_date = end_date - timedelta(days=30)

params = {
    "start_time": int(start_date.timestamp()),
    "end_time": int(end_date.timestamp()),
    "group_by": "project_id",
    "limit": 100
}

headers = {"Authorization": f"Bearer {API_KEY}"}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    
    # Variable para acumular el total del proyecto específico
    total_proyecto = 0.0

    # 1. Recorremos los 'buckets' (los días)
    for bucket in data.get('data', []):
        # 2. Recorremos los resultados dentro de cada día
        for result in bucket.get('results', []):
            
            project_name = result.get('project_name', 'Desconocido')
            
            # Solo sumamos si el nombre del proyecto coincide con PROYECTO
            if project_name == PROYECTO:
                # A veces el valor viene como string, aseguramos que sea float
                amount_value = float(result['amount']['value'])
                total_proyecto += amount_value

    # Imprimir solo el resultado final
    print("=" * 50)
    print(f"Proyecto: {PROYECTO}")
    print(f"Gasto total (últimos 30 días): ${total_proyecto:.6f} USD")
    print("=" * 50)

else:
    print(f"Error {response.status_code}: {response.text}")