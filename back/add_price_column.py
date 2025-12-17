from flask import Flask
from bd import db
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://padelpro:padelpro123@localhost/padelpro'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def add_price_column():
    with app.app_context():
        try:
            # Check if column exists
            result = db.session.execute(text("SHOW COLUMNS FROM cancha LIKE 'precio'"))
            if result.fetchone():
                print("La columna 'precio' ya existe en 'cancha'.")
            else:
                print("Agregando columna 'precio' a tabla 'cancha'...")
                db.session.execute(text("ALTER TABLE cancha ADD COLUMN precio FLOAT DEFAULT 0.0"))
                print("Columna agregada exitosamente.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    add_price_column()
