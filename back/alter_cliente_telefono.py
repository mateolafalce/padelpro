from flask import Flask
from bd import db
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://padelpro:padelpro123@localhost/padelpro'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def alter_telefono_column():
    with app.app_context():
        try:
            print("Modificando columna 'telefono' en tabla 'cliente' a VARCHAR(50)...")
            # En MySQL, MODIFY COLUMN permite cambiar el tipo
            db.session.execute(text("ALTER TABLE cliente MODIFY COLUMN telefono VARCHAR(50)"))
            db.session.commit()
            print("Columna modificada exitosamente.")
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    alter_telefono_column()
