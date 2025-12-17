from flask import Blueprint, request, jsonify
from ai import chat_with_assistant
from bd import db, Cancha, CanchaHorario, Horario
from datetime import datetime, timedelta
from abml_reservas import verificar_disponibilidad, crear_reserva

chat_bp = Blueprint('chat', __name__, url_prefix='/api/chat')

@chat_bp.route('/message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        
        if not data or not data.get('message'):
            return jsonify({'error': 'El mensaje es requerido'}), 400
        
        user_message = data['message']
        conversation_history = data.get('history', [])
        
        # Obtener información de las canchas desde la BD
        canchas = Cancha.query.all()
        canchas_info = []
        
        for cancha in canchas:
            # Obtener los horarios de esta cancha
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
        
        # Obtener respuesta del asistente
        response = chat_with_assistant(
            user_message,
            canchas_info,
            conversation_history,
            verificar_disponibilidad_func=verificar_disponibilidad,
            crear_reserva_func=crear_reserva
        )
        
        return jsonify({
            'response': response,
            'success': True
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500
