from flask import Blueprint, request, jsonify
from bd import db, Cancha, Horario, CanchaHorario, Reserva
from datetime import datetime, timedelta

canchas_bp = Blueprint('canchas', __name__, url_prefix='/canchas')

# GET - Listar todos los horarios disponibles
@canchas_bp.route('/horarios', methods=['GET'])
def listar_horarios():
    try:
        # Se ordena alfbeticamente al ser string, pero para "08:XX", "10:XX" funciona bien
        # Si queremos orden perfecto, habría que ver. Por ahora confiamos en el formato HH:MM
        horarios = Horario.query.order_by(Horario.dia, Horario.hora).all()
        resultado = []
        for horario in horarios:
            resultado.append({
                'id': horario.id,
                'dia': horario.dia,
                'hora': horario.hora # Ya es el string "08:00-09:00"
            })
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GET - Listar todas las canchas
@canchas_bp.route('/', methods=['GET'])
def listar_canchas():
    try:
        canchas = Cancha.query.all()
        resultado = []
        for cancha in canchas:
            # Obtener los horarios de esta cancha
            horarios_cancha = []
            for ch in CanchaHorario.query.filter_by(cancha_id=cancha.id).all():
                horario = Horario.query.get(ch.horario_id)
                if horario:
                    horarios_cancha.append({
                        'id': horario.id,
                        'dia': horario.dia,
                        'hora': horario.hora
                    })
            
            resultado.append({
                'id': cancha.id,
                'nombre': cancha.nombre,
                'cantidad': cancha.cantidad,
                'descripcion': cancha.descripcion,
                'precio': cancha.precio,
                'horarios': horarios_cancha
            })
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# POST - Crear una nueva cancha
@canchas_bp.route('/', methods=['POST'])
def crear_cancha():
    try:
        data = request.get_json()
        
        # Validar que los campos requeridos existan
        if not data or not data.get('nombre') or not data.get('cantidad'):
            return jsonify({'error': 'Faltan campos requeridos: nombre, cantidad'}), 400
        
        nueva_cancha = Cancha(
            nombre=data['nombre'],
            cantidad=data['cantidad'],
            descripcion=data.get('descripcion', ''),
            precio=data.get('precio', 0.0)
        )
        
        db.session.add(nueva_cancha)
        db.session.flush()  # Para obtener el ID de la nueva cancha
        
        # Agregar horarios si se proporcionaron
        horarios_ids = data.get('horarios', [])
        if horarios_ids:
            for horario_id in horarios_ids:
                cancha_horario = CanchaHorario(
                    cancha_id=nueva_cancha.id,
                    horario_id=horario_id
                )
                db.session.add(cancha_horario)
        
        db.session.commit()
        
        return jsonify({
            'id': nueva_cancha.id,
            'nombre': nueva_cancha.nombre,
            'cantidad': nueva_cancha.cantidad,
            'descripcion': nueva_cancha.descripcion,
            'precio': nueva_cancha.precio,
            'mensaje': 'Cancha creada exitosamente'
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# PUT - Modificar una cancha
@canchas_bp.route('/<int:id>', methods=['PUT'])
def modificar_cancha(id):
    try:
        cancha = Cancha.query.get(id)
        
        if not cancha:
            return jsonify({'error': 'Cancha no encontrada'}), 404
        
        data = request.get_json()
        
        # Actualizar solo los campos que se proporcionan
        if 'nombre' in data:
            cancha.nombre = data['nombre']
        if 'cantidad' in data:
            cancha.cantidad = data['cantidad']
        if 'descripcion' in data:
            cancha.descripcion = data['descripcion']
        if 'precio' in data:
            cancha.precio = data['precio']
        
        # Actualizar horarios si se proporcionaron
        if 'horarios' in data:
            # Eliminar los horarios actuales
            CanchaHorario.query.filter_by(cancha_id=id).delete()
            
            # Agregar los nuevos horarios
            horarios_ids = data['horarios']
            for horario_id in horarios_ids:
                cancha_horario = CanchaHorario(
                    cancha_id=id,
                    horario_id=horario_id
                )
                db.session.add(cancha_horario)
        
        db.session.commit()
        
        return jsonify({
            'id': cancha.id,
            'nombre': cancha.nombre,
            'cantidad': cancha.cantidad,
            'descripcion': cancha.descripcion,
            'precio': cancha.precio,
            'mensaje': 'Cancha modificada exitosamente'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# DELETE - Eliminar una cancha
@canchas_bp.route('/<int:id>', methods=['DELETE'])
def eliminar_cancha(id):
    try:
        cancha = Cancha.query.get(id)
        
        if not cancha:
            return jsonify({'error': 'Cancha no encontrada'}), 404
        
        # Eliminar registros asociados para evitar error de FK
        CanchaHorario.query.filter_by(cancha_id=id).delete()
        Reserva.query.filter_by(cancha_id=id).delete()
        
        db.session.delete(cancha)
        db.session.commit()
        
        return jsonify({'mensaje': 'Cancha eliminada exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
