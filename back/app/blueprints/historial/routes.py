"""
Blueprint para gestionar el historial de conversaciones
"""
from flask import Blueprint, request, jsonify
from app.models import db, Conversacion
from app.services.historial_utils import obtener_estadisticas_usuario, obtener_historial
from sqlalchemy import func

historial_bp = Blueprint('historial', __name__, url_prefix='/api/historial')

@historial_bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    """Lista todos los usuarios con conversaciones"""
    try:
        # Obtener parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Obtener usuarios únicos con conteo de mensajes
        usuarios_query = db.session.query(
            Conversacion.usuario,
            func.count(Conversacion.id).label('total_mensajes'),
            func.max(Conversacion.fecha).label('ultimo_mensaje')
        ).group_by(Conversacion.usuario)\
         .order_by(func.max(Conversacion.fecha).desc())
        
        # Paginar
        total = usuarios_query.count()
        usuarios = usuarios_query.limit(per_page).offset((page - 1) * per_page).all()
        
        resultado = []
        for usuario, total_mensajes, ultimo_mensaje in usuarios:
            resultado.append({
                'usuario': usuario,
                'total_mensajes': total_mensajes,
                'ultimo_mensaje': ultimo_mensaje.isoformat() if ultimo_mensaje else None,
                'tipo': 'Local' if usuario == '99999999' else 'WhatsApp'
            })
        
        return jsonify({
            'success': True,
            'usuarios': resultado,
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@historial_bp.route('/usuario/<usuario>', methods=['GET'])
def obtener_conversacion_usuario(usuario):
    """Obtiene el historial completo de un usuario"""
    try:
        limite = request.args.get('limite', 50, type=int)
        
        mensajes = obtener_historial(usuario, limite=limite)
        estadisticas = obtener_estadisticas_usuario(usuario)
        
        return jsonify({
            'success': True,
            'usuario': usuario,
            'mensajes': mensajes,
            'estadisticas': {
                'total_mensajes': estadisticas['total_mensajes'],
                'mensajes_usuario': estadisticas['mensajes_usuario'],
                'mensajes_asistente': estadisticas['mensajes_asistente'],
                'primer_mensaje': estadisticas['primer_mensaje'].isoformat() if estadisticas['primer_mensaje'] else None,
                'ultimo_mensaje': estadisticas['ultimo_mensaje'].isoformat() if estadisticas['ultimo_mensaje'] else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@historial_bp.route('/usuario/<usuario>', methods=['DELETE'])
def eliminar_conversacion_usuario(usuario):
    """Elimina todo el historial de un usuario"""
    try:
        Conversacion.query.filter_by(usuario=usuario).delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Historial de {usuario} eliminado correctamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@historial_bp.route('/estadisticas', methods=['GET'])
def estadisticas_generales():
    """Obtiene estadísticas generales del sistema"""
    try:
        total_mensajes = Conversacion.query.count()
        total_usuarios = db.session.query(func.count(func.distinct(Conversacion.usuario))).scalar()
        
        mensajes_por_rol = db.session.query(
            Conversacion.rol,
            func.count(Conversacion.id)
        ).group_by(Conversacion.rol).all()
        
        usuarios_activos_hoy = db.session.query(
            func.count(func.distinct(Conversacion.usuario))
        ).filter(
            func.date(Conversacion.fecha) == func.current_date()
        ).scalar()
        
        return jsonify({
            'success': True,
            'estadisticas': {
                'total_mensajes': total_mensajes,
                'total_usuarios': total_usuarios,
                'usuarios_activos_hoy': usuarios_activos_hoy,
                'mensajes_por_rol': dict(mensajes_por_rol)
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
