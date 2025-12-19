from flask import Blueprint, request, jsonify
import os
import requests
import json
from ai import chat_with_assistant
from bd import db, Cancha, CanchaHorario, Horario
from abml_reservas import verificar_disponibilidad, crear_reserva, listar_reservas_usuario, cancelar_reserva_usuario
from historial_utils import guardar_mensaje, obtener_historial, limpiar_historial_antiguo

wsp_bp = Blueprint('whatsapp', __name__, url_prefix='/api/whatsapp')

# Configuración de WhatsApp Business API
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN', 'padelpro_verify_token_2024')

def get_canchas_info():
    """Obtener información de las canchas desde la BD"""
    canchas = Cancha.query.all()
    canchas_info = []
    
    for cancha in canchas:
        horarios_cancha = []
        for ch in CanchaHorario.query.filter_by(cancha_id=cancha.id).all():
            horario = Horario.query.get(ch.horario_id)
            if horario:
                horarios_cancha.append({
                    'dia': horario.dia,
                    'hora': horario.hora
                })
        
        canchas_info.append({
            'nombre': cancha.nombre,
            'descripcion': cancha.descripcion or '',
            'cantidad': cancha.cantidad,
            'precio': cancha.precio,
            'horarios': horarios_cancha
        })
    
    return canchas_info

def send_whatsapp_message(phone_number, message):
    """Enviar mensaje de WhatsApp usando la API de Meta"""
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        print("Error: WhatsApp credentials not configured")
        return False
    
    url = f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": message
        }
    }
    
    try:
        print(f"DEBUG: Sending WhatsApp message to {phone_number} with content: {message}")
        response = requests.post(url, headers=headers, json=data)
        
        if not response.ok:
            error_data = response.json()
            error_code = error_data.get('error', {}).get('code')
            print(f"Error sending WhatsApp message: {response.status_code} - {response.text}")
            
            # Reintento automático para números de Argentina (problema común del prefijo 9)
            # Código 131030 es "Recipient phone number not in allowed list"
            # A veces la lista de permitidos no tiene el 9, pero el webhook sí lo trae.
            if error_code == 131030 and phone_number.startswith('549'):
                alternate_phone = '54' + phone_number[3:]
                print(f"DEBUG: Reintentando con número alternativo: {alternate_phone}")
                data['to'] = alternate_phone
                response = requests.post(url, headers=headers, json=data)
                if not response.ok:
                    print(f"Error en reintento: {response.status_code} - {response.text}")
                else:
                    return True

        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Exception sending WhatsApp message: {e}")
        return False

@wsp_bp.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verificación del webhook de WhatsApp"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        print("Webhook verified successfully!")
        return challenge, 200
    else:
        print("Webhook verification failed")
        return 'Forbidden', 403

@wsp_bp.route('/webhook', methods=['POST'])
def webhook():
    """Recibir mensajes de WhatsApp"""
    try:
        data = request.get_json()
        
        # Verificar que sea un mensaje válido
        if not data.get('entry'):
            return jsonify({'status': 'ok'}), 200
        
        for entry in data['entry']:
            for change in entry.get('changes', []):
                value = change.get('value', {})
                
                # Verificar que haya mensajes
                if not value.get('messages'):
                    continue
                
                for message in value['messages']:
                    # Obtener datos del mensaje
                    from_number = message['from']
                    message_type = message['type']
                    
                    print(f"DEBUG WSP: Mensaje recibido de número: {from_number}")
                    
                    # Solo procesar mensajes de texto
                    if message_type != 'text':
                        send_whatsapp_message(
                            from_number, 
                            "Lo siento, solo puedo procesar mensajes de texto por ahora."
                        )
                        continue
                    
                    user_message = message['text']['body']
                    message_id = message['id']
                    
                    # Guardar el mensaje del usuario en la BD
                    guardar_mensaje(from_number, 'user', user_message)
                    
                    # Obtener historial de conversación desde la BD (últimos 10 mensajes)
                    conversation_history = obtener_historial(from_number, limite=10)
                    
                    # Obtener información de canchas
                    canchas_info = get_canchas_info()
                    
                    # Wrapper para inyectar el teléfono en crear_reserva
                    def crear_reserva_wrapper(**kwargs):
                         print(f"DEBUG WSP: crear_reserva_wrapper llamado con telefono={from_number}")
                         kwargs['telefono'] = from_number
                         return crear_reserva(**kwargs)

                    # Obtener respuesta del asistente
                    print(f"DEBUG WSP: Llamando chat_with_assistant con usuario={from_number}")
                    response = chat_with_assistant(
                        user_message,
                        canchas_info,
                        conversation_history,
                        verificar_disponibilidad_func=verificar_disponibilidad,
                        crear_reserva_func=crear_reserva_wrapper,
                        listar_reservas_func=listar_reservas_usuario,
                        cancelar_reserva_func=cancelar_reserva_usuario,
                        usuario=from_number
                    )
                    
                    # Guardar la respuesta del asistente en la BD
                    guardar_mensaje(from_number, 'assistant', response)
                    
                    # Limpiar historial antiguo (mantener solo últimos 50 mensajes)
                    limpiar_historial_antiguo(from_number, mantener_ultimos=50)
                    
                    # Enviar respuesta
                    send_whatsapp_message(from_number, response)
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@wsp_bp.route('/send', methods=['POST'])
def send_message():
    """Endpoint manual para enviar mensajes (útil para testing)"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        message = data.get('message')
        
        if not phone_number or not message:
            return jsonify({'error': 'phone_number and message are required'}), 400
        
        success = send_whatsapp_message(phone_number, message)
        
        if success:
            return jsonify({'status': 'sent', 'success': True}), 200
        else:
            return jsonify({'status': 'failed', 'success': False}), 500
            
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@wsp_bp.route('/clear-history/<phone_number>', methods=['DELETE'])
def clear_history(phone_number):
    """Limpiar historial de conversación de un número"""
    try:
        from bd import Conversacion
        # Eliminar todos los mensajes de este usuario
        Conversacion.query.filter_by(usuario=phone_number).delete()
        db.session.commit()
        return jsonify({'status': 'cleared', 'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e), 'success': False}), 500
