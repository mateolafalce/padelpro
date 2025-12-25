from flask import Flask
from bd import db, Horario, CanchaHorario, FechaHorarioNo, Reserva
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://padelpro:padelpro123@localhost/padelpro'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def reset_and_recreate_horarios():
    with app.app_context():
        print("Recreando tablas de Horarios y Reservas con nuevo esquema (String)...")
        
        # Borrar tablas en orden correcto (Hijos primero)
        # CanchaHorario y FechaHorarioNo dependen de Horario
        try:
            CanchaHorario.__table__.drop(db.engine)
            print("Tabla CanchaHorario eliminada.")
        except Exception as e:
            print(f"Nota: {e}")

        try:
            FechaHorarioNo.__table__.drop(db.engine)
            print("Tabla FechaHorarioNo eliminada.")
        except Exception as e:
            print(f"Nota: {e}")

        try:
            Reserva.__table__.drop(db.engine)
            print("Tabla Reserva eliminada.")
        except Exception as e:
            print(f"Nota: {e}")

        try:
            Horario.__table__.drop(db.engine)
            print("Tabla Horario eliminada.")
        except Exception as e:
            print(f"Nota: {e}")
        
        # Re-crear tablas (solo las que faltan)
        db.create_all()
        print("Tablas re-creadas.")
        
        # Rellenar Horarios
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        horas = ['08:00-09:00', '10:00-11:00', '12:00-13:00', '14:00-15:00', 
                 '16:00-17:00', '18:00-19:00', '20:00-21:00', '22:00-23:00']
        
        count = 0
        for dia in dias:
            for hora_str in horas:
                # Ahora guardamos el string directo "08:00-09:00"
                nuevo_horario = Horario(dia=dia, hora=hora_str)
                db.session.add(nuevo_horario)
                count += 1
        
        db.session.commit()
        print(f"¡Éxito! Insertados {count} horarios con formato de rango.")

if __name__ == '__main__':
    reset_and_recreate_horarios()
