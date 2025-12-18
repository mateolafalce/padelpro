from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time

db = SQLAlchemy()

# Tabla: Horario
class Horario(db.Model):
    __tablename__ = 'horario'
    id = db.Column(db.Integer, primary_key=True)
    dia = db.Column(db.String(45), nullable=False)
    hora = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<Horario {self.dia} {self.hora}>'

# Tabla: Cancha
class Cancha(db.Model):
    __tablename__ = 'cancha'
    id = db.Column(db.Integer, primary_key=True)
    cantidad = db.Column(db.Integer, nullable=False)
    nombre = db.Column(db.String(45), nullable=False)
    descripcion = db.Column(db.String(100))
    precio = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<Cancha {self.nombre}>'

# Tabla: CanchaHorario
class CanchaHorario(db.Model):
    __tablename__ = 'cancha_horario'
    id = db.Column(db.Integer, primary_key=True)
    cancha_id = db.Column(db.Integer, db.ForeignKey('cancha.id'), nullable=False)
    horario_id = db.Column(db.Integer, db.ForeignKey('horario.id'), nullable=False)
    
    cancha = db.relationship('Cancha', backref='horarios')
    horario = db.relationship('Horario', backref='canchas')

    def __repr__(self):
        return f'<CanchaHorario cancha_id={self.cancha_id} horario_id={self.horario_id}>'

# Tabla: Cliente
class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(45), nullable=False)
    apellido = db.Column(db.String(45), nullable=False)
    telefono = db.Column(db.String(50))
    categoria = db.Column(db.Integer)

    def __repr__(self):
        return f'<Cliente {self.nombre} {self.apellido}>'

# Tabla: Estado
class Estado(db.Model):
    __tablename__ = 'estado'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(45), nullable=False, unique=True)

    def __repr__(self):
        return f'<Estado {self.nombre}>'

# Tabla: Reserva
class Reserva(db.Model):
    __tablename__ = 'reserva'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    # Cambiado a String para coincidir con el formato de Horario
    hora = db.Column(db.String(20), nullable=False)
    cancha_id = db.Column(db.Integer, db.ForeignKey('cancha.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    estado_id = db.Column(db.Integer, db.ForeignKey('estado.id'), nullable=False)
    monto = db.Column(db.Float, default=0.0)
    
    cancha = db.relationship('Cancha', backref='reservas')
    cliente = db.relationship('Cliente', backref='reservas')
    estado = db.relationship('Estado', backref='reservas')

    def __repr__(self):
        return f'<Reserva {self.id} - {self.fecha} {self.hora}>'

# Tabla: FechaHorarioNo (Fechas y horarios no disponibles)
class FechaHorarioNo(db.Model):
    __tablename__ = 'fecha_horario_no'
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    horario_id = db.Column(db.Integer, db.ForeignKey('horario.id'), nullable=False)
    
    horario = db.relationship('Horario', backref='fechas_no_disponibles')

    def __repr__(self):
        return f'<FechaHorarioNo {self.fecha}>'

# Tabla: Configuracion (Configuración del sistema)
class Configuracion(db.Model):
    __tablename__ = 'configuracion'
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(50), nullable=False, unique=True)
    valor = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<Configuracion {self.clave}={self.valor}>'

# Tabla: Conversacion (Historial de mensajes)
class Conversacion(db.Model):
    __tablename__ = 'conversacion'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    usuario = db.Column(db.String(50), nullable=False)  # Número de teléfono o '99999999' para local
    rol = db.Column(db.String(20), nullable=False)  # 'user' o 'assistant'
    mensaje = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f'<Conversacion {self.usuario} - {self.rol}>'
    
    def to_dict(self):
        """Convierte el mensaje al formato de OpenAI"""
        return {
            'role': self.rol,
            'content': self.mensaje
        }

# Función para crear todas las tablas
def crear_tablas(app):
    with app.app_context():
        db.create_all()
        print("Tablas creadas exitosamente en la base de datos 'padelpro'")
        
        # Insertar estados si no existen
        estados_predeterminados = ['iniciada', 'ejecutada', 'cancelada', 'bloqueada']
        for nombre_estado in estados_predeterminados:
            if not Estado.query.filter_by(nombre=nombre_estado).first():
                nuevo_estado = Estado(nombre=nombre_estado)
                db.session.add(nuevo_estado)
        
        db.session.commit()
        print("Estados insertados: iniciada, ejecutada, cancelada, bloqueada")
        
        # Insertar horarios predeterminados si no existen
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        horas = ['08:00-09:00', '09:00-10:00', '10:00-11:00', '11:00-12:00', '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00', '18:00-19:00', '19:00-20:00', '20:00-21:00', '21:00-22:00', '22:00-23:00']
        
        for dia in dias:
            for hora_str in horas:
                # Verificar si ya existe
                # Almacenamos el rango completo como string
                if not Horario.query.filter_by(dia=dia, hora=hora_str).first():
                    nuevo_horario = Horario(dia=dia, hora=hora_str)
                    db.session.add(nuevo_horario)
        
        db.session.commit()
        print("Horarios predeterminados insertados")
        
        # Insertar configuración predeterminada si no existe
        configs_predeterminadas = [
            {'clave': 'cbu', 'valor': ''},
            {'clave': 'alias', 'valor': ''},
            {'clave': 'business_name', 'valor': 'Complejo de Padel'},
            {'clave': 'business_kind', 'valor': 'PadelPro'},
            {'clave': 'business_address', 'valor': '69 entre 119 y 120'}
        ]
        for config in configs_predeterminadas:
            if not Configuracion.query.filter_by(clave=config['clave']).first():
                nueva_config = Configuracion(clave=config['clave'], valor=config['valor'])
                db.session.add(nueva_config)
        
        db.session.commit()
        print("Configuración predeterminada insertada (CBU, Alias y datos del negocio)")

if __name__ == '__main__':
    from flask import Flask
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://padelpro:padelpro123@localhost/padelpro'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    crear_tablas(app)
