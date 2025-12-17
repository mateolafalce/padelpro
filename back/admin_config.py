from flask import Blueprint, request, jsonify
from bd import db, Configuracion
import os

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/api/configuracion', methods=['GET'])
def obtener_configuracion():
    """Obtiene la configuración actual de CBU, Alias y datos del negocio"""
    try:
        cbu_config = Configuracion.query.filter_by(clave='cbu').first()
        alias_config = Configuracion.query.filter_by(clave='alias').first()
        business_name_config = Configuracion.query.filter_by(clave='business_name').first()
        business_kind_config = Configuracion.query.filter_by(clave='business_kind').first()
        business_address_config = Configuracion.query.filter_by(clave='business_address').first()
        
        return jsonify({
            'success': True,
            'cbu': cbu_config.valor if cbu_config else '',
            'alias': alias_config.valor if alias_config else '',
            'business_name': business_name_config.valor if business_name_config else 'Complejo de Padel',
            'business_kind': business_kind_config.valor if business_kind_config else 'PadelPro',
            'business_address': business_address_config.valor if business_address_config else '69 entre 119 y 120'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/configuracion', methods=['POST'])
def actualizar_configuracion():
    """Actualiza la configuración de CBU, Alias y datos del negocio"""
    try:
        data = request.get_json()
        cbu = data.get('cbu', '').strip()
        alias = data.get('alias', '').strip()
        business_name = data.get('business_name', '').strip()
        business_kind = data.get('business_kind', '').strip()
        business_address = data.get('business_address', '').strip()
        
        # Actualizar o crear CBU
        cbu_config = Configuracion.query.filter_by(clave='cbu').first()
        if cbu_config:
            cbu_config.valor = cbu
        else:
            cbu_config = Configuracion(clave='cbu', valor=cbu)
            db.session.add(cbu_config)
        
        # Actualizar o crear Alias
        alias_config = Configuracion.query.filter_by(clave='alias').first()
        if alias_config:
            alias_config.valor = alias
        else:
            alias_config = Configuracion(clave='alias', valor=alias)
            db.session.add(alias_config)
        
        # Actualizar o crear Business Name
        business_name_config = Configuracion.query.filter_by(clave='business_name').first()
        if business_name_config:
            business_name_config.valor = business_name
        else:
            business_name_config = Configuracion(clave='business_name', valor=business_name)
            db.session.add(business_name_config)
        
        # Actualizar o crear Business Kind
        business_kind_config = Configuracion.query.filter_by(clave='business_kind').first()
        if business_kind_config:
            business_kind_config.valor = business_kind
        else:
            business_kind_config = Configuracion(clave='business_kind', valor=business_kind)
            db.session.add(business_kind_config)
        
        # Actualizar o crear Business Address
        business_address_config = Configuracion.query.filter_by(clave='business_address').first()
        if business_address_config:
            business_address_config.valor = business_address
        else:
            business_address_config = Configuracion(clave='business_address', valor=business_address)
            db.session.add(business_address_config)
        
        db.session.commit()
        
        # Actualizar también el archivo .env si existe
        actualizar_env_file(cbu, alias, business_name, business_kind, business_address)
        
        return jsonify({
            'success': True,
            'message': 'Configuración actualizada correctamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def actualizar_env_file(cbu, alias, business_name, business_kind, business_address):
    """Actualiza el archivo .env con los nuevos valores"""
    try:
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        
        if os.path.exists(env_path):
            # Leer el archivo actual
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Actualizar las líneas
            cbu_found = False
            alias_found = False
            business_name_found = False
            business_kind_found = False
            business_address_found = False
            
            for i, line in enumerate(lines):
                if line.startswith('CBU='):
                    lines[i] = f'CBU={cbu}\n'
                    cbu_found = True
                elif line.startswith('ALIAS='):
                    lines[i] = f'ALIAS={alias}\n'
                    alias_found = True
                elif line.startswith('BUSINESS_NAME='):
                    lines[i] = f'BUSINESS_NAME={business_name}\n'
                    business_name_found = True
                elif line.startswith('BUSINESS_KIND='):
                    lines[i] = f'BUSINESS_KIND={business_kind}\n'
                    business_kind_found = True
                elif line.startswith('BUSINESS_ADDRESS='):
                    lines[i] = f'BUSINESS_ADDRESS={business_address}\n'
                    business_address_found = True
            
            # Si no se encontraron, añadirlas al final
            if not cbu_found:
                lines.append(f'CBU={cbu}\n')
            if not alias_found:
                lines.append(f'ALIAS={alias}\n')
            if not business_name_found:
                lines.append(f'BUSINESS_NAME={business_name}\n')
            if not business_kind_found:
                lines.append(f'BUSINESS_KIND={business_kind}\n')
            if not business_address_found:
                lines.append(f'BUSINESS_ADDRESS={business_address}\n')
            
            # Escribir el archivo actualizado
            with open(env_path, 'w') as f:
                f.writelines(lines)
    except Exception as e:
        print(f"Error actualizando .env: {e}")
