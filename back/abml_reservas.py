from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from bd import db, Cancha, Reserva, Cliente, Estado

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

reservas_bp = Blueprint('reservas', __name__, url_prefix='/api/reservas')


def _parse_fecha(fecha: str):
	return datetime.strptime(fecha, '%Y-%m-%d').date()

# Horarios válidos del sistema (rangos)
HORARIOS_VALIDOS = ['08:00-09:00', '10:00-11:00', '12:00-13:00', '14:00-15:00', 
                    '16:00-17:00', '18:00-19:00', '20:00-21:00', '22:00-23:00']

def _normalizar_hora(hora: str):
    # Si es exactamente un rango válido, retornarlo
    if hora in HORARIOS_VALIDOS:
        return hora
    
    # Si es una hora simple "08:00", buscar si coincide con el inicio de algún rango
    for rango in HORARIOS_VALIDOS:
        start = rango.split('-')[0] # "08:00"
        if hora == start:
            return rango
            
    # Si no se encuentra, retornar tal cual para que falle o intentar manejarlo
    return hora

def verificar_disponibilidad(cancha_nombre: str, fecha: str, hora: str):
	try:
		cancha = Cancha.query.filter_by(nombre=cancha_nombre).first()
		if not cancha:
			return {'disponible': False, 'error': f'No se encontró la cancha "{cancha_nombre}"'}

		fecha_obj = _parse_fecha(fecha)
		
		# Normalizar hora (si viene 08:00 -> 08:00-09:00)
		hora_norm = _normalizar_hora(hora)
		
		if hora_norm not in HORARIOS_VALIDOS:
		    return {'disponible': False, 'error': f'Horario "{hora}" no válido. Horarios permitidos: {", ".join(HORARIOS_VALIDOS)}'}

		# Existe reserva activa para esa cancha-fecha-hora (no cancelada)
		reserva_existente = (
			Reserva.query
			.filter_by(cancha_id=cancha.id, fecha=fecha_obj, hora=hora_norm)
			.join(Estado, Reserva.estado_id == Estado.id)
			.filter(Estado.nombre != 'cancelada')
			.first()
		)

		if reserva_existente:
			return {
				'disponible': False,
				'mensaje': f'La cancha {cancha_nombre} no está disponible el {fecha} a las {hora_norm}'
			}

		return {
			'disponible': True,
			'cancha_id': cancha.id,
			'mensaje': f'La cancha {cancha_nombre} está disponible el {fecha} a las {hora_norm}',
			'hora_normalizada': hora_norm
		}
	except Exception as e:
		return {'disponible': False, 'error': str(e)}


def crear_reserva(cancha_nombre: str, fecha: str, hora: str, cliente_nombre: str = None, telefono: str = None):
	try:
		disponibilidad = verificar_disponibilidad(cancha_nombre, fecha, hora)
		if not disponibilidad.get('disponible'):
			return disponibilidad

		cancha_id = disponibilidad['cancha_id']
		# Usar la hora normalizada que nos devolvió verificar_disponibilidad (si existe), o normalizar aqui
		hora_final = disponibilidad.get('hora_normalizada', _normalizar_hora(hora))
		fecha_obj = _parse_fecha(fecha)

		# Obtener la cancha para acceder al precio
		cancha = Cancha.query.get(cancha_id)
		if not cancha:
			return {'exito': False, 'error': 'Cancha no encontrada'}
		
		# Buscar o crear cliente
		cliente = None
		if telefono:
		    logger.info(f"DEBUG crear_reserva: Buscando cliente con telefono={telefono}")
		    cliente = Cliente.query.filter_by(telefono=str(telefono)).first()
		    if cliente:
		        logger.info(f"DEBUG crear_reserva: Cliente encontrado: ID={cliente.id}, nombre={cliente.nombre}, telefono={cliente.telefono}")
		        # FIX: Si el cliente ya existe y tiene el nombre "Cliente WhatsApp" (de pruebas anteriores),
		        # lo actualizamos a la nueva preferencia (solo número).
		        if cliente.nombre == "Cliente WhatsApp":
		            cliente.nombre = str(telefono)
		            cliente.apellido = ""
		            db.session.add(cliente) # Asegurar que se guarde
		            
		    if not cliente:
		        # Crear cliente nuevo con el teléfono
		        # Si no hay nombre, usar el teléfono como nombre para que aparezca "solo el numero"
		        nombre_cliente = cliente_nombre if cliente_nombre else str(telefono)
		        apellido_cliente = "WSP" if cliente_nombre else ""
		        logger.info(f"DEBUG crear_reserva: Creando nuevo cliente con telefono={telefono}, nombre={nombre_cliente}")
		        cliente = Cliente(nombre=nombre_cliente, apellido=apellido_cliente, telefono=str(telefono), categoria=0)
		        db.session.add(cliente)
		        db.session.flush()
		        logger.info(f"DEBUG crear_reserva: Cliente creado con ID={cliente.id}")
		else:
		    # Buscar o crear cliente genérico
		    cliente = Cliente.query.filter_by(nombre='Cliente', apellido='Generico').first()
		    if not cliente:
		        cliente = Cliente(nombre='Cliente', apellido='Generico', telefono="0", categoria=0)
		        db.session.add(cliente)
		        db.session.flush()

		estado = Estado.query.filter_by(nombre='iniciada').first()
		if not estado:
			return {'exito': False, 'error': 'No se encontró el estado "iniciada"'}

		nueva_reserva = Reserva(
			fecha=fecha_obj,
			hora=hora_final, # Guardamos el rango normalizado
			cancha_id=cancha_id,
			cliente_id=cliente.id,
			estado_id=estado.id,
			monto=cancha.precio  # Guardamos el precio actual de la cancha
		)
		db.session.add(nueva_reserva)
		db.session.commit()

		return {
			'exito': True,
			'reserva_id': nueva_reserva.id,
			'mensaje': f'¡Reserva confirmada! Cancha {cancha_nombre} el {fecha} a las {hora_final}. Monto: ${cancha.precio}'
			}
	except Exception as e:
		db.session.rollback()
		return {'exito': False, 'error': str(e)}


def listar_reservas_usuario(telefono: str = None):
	"""Lista las reservas activas (no canceladas) de un usuario"""
	try:
		logger.info(f"DEBUG: listar_reservas_usuario llamado con telefono={telefono}")
		
		if not telefono:
			return {'exito': False, 'error': 'Se requiere el teléfono del usuario'}
		
		# Buscar el cliente por teléfono
		cliente = Cliente.query.filter_by(telefono=str(telefono)).first()
		logger.info(f"DEBUG: Cliente encontrado: {cliente}")
		
		if not cliente:
			logger.info(f"DEBUG: No se encontró cliente con telefono={telefono}")
			return {
				'exito': True,
				'reservas': [],
				'mensaje': 'No se encontraron reservas para este número de teléfono'
			}
		
		logger.info(f"DEBUG: Cliente ID={cliente.id}, nombre={cliente.nombre}, telefono={cliente.telefono}")
		
		# Obtener reservas en estado 'iniciada' del cliente
		reservas = (
			Reserva.query
			.filter_by(cliente_id=cliente.id)
			.join(Estado, Reserva.estado_id == Estado.id)
			.filter(Estado.nombre == 'iniciada')
			.order_by(Reserva.fecha, Reserva.hora)
			.all()
		)
		
		logger.info(f"DEBUG: Reservas encontradas: {len(reservas)}")
		
		if not reservas:
			return {
				'exito': True,
				'reservas': [],
				'mensaje': 'No tenés reservas pendientes'
			}
		
		# Formatear las reservas
		reservas_info = []
		for r in reservas:
			cancha = Cancha.query.get(r.cancha_id)
			estado = Estado.query.get(r.estado_id)
			reservas_info.append({
				'id': r.id,
				'cancha': cancha.nombre if cancha else 'Desconocida',
				'fecha': r.fecha.strftime('%d/%m/%Y'),
				'hora': r.hora,
				'monto': r.monto,
				'estado': estado.nombre if estado else 'Desconocido'
			})
		
		logger.info(f"DEBUG: Reservas formateadas: {reservas_info}")
		
		return {
			'exito': True,
			'reservas': reservas_info,
			'mensaje': f'Encontramos {len(reservas_info)} reserva(s) pendiente(s)'
		}
	except Exception as e:
		logger.error(f"DEBUG ERROR: {str(e)}")
		return {'exito': False, 'error': str(e)}


def cancelar_reserva_usuario(reserva_id: int, telefono: str = None):
	"""Cancela una reserva cambiando su estado de 'iniciada' a 'cancelada'"""
	try:
		logger.info(f"DEBUG: cancelar_reserva_usuario llamado con reserva_id={reserva_id}, telefono={telefono}")
		# Buscar la reserva
		reserva = Reserva.query.get(reserva_id)
		logger.info(f"DEBUG: Reserva encontrada: {reserva}")
		if not reserva:
			logger.info(f"DEBUG: No se encontró reserva con ID={reserva_id}")
			return {'exito': False, 'error': f'No se encontró la reserva con ID {reserva_id}'}
		
		# Verificar que la reserva pertenece al usuario (si se proporciona teléfono)
		if telefono:
			cliente = Cliente.query.get(reserva.cliente_id)
			logger.info(f"DEBUG: Verificando propiedad - Cliente de la reserva: {cliente.telefono if cliente else 'None'}, Usuario actual: {telefono}")
			if not cliente or cliente.telefono != str(telefono):
				logger.info(f"DEBUG: La reserva no pertenece al usuario")
				return {'exito': False, 'error': 'Esta reserva no te pertenece'}
		
		# Verificar que la reserva no esté ya cancelada
		estado_actual = Estado.query.get(reserva.estado_id)
		if estado_actual and estado_actual.nombre == 'cancelada':
			return {'exito': False, 'error': 'Esta reserva ya está cancelada'}
		
		# Cambiar el estado a cancelada
		estado_cancelada = Estado.query.filter_by(nombre='cancelada').first()
		if not estado_cancelada:
			return {'exito': False, 'error': 'No se encontró el estado "cancelada" en el sistema'}
		
		reserva.estado_id = estado_cancelada.id
		db.session.commit()
		logger.info(f"DEBUG: Reserva {reserva_id} cancelada exitosamente")
		
		# Obtener información de la reserva para el mensaje
		cancha = Cancha.query.get(reserva.cancha_id)
		fecha_formateada = reserva.fecha.strftime('%d/%m/%Y')
		
		return {
			'exito': True,
			'mensaje': f'Reserva cancelada exitosamente. Cancha {cancha.nombre if cancha else "Desconocida"} del {fecha_formateada} a las {reserva.hora}'
		}
	except Exception as e:
		db.session.rollback()
		return {'exito': False, 'error': str(e)}



@reservas_bp.route('/', methods=['GET'])
def listar_reservas():
	try:
		reservas = Reserva.query.order_by(Reserva.fecha, Reserva.hora).all()
		data = []
		for r in reservas:
			estado = Estado.query.get(r.estado_id)
			cancha = Cancha.query.get(r.cancha_id)
			cliente = Cliente.query.get(r.cliente_id)
			data.append({
				'id': r.id,
				'fecha': r.fecha.strftime('%Y-%m-%d'),
				'hora': r.hora, # Es string
				'cancha': cancha.nombre if cancha else None,
				'cliente': f"{cliente.nombre} {cliente.apellido}".strip() if cliente else None,
				'estado': estado.nombre if estado else None,
				'monto': r.monto
			})
		return jsonify({'success': True, 'reservas': data}), 200
	except Exception as e:
		return jsonify({'success': False, 'error': str(e)}), 500


@reservas_bp.route('/<int:reserva_id>', methods=['GET'])
def obtener_reserva(reserva_id: int):
	try:
		r = Reserva.query.get(reserva_id)
		if not r:
			return jsonify({'success': False, 'error': 'Reserva no encontrada'}), 404
		estado = Estado.query.get(r.estado_id)
		cancha = Cancha.query.get(r.cancha_id)
		cliente = Cliente.query.get(r.cliente_id)
		data = {
			'id': r.id,
			'fecha': r.fecha.strftime('%Y-%m-%d'),
			'hora': r.hora, # Es string
			'cancha': cancha.nombre if cancha else None,
			'cliente': f"{cliente.nombre} {cliente.apellido}".strip() if cliente else None,
			'estado': estado.nombre if estado else None,
			'monto': r.monto
		}
		return jsonify({'success': True, 'reserva': data}), 200
	except Exception as e:
		return jsonify({'success': False, 'error': str(e)}), 500


@reservas_bp.route('/', methods=['POST'])
def crear_reserva_endpoint():
	try:
		data = request.get_json() or {}
		cancha_nombre = data.get('cancha_nombre')
		fecha = data.get('fecha')
		hora = data.get('hora')
		cliente_nombre = data.get('cliente_nombre')  # opcional

		if not cancha_nombre or not fecha or not hora:
			return jsonify({'success': False, 'error': 'Faltan datos: cancha_nombre, fecha, hora'}), 400

		resultado = crear_reserva(cancha_nombre, fecha, hora, cliente_nombre)
		status = 200 if resultado.get('exito') else 400
		return jsonify(resultado), status
	except Exception as e:
		return jsonify({'success': False, 'error': str(e)}), 500


@reservas_bp.route('/<int:reserva_id>', methods=['PUT'])
def actualizar_reserva(reserva_id: int):
	try:
		r = Reserva.query.get(reserva_id)
		if not r:
			return jsonify({'success': False, 'error': 'Reserva no encontrada'}), 404

		data = request.get_json() or {}
		nueva_fecha = data.get('fecha')
		nueva_hora = data.get('hora')
		nueva_cancha_nombre = data.get('cancha_nombre')

		if nueva_fecha and nueva_hora and nueva_cancha_nombre:
			disp = verificar_disponibilidad(nueva_cancha_nombre, nueva_fecha, nueva_hora)
			if not disp.get('disponible'):
				return jsonify(disp), 400
			r.fecha = _parse_fecha(nueva_fecha)
			r.hora = nueva_hora
			cancha = Cancha.query.filter_by(nombre=nueva_cancha_nombre).first()
			if not cancha:
				return jsonify({'success': False, 'error': 'Cancha no encontrada'}), 404
			r.cancha_id = cancha.id
		else:
			if nueva_fecha:
				r.fecha = datetime.strptime(nueva_fecha, '%Y-%m-%d').date()
			if nueva_hora:
				r.hora = nueva_hora # Directamente string
			if nueva_cancha_nombre:
				cancha = Cancha.query.filter_by(nombre=nueva_cancha_nombre).first()
				if not cancha:
					return jsonify({'success': False, 'error': 'Cancha no encontrada'}), 404
				r.cancha_id = cancha.id

		db.session.commit()
		return jsonify({'success': True, 'mensaje': 'Reserva actualizada'}), 200
	except Exception as e:
		db.session.rollback()
		return jsonify({'success': False, 'error': str(e)}), 500


@reservas_bp.route('/<int:reserva_id>', methods=['DELETE'])
def eliminar_reserva(reserva_id: int):
	try:
		r = Reserva.query.get(reserva_id)
		if not r:
			return jsonify({'success': False, 'error': 'Reserva no encontrada'}), 404
		db.session.delete(r)
		db.session.commit()
		return jsonify({'success': True, 'mensaje': 'Reserva eliminada'}), 200
	except Exception as e:
		db.session.rollback()
		return jsonify({'success': False, 'error': str(e)}), 500


@reservas_bp.route('/<int:reserva_id>/cancelar', methods=['POST'])
def cancelar_reserva(reserva_id: int):
	try:
		r = Reserva.query.get(reserva_id)
		if not r:
			return jsonify({'success': False, 'error': 'Reserva no encontrada'}), 404
		estado_cancelada = Estado.query.filter_by(nombre='cancelada').first()
		if not estado_cancelada:
			return jsonify({'success': False, 'error': 'Estado "cancelada" no encontrado'}), 400
		r.estado_id = estado_cancelada.id
		db.session.commit()
		return jsonify({'success': True, 'mensaje': 'Reserva cancelada'}), 200
	except Exception as e:
		db.session.rollback()
		return jsonify({'success': False, 'error': str(e)}), 500


@reservas_bp.route('/disponibilidad', methods=['POST'])
def disponibilidad_endpoint():
	try:
		data = request.get_json() or {}
		cancha_nombre = data.get('cancha_nombre')
		fecha = data.get('fecha')
		hora = data.get('hora')
		if not cancha_nombre or not fecha or not hora:
			return jsonify({'success': False, 'error': 'Faltan datos: cancha_nombre, fecha, hora'}), 400
		resultado = verificar_disponibilidad(cancha_nombre, fecha, hora)
		status = 200 if resultado.get('disponible') else 200
		resultado['success'] = True
		return jsonify(resultado), status
	except Exception as e:
		return jsonify({'success': False, 'error': str(e)}), 500

