from flask import Flask
from bd import db
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://padelpro:padelpro123@localhost/padelpro'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def add_monto_column():
    with app.app_context():
        try:
            # Check if column exists
            result = db.session.execute(text("SHOW COLUMNS FROM reserva LIKE 'monto'"))
            if result.fetchone():
                print("La columna 'monto' ya existe en 'reserva'.")
            else:
                print("Agregando columna 'monto' a tabla 'reserva'...")
                db.session.execute(text("ALTER TABLE reserva ADD COLUMN monto FLOAT DEFAULT 0.0"))
                db.session.commit()
                print("Columna agregada exitosamente.")
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    add_monto_column()
