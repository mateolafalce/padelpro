from flask import Flask
from bd import db, Horario

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://padelpro:padelpro123@localhost/padelpro'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    horarios = Horario.query.order_by(Horario.dia, Horario.hora).all()
    print(f"\n{'ID':<5} {'Día':<10} {'Hora':<10}")
    print("-" * 30)
    for h in horarios:
        print(f"{h.id:<5} {h.dia:<10} {h.hora}")
