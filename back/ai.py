import os
import json
import re
from datetime import datetime

from dotenv import load_dotenv
import dateparser
from openai import OpenAI


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

business_kind = os.getenv("BUSINESS_KIND", "PadelPro")
business_name = os.getenv("BUSINESS_NAME", "Complejo de Padel")
business_address = os.getenv("BUSINESS_ADDRESS", "69 entre 119 y 120")
cbu = os.getenv("CBU", "")
alias = os.getenv("ALIAS", "")

# Horarios válidos del sistema (rangos)
HORARIOS_VALIDOS = ['08:00-09:00', '10:00-11:00', '12:00-13:00', '14:00-15:00', 
                    '16:00-17:00', '18:00-19:00', '20:00-21:00', '22:00-23:00']

if not api_key:
    raise RuntimeError("Missing required environment variable: OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


def send_prompt(prompt: str, system_message: str) -> str:
    messages = []
    
    if system_message:
        messages.append({"role": "system", "content": system_message})
    
    messages.append({"role": "user", "content": prompt})
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.8,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as exc:
        raise Exception(f"OpenAI API call failed: {exc}") from exc


def send_prompt_with_history(
    messages: list[dict[str, str]], temperature: float = 0.7
) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as exc:
        raise Exception(f"OpenAI API call failed: {exc}") from exc


def build_system_prompt(canchas: list[dict]) -> str:
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    dia_actual = datetime.now().strftime('%A %d de %B de %Y')
    
    system_prompt = f"""Eres un agente de atención al cliente para {business_name}, un {business_kind} ubicado en {business_address}.

FECHA ACTUAL: {dia_actual} ({fecha_actual})

INSTRUCCIONES IMPORTANTES:
- Siempre responde en español argentino.
- Utiliza un tono amigable y profesional.
- Ayuda a los clientes con información sobre canchas, horarios y reservas.
- Si el cliente expresa fecha y hora en lenguaje natural (ej: "martes de la semana que viene a las 13"), inferí y convertí automáticamente a formato YYYY-MM-DD y HH:MM usando la fecha actual como referencia. Evitá pedirle el formato si la información ya está presente.
- Si te piden reservar, PRIMERO verifica la disponibilidad usando la función verificar_disponibilidad.
- Si la cancha está disponible, NO reserves automáticamente. En su lugar, PRESENTA un resumen claro de los datos de la reserva (Cancha, Fecha, Hora, Precio) y PREGUNTA al usuario si desea confirmar la reserva.
- Cuando hables de una cancha, menciona su precio también.
- SOLO cuando el usuario confirme explícitamente (diga "sí", "confirmar", "dale", etc.), llama a la función crear_reserva.
- Solo después de que crear_reserva retorne éxito, confirmá al cliente que la reserva fue completada. ADEMÁS, debes enviar un mensaje con el detalle del pago: Menciona el monto a pagar, el CBU ({cbu}) y el Alias ({alias}) para realizar la transferencia.
- Sé proactivo en ayudar a encontrar alternativas si no hay disponibilidad.
- Los horarios de reserva son ESTRICTOS y ÚNICOS. Debes usar EXACTAMENTE uno de los siguientes rangos para el parámetro 'hora' en las funciones: {", ".join(HORARIOS_VALIDOS)}. No inventes otros horarios ni uses formato HH:MM simple si puedes evitarlo.

"""
    
    # Agregar información de las canchas
    if canchas:
        system_prompt += "CANCHAS DISPONIBLES:\n\n"
        for cancha in canchas:
            system_prompt += f"📍 {cancha['nombre']}\n"
            if cancha.get('descripcion'):
                system_prompt += f"   Descripción: {cancha['descripcion']}\n"
            system_prompt += f"   Capacidad máxima: {cancha['cantidad']} personas\n"
            if cancha.get('precio'):
                system_prompt += f"   Precio: ${cancha['precio']}\n"
            
            if cancha.get('horarios'):
                system_prompt += "   Horarios disponibles:\n"
                # Agrupar horarios por día
                horarios_por_dia = {}
                for h in cancha['horarios']:
                    dia = h['dia']
                    hora = h['hora']
                    if dia not in horarios_por_dia:
                        horarios_por_dia[dia] = []
                    horarios_por_dia[dia].append(hora)
                
                for dia, horas in horarios_por_dia.items():
                    horas_str = ', '.join(sorted(horas))
                    system_prompt += f"      {dia}: {horas_str}\n"
            else:
                system_prompt += "   Horarios: No definidos aún\n"
            system_prompt += "\n"
    else:
        system_prompt += "NOTA: Actualmente no hay canchas registradas en el sistema.\n"
    
    return system_prompt


def get_function_definitions():
    """Define las funciones que el asistente puede llamar"""
    return [
        {
            "name": "verificar_disponibilidad",
            "description": "Verifica si una cancha está disponible en una fecha y hora específica",
            "parameters": {
                "type": "object",
                "properties": {
                    "cancha_nombre": {
                        "type": "string",
                        "description": "El nombre exacto de la cancha (ej: 'Cancha A')"
                    },
                    "fecha": {
                        "type": "string",
                        "description": "La fecha en formato YYYY-MM-DD (ej: '2025-12-20')"
                    },
                    "hora": {
                        "type": "string",
                        "description": "La hora en formato HH:MM (ej: '18:00')"
                    }
                },
                "required": ["cancha_nombre", "fecha", "hora"]
            }
        },
        {
            "name": "crear_reserva",
            "description": "Crea una reserva para una cancha en una fecha y hora específica. Solo llamar después de verificar disponibilidad y confirmar con el cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cancha_nombre": {
                        "type": "string",
                        "description": "El nombre exacto de la cancha"
                    },
                    "fecha": {
                        "type": "string",
                        "description": "La fecha en formato YYYY-MM-DD"
                    },
                    "hora": {
                        "type": "string",
                        "description": "La hora en formato HH:MM"
                    },
                    "cliente_nombre": {
                        "type": "string",
                        "description": "Nombre del cliente (opcional)"
                    }
                },
                "required": ["cancha_nombre", "fecha", "hora"]
            }
        }
    ]


def chat_with_assistant(
    user_message: str, 
    canchas: list[dict], 
    conversation_history: list[dict] = None,
    verificar_disponibilidad_func = None,
    crear_reserva_func = None
) -> str:
    system_prompt = build_system_prompt(canchas)
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": user_message})
    
    tools = [{"type": "function", "function": func} for func in get_function_definitions()]
    
    # Loop para manejar múltiples llamadas a herramientas consecutivas (ej: verificar -> reservar)
    max_turns = 5
    turn_count = 0
    
    while turn_count < max_turns:
        turn_count += 1
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                tools=tools,
                tool_choice="auto"
            )
            
            response_message = response.choices[0].message
            
            # Si no hay llamadas a herramientas, devolvemos la respuesta final
            if not response_message.tool_calls:
                return response_message.content.strip()
            
            # Agregar la respuesta del asistente (con tool_calls) al historial
            messages.append(response_message)
            
            # Ejecutar cada función llamada
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Normalizar fecha/hora si están en lenguaje natural
                def _normalize_args(args: dict):
                    out = dict(args)
                    # Normalizar fecha
                    fecha = out.get("fecha")
                    if fecha and not re.match(r"^\d{4}-\d{2}-\d{2}$", str(fecha)):
                        print(f"DEBUG: Normalizando fecha '{fecha}'")
                        dt = dateparser.parse(str(fecha), languages=["es"], settings={
                            "RELATIVE_BASE": datetime.now(),
                            "PREFER_DATES_FROM": "future",
                        })
                        if dt:
                            out["fecha"] = dt.strftime("%Y-%m-%d")
                            print(f"DEBUG: Fecha normalizada a '{out['fecha']}'")
                    
                    # Normalizar hora (ahora soportamos rangos en strings, intentamos conservarlos)
                    # Si viene algo como "8" o "8pm", dateparser ayuda, pero si ya es rango "08:00-09:00" lo dejamos
                    hora = out.get("hora")
                    if hora:
                        # Si parece un rango 'HH:MM-HH:MM', lo dejamos pasar
                        if re.match(r"^\d{2}:\d{2}-\d{2}:\d{2}$", str(hora)):
                            pass
                        elif not re.match(r"^\d{2}:\d{2}$", str(hora)):
                            print(f"DEBUG: Normalizando hora '{hora}'")
                            dt_h = dateparser.parse(str(hora), languages=["es"], settings={
                                "RELATIVE_BASE": datetime.now(),
                            })
                            if dt_h:
                                # OJO: Aquí simplificamos a HH:MM si el LLM mandó "8 pm".
                                # Pero nuestro backend espera rangos "HH:MM-HH:MM".
                                # Si el LLM no mandó rango, el backend fallará o necesitará adaptación.
                                # Por ahora asumimos que el prompt instruye al LLM a usar los rangos disponibles.
                                out["hora"] = dt_h.strftime("%H:%M")
                                print(f"DEBUG: Hora normalizada a '{out['hora']}'")
                                
                    return out
                
                function_args = _normalize_args(function_args)
                print(f"DEBUG: Ejecutando herramienta {function_name} con args: {function_args}")
                
                # Llamar a la función correspondiente
                if function_name == "verificar_disponibilidad" and verificar_disponibilidad_func:
                    function_response = verificar_disponibilidad_func(**function_args)
                elif function_name == "crear_reserva" and crear_reserva_func:
                    function_response = crear_reserva_func(**function_args)
                else:
                    function_response = {"error": "Función no disponible"}
                
                # Agregar la respuesta de la función a los mensajes
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(function_response, ensure_ascii=False)
                })
                
        except Exception as e:
            print(f"Error en chat loop: {e}")
            return "Lo siento, hubo un error al procesar tu solicitud."

    return "Lo siento, la operación está tomando demasiados pasos."