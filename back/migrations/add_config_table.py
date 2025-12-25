"""
Script para añadir la tabla de configuración a la base de datos existente
"""
from flask import Flask
from bd import db, Configuracion

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://padelpro:padelpro123@localhost/padelpro'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Crear la tabla de configuración
    db.create_all()
    print("✅ Tabla 'configuracion' creada exitosamente")
    
    # Insertar valores predeterminados si no existen
    configs_predeterminadas = [
        {'clave': 'cbu', 'valor': ''},
        {'clave': 'alias', 'valor': ''}
    ]
    
    for config in configs_predeterminadas:
        existing = Configuracion.query.filter_by(clave=config['clave']).first()
        if not existing:
            nueva_config = Configuracion(clave=config['clave'], valor=config['valor'])
            db.session.add(nueva_config)
            print(f"✅ Configuración '{config['clave']}' añadida")
        else:
            print(f"ℹ️  Configuración '{config['clave']}' ya existe con valor: '{existing.valor}'")
    
    db.session.commit()
    print("\n✅ Migración completada exitosamente!")
