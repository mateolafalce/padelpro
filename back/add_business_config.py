"""
Script para añadir configuraciones adicionales (nombre, tipo y ubicación del negocio)
"""
from flask import Flask
from bd import db, Configuracion

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://padelpro:padelpro123@localhost/padelpro'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Insertar nuevas configuraciones si no existen
    configs_adicionales = [
        {'clave': 'business_name', 'valor': 'Complejo de Padel'},
        {'clave': 'business_kind', 'valor': 'PadelPro'},
        {'clave': 'business_address', 'valor': '69 entre 119 y 120'}
    ]
    
    for config in configs_adicionales:
        existing = Configuracion.query.filter_by(clave=config['clave']).first()
        if not existing:
            nueva_config = Configuracion(clave=config['clave'], valor=config['valor'])
            db.session.add(nueva_config)
            print(f"✅ Configuración '{config['clave']}' añadida con valor: '{config['valor']}'")
        else:
            print(f"ℹ️  Configuración '{config['clave']}' ya existe con valor: '{existing.valor}'")
    
    db.session.commit()
    print("\n✅ Configuraciones adicionales añadidas exitosamente!")
