"""
Script para añadir la tabla de conversaciones
"""
from flask import Flask
from bd import db, Conversacion

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://padelpro:padelpro123@localhost/padelpro'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    # Crear la tabla de conversaciones
    db.create_all()
    print("✅ Tabla 'conversacion' creada exitosamente")
    print("\nEstructura de la tabla:")
    print("  - id (INT, PRIMARY KEY, AUTO_INCREMENT)")
    print("  - fecha (DATETIME, DEFAULT CURRENT_TIMESTAMP)")
    print("  - usuario (VARCHAR(50), NOT NULL) - Número de teléfono o '99999999' para local")
    print("  - rol (VARCHAR(20), NOT NULL) - 'user' o 'assistant'")
    print("  - mensaje (TEXT, NOT NULL)")
    print("\n✅ Migración completada exitosamente!")
