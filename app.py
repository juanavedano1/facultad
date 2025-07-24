# C:\Users\Juan Avedano\Desktop\Facultad\Proyecto\app.py

import os
import pandas as pd
import io
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.cell.cell import MergedCell
from flask import send_file
from flask import Flask, render_template, redirect, url_for, flash, request, Blueprint, current_app
from flask_login import LoginManager, login_user, current_user, logout_user, login_required, UserMixin
from forms import LoginForm, RegistrationForm, UserEditForm, ContractServiceForm, ToggleUserStatusForm
from config import Config # <-- Mantenla comentada si no tienes un config.py con tu URL de DB
from functools import wraps
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask import jsonify # Probablemente ya lo tienes
from sqlalchemy import func # ¡Importante!
#from flask_wtf import FlaskForm
#from wtforms import SubmitField
# Importar el blueprint del customer_dashboard
from customer_dashboard.views import customer_dashboard_bp

from admin.views import admin_bp #

# === IMPORTAR la instancia 'db' declarada en models.py ===
from models import db, User, Service, Complaint, user_services_association # <-- Importa 'db' también, junto con los modelos

print("=== DEBUG: app.py ha sido recargado y ejecutado ===")
# === INSTANCIA DE LA APP Y CONFIGURACIÓN ===
app = Flask(__name__)

csrf = CSRFProtect(app)
app.config.from_object(Config)
# --- Configuración de la base de datos MySQL ---
#app.config["SECRET_KEY"] = "PirataCordobesInstaMegaNashey2025"
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:juancho16@localhost:3306/customer_portal'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['SIMULATION_MODE'] = False # Cambia a True para simulación sin DB real

# === INSTANCIAS DE EXTENSIÓN INICIALIZADAS CON LA APP YA CONFIGURADA ===
db.init_app(app) # <-- Aquí inicializamos la 'db' que los modelos están usando.

bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.init_app(app)
migrate = Migrate(app, db)

# Define un User mock para el modo simulación si no hay DB real
class MockUser(UserMixin):
    def __init__(self, id, username, email, is_admin=False):
        self.id = id
        self.username = username
        self.email = email
        self.is_admin = is_admin

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return True
    @property
    def is_authenticated(self):
        return True
    @property
    def is_anonymous(self):
        return False

    def check_password(self, password):
        mock_passwords = {
            'admin': 'admin123',
            'cliente': 'cliente123',
            'test': 'test123'
        }
        return mock_passwords.get(self.username) == password

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@login_manager.user_loader
def load_user(user_id):
    if app.config['SIMULATION_MODE']:
        mock_users_data = {
            1: {'username': 'admin', 'email': 'admin@example.com', 'is_admin': True},
            2: {'username': 'cliente', 'email': 'cliente@example.com', 'is_admin': False},
            3: {'username': 'test', 'email': 'test@example.com', 'is_admin': False},
        }
        user_data = mock_users_data.get(int(user_id))
        if user_data:
            return MockUser(int(user_id), user_data['username'], user_data['email'], user_data['is_admin'])
        return None
    else:
          # Solo cargar si el usuario existe y está activo
        user = User.query.get(int(user_id))
        if user and user.is_active: # <-- Verificar si el usuario está activo
            return user
        return None # No cargar el usuario si no existe o no está activo


# --- Rutas de Autenticación y Registro ---

# En tu app.py, reemplaza la función login existente por esta:



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        print("--- FORMULARIO DE LOGIN ENVIADO ---") #<-- AÑADE ESTO
        print(f"Intentando iniciar sesión con usuario: '{form.username.data}'") #<-- AÑADE ESTO

        user = User.query.filter_by(username=form.username.data).first()
        print(f"Usuario encontrado en la BD: {user}") #<-- AÑADE ESTO

        if user:
            # Comprobamos la contraseña solo si el usuario existe
            password_check = bcrypt.check_password_hash(user.password, form.password.data)
            print(f"¿La contraseña es correcta?: {password_check}") #<-- AÑADE ESTO
            if password_check:
                # Si el usuario y la contraseña son correctos...
                if user.is_active:
                    login_user(user, remember=form.remember_me.data)
                    flash('Inicio de sesión exitoso!', 'success')
                    if user.is_admin:
                        return redirect(url_for('admin.dashboard'))
                    else:
                        return redirect(url_for('customer_dashboard.index'))
                else:
                    flash('Tu cuenta ha sido desactivada.', 'danger')
            else:
                # Contraseña incorrecta
                flash('Nombre de usuario o contraseña incorrectos.', 'danger')
        else:
            # Usuario no encontrado
            flash('Nombre de usuario o contraseña incorrectos.', 'danger')

    return render_template('auth.html', title='Iniciar Sesión', form=form, form_register=RegistrationForm())

# En tu app.py

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form_register = RegistrationForm()
    
    if form_register.validate_on_submit():
        # --- SOLUCIÓN AL PROBLEMA 1: Verificación de duplicados ---
        existing_user = User.query.filter_by(username=form_register.username.data).first()
        existing_email = User.query.filter_by(email=form_register.email.data).first()

        # Si el usuario ya existe, muestra un error y no intentes guardar
        if existing_user:
            flash('Ese nombre de usuario ya está en uso. Por favor, elige otro.', 'danger')
            # Vuelve a renderizar la página de auth para mostrar el error
            return render_template('auth.html', title='Registrarse', form=LoginForm(), form_register=form_register)

        # Si el email ya existe, muestra un error
        if existing_email:
            flash('Ese correo electrónico ya está registrado. Por favor, usa otro.', 'danger')
            return render_template('auth.html', title='Registrarse', form=LoginForm(), form_register=form_register)

        # Si no hay duplicados, procede a crear el usuario
        hashed_password = bcrypt.generate_password_hash(form_register.password.data).decode('utf-8')
        user = User(username=form_register.username.data, email=form_register.email.data, password=hashed_password, is_active=True)
        db.session.add(user)
        db.session.commit()
        
        flash('¡Tu cuenta ha sido creada con éxito! Ahora puedes iniciar sesión.', 'success')
        
        # --- SOLUCIÓN AL PROBLEMA 2: Redirección a Login ---
        # Simplemente redirigimos a 'login' sin llamar a login_user()
        return redirect(url_for('login'))
    
    # Si el método es GET o la validación falla, renderiza la plantilla
    return render_template('auth.html', title='Registrarse', form=LoginForm(), form_register=form_register)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))

# --- Rutas de la Raíz ---

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('customer_dashboard.index'))
    # Si no está autenticado, lo mandamos a la página de login
    return redirect(url_for('login'))

# --- Registro de Blueprints ---
# ELIMINA ESTA LÍNEA de admin/views.py

app.register_blueprint(customer_dashboard_bp, url_prefix='/customer')
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    with app.app_context():
        try:
            # db.create_all() # Ya comentada, ¡no la descomentes!
            print("Tablas de la base de datos creadas/actualizadas.")

            # Lógica para crear el usuario admin si no existe
            if not User.query.filter_by(username='admin').first():
                hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
                admin_user = User(username='admin', email='admin@example.com', password=hashed_password, is_admin=True, is_active=True)
                db.session.add(admin_user)
                db.session.commit()
                print("Usuario admin creado automáticamente.")
            else:
                print("El usuario admin ya existe, no se creó.")

            # Lógica para crear servicios de ejemplo si no existen
            if not Service.query.first():
                service1 = Service(name="Internet Fibra Óptica 300Mbps", description="Conexión de alta velocidad para hogar y teletrabajo.", price=35000.00)
                service2 = Service(name="Telefonía Fija Ilimitada", description="Llamadas ilimitadas a números fijos nacionales.", price=15000.00)
                service3 = Service(name="TV Cable Premium", description="Paquete con más de 100 canales HD, incluye deportes y películas.", price=25000.00)

                db.session.add_all([service1, service2, service3])
                db.session.commit()
                print("Servicios de ejemplo creados automáticamente.")
            else:
                print("Los servicios ya existen, no se crearon nuevos.")

        except Exception as e:
            print(f"Error en el contexto de la aplicación durante la inicialización: {e}")
            print("Asegúrate de que la base de datos está accesible y las tablas existen.")
    
    app.run(debug=True)