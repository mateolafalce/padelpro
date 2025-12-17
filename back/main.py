from flask import Flask, send_from_directory
from dotenv import load_dotenv
import os

load_dotenv()

from bd import db
from abml_canchas import canchas_bp
from chat_bp import chat_bp
from abml_reservas import reservas_bp
from cancelar_horario import cancelar_bp
from wsp import wsp_bp
from admin_config import admin_bp
from historial_bp import historial_bp

app = Flask(__name__)

# Configuración de la base de datos MariaDB
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://padelpro:padelpro123@localhost/padelpro'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Registrar blueprints
app.register_blueprint(canchas_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(reservas_bp)
app.register_blueprint(cancelar_bp)
app.register_blueprint(wsp_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(historial_bp)

# Ruta a la carpeta front
FRONT_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'front')

@app.route('/')
def home():
	return send_from_directory(FRONT_FOLDER, 'index.html')

@app.route('/abml-canchas')
def abml_canchas():
	return send_from_directory(FRONT_FOLDER, 'abml_canchas.html')

@app.route('/abml-clientes')
def abml_clientes():
	return "<h1>ABML Clientes - Próximamente</h1>"

@app.route('/abml-reservas')
def abml_reservas():
	return send_from_directory(FRONT_FOLDER, 'abml_reservas.html')

@app.route('/cancelar')
def cancelar():
	return send_from_directory(FRONT_FOLDER, 'cancelar.html')

@app.route('/chat')
def chat():
	return send_from_directory(FRONT_FOLDER, 'chat.html')

@app.route('/admin')
def admin():
	return send_from_directory(FRONT_FOLDER, 'admin.html')

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=8080)
