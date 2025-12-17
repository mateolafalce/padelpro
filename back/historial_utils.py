"""
Utilidades para gestionar el historial de conversaciones
"""
from bd import db, Conversacion
from datetime import datetime


def guardar_mensaje(usuario: str, rol: str, mensaje: str):
    """
    Guarda un mensaje en el historial de conversaciones
    
    Args:
        usuario: Número de teléfono o '99999999' para local
        rol: 'user' o 'assistant'
        mensaje: Contenido del mensaje
    """
    try:
        nueva_conversacion = Conversacion(
            usuario=usuario,
            rol=rol,
            mensaje=mensaje
        )
        db.session.add(nueva_conversacion)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error guardando mensaje: {e}")
        db.session.rollback()
        return False


def obtener_historial(usuario: str, limite: int = 10):
    """
    Obtiene los últimos N mensajes de un usuario
    
    Args:
        usuario: Número de teléfono o '99999999' para local
        limite: Cantidad de mensajes a recuperar (default: 10)
    
    Returns:
        Lista de diccionarios con formato OpenAI: [{'role': 'user', 'content': '...'}, ...]
    """
    try:
        mensajes = Conversacion.query.filter_by(usuario=usuario)\
            .order_by(Conversacion.fecha.desc())\
            .limit(limite)\
            .all()
        
        # Invertir el orden para que los más antiguos estén primero
        mensajes.reverse()
        
        return [msg.to_dict() for msg in mensajes]
    except Exception as e:
        print(f"Error obteniendo historial: {e}")
        return []


def limpiar_historial_antiguo(usuario: str, mantener_ultimos: int = 50):
    """
    Limpia mensajes antiguos manteniendo solo los últimos N
    
    Args:
        usuario: Número de teléfono o '99999999' para local
        mantener_ultimos: Cantidad de mensajes a mantener (default: 50)
    """
    try:
        # Obtener el ID del mensaje N-ésimo más reciente
        mensajes = Conversacion.query.filter_by(usuario=usuario)\
            .order_by(Conversacion.fecha.desc())\
            .limit(mantener_ultimos)\
            .all()
        
        if len(mensajes) == mantener_ultimos:
            # Hay más de N mensajes, eliminar los antiguos
            ultimo_id_a_mantener = mensajes[-1].id
            
            Conversacion.query.filter(
                Conversacion.usuario == usuario,
                Conversacion.id < ultimo_id_a_mantener
            ).delete()
            
            db.session.commit()
            return True
    except Exception as e:
        print(f"Error limpiando historial: {e}")
        db.session.rollback()
        return False


def obtener_estadisticas_usuario(usuario: str):
    """
    Obtiene estadísticas de conversación de un usuario
    
    Args:
        usuario: Número de teléfono o '99999999' para local
    
    Returns:
        Dict con estadísticas
    """
    try:
        total_mensajes = Conversacion.query.filter_by(usuario=usuario).count()
        mensajes_usuario = Conversacion.query.filter_by(usuario=usuario, rol='user').count()
        mensajes_asistente = Conversacion.query.filter_by(usuario=usuario, rol='assistant').count()
        
        primer_mensaje = Conversacion.query.filter_by(usuario=usuario)\
            .order_by(Conversacion.fecha.asc())\
            .first()
        
        ultimo_mensaje = Conversacion.query.filter_by(usuario=usuario)\
            .order_by(Conversacion.fecha.desc())\
            .first()
        
        return {
            'total_mensajes': total_mensajes,
            'mensajes_usuario': mensajes_usuario,
            'mensajes_asistente': mensajes_asistente,
            'primer_mensaje': primer_mensaje.fecha if primer_mensaje else None,
            'ultimo_mensaje': ultimo_mensaje.fecha if ultimo_mensaje else None
        }
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return None
