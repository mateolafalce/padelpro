from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from bd import db, Cancha, Horario, Reserva, Estado, Cliente

cancelar_bp = Blueprint('cancelar', __name__, url_prefix='/api/cancelar')

@cancelar_bp.route('/horarios_fecha', methods=['GET'])
def obtener_horarios_fecha():
    try:
        fecha_str = request.args.get('fecha')
        if not fecha_str:
            return jsonify({'success': False, 'error': 'Fecha requerida'}), 400
            
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # Mapear fecha a día de la semana (0=Lunes, 6=Domingo)
        dias_semana = {
            0: 'Lunes',
            1: 'Martes',
            2: 'Miércoles',
            3: 'Jueves',
            4: 'Viernes',
            5: 'Sábado',
            6: 'Domingo'
        }
        dia_nombre = dias_semana[fecha_obj.weekday()]
        
        # Obtener todas las canchas
        canchas = Cancha.query.all()
        
        # Obtener horarios filtrados por el día de la semana para evitar duplicados del grid semanal
        horarios = Horario.query.filter_by(dia=dia_nombre).order_by(Horario.hora).all()
        
        # Obtener reservas existentes para esa fecha
        reservas = Reserva.query.filter_by(fecha=fecha_obj).all()
        
        # Mapear reservas por cancha_id y hora
        reservas_map = {}
        for r in reservas:
            key = (r.cancha_id, r.hora)
            estado = Estado.query.get(r.estado_id)
            reservas_map[key] = estado.nombre
            
        # Construir respuesta
        grid = []
        for h in horarios:
            # La hora ya es un rango string "08:00-09:00"
            time_str = h.hora
            
            fila = {'hora': time_str, 'canchas': []}
            for c in canchas:
                estado_actual = reservas_map.get((c.id, h.hora), 'disponible')
                
                # Si está cancelada, cuenta como disponible
                if estado_actual == 'cancelada':
                    estado_actual = 'disponible'
                    
                fila['canchas'].append({
                    'cancha_id': c.id,
                    'cancha_nombre': c.nombre,
                    'estado': estado_actual
                })
            grid.append(fila)
            
        return jsonify({'success': True, 'horarios': grid}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@cancelar_bp.route('/toggle', methods=['POST'])
def toggle_bloqueo():
    try:
        data = request.get_json()
        cancha_id = data.get('cancha_id')
        fecha_str = data.get('fecha')
        hora_str = data.get('hora')
        
        if not all([cancha_id, fecha_str, hora_str]):
            return jsonify({'success': False, 'error': 'Faltan datos'}), 400
            
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # El frontend debe enviar el rango completo ej "08:00-09:00"
        # Si envía solo la hora de inicio, podríamos normalizarlo, pero asumiremos que el frontend
        # envía lo que recibió en GET /horarios_fecha.
        
        # Buscar reserva existente
        reserva = Reserva.query.filter_by(
            cancha_id=cancha_id, 
            fecha=fecha_obj, 
            hora=hora_str # Usamos el string directo
        ).join(Estado).filter(Estado.nombre != 'cancelada').first()
        
        estado_bloqueada = Estado.query.filter_by(nombre='bloqueada').first()
        if not estado_bloqueada:
            return jsonify({'success': False, 'error': 'Estado bloqueada no existe'}), 500
            
        if reserva:
            # Si existe y está bloqueada, la desbloqueamos (ponemos en cancelada o la borramos)
            # Mejor la borramos para limpiar, o la ponemos en 'cancelada'.
            # Para mantener historial, 'cancelada' es mejor, pero si es un bloqueo administrativo, tal vez borrar es mas limpio.
            # Usemos 'cancelada' para ser consistentes con el sistema.
            if reserva.estado.nombre == 'bloqueada':
                estado_cancelada = Estado.query.filter_by(nombre='cancelada').first()
                reserva.estado_id = estado_cancelada.id
                accion = 'desbloqueada'
            else:
                return jsonify({'success': False, 'error': 'El horario ya está ocupado por una reserva real'}), 400
        else:
            # Crear bloqueo
            # Necesitamos un cliente dummy o null?
            # El modelo Reserva requiere cliente_id.
            # Busquemos 'Admin' o usemos el generico.
            cliente = Cliente.query.filter_by(nombre='Admin').first()
            if not cliente:
                 cliente = Cliente.query.filter_by(nombre='Cliente', apellido='Generico').first()
                 
            if not cliente:
                 # Crear si no existe nada
                 cliente = Cliente(nombre='Cliente', apellido='Generico', telefono=0, categoria=0)
                 db.session.add(cliente)
                 db.session.flush()
            
            nueva_reserva = Reserva(
                fecha=fecha_obj,
                hora=hora_str, # String directo
                cancha_id=cancha_id,
                cliente_id=cliente.id,
                estado_id=estado_bloqueada.id
            )
            db.session.add(nueva_reserva)
            accion = 'bloqueada'
            
        db.session.commit()
        return jsonify({'success': True, 'accion': accion}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
