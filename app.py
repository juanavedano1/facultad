# C:\Users\Juan Avedano\Desktop\Facultad\Proyecto\app.py

import os
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
from flask import jsonify 
from sqlalchemy import func 


# === IMPORTAR la instancia 'db' declarada en models.py ===
from models import db, User, Service, Complaint, user_services_association 

print("=== DEBUG: app.py ha sido recargado y ejecutado ===") # Este print se ejecuta cuando el módulo es cargado

# Definición de la función create_app
def create_app():
    # === INSTANCIA DE LA APP Y CONFIGURACIÓN ===
    app = Flask(__name__)

    csrf = CSRFProtect(app)
    app.config.from_object(Config)
    # --- Configuración de la base de datos MySQL (comentadas, asumo que usas Config.py) ---
    #app.config["SECRET_KEY"] = "PirataCordobesInstaMegaNashey2025"
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:juancho16@localhost:3306/customer_portal'
    #app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    #app.config['SIMULATION_MODE'] = False 

    # === INSTANCIAS DE EXTENSIÓN INICIALIZADAS CON LA APP YA CONFIGURADA ===
    db.init_app(app) 
    
    # Bcrypt inicializado aquí, dentro de create_app
    # Para acceder a él fuera de create_app, usaremos current_app.extensions['flask-bcrypt']
    bcrypt_instance = Bcrypt(app) 

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

        # >>>>>>>>>>>>>> CORRECCIÓN DE INDENTACIÓN AQUÍ <<<<<<<<<<<<<<
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
        # >>>>>>>>>>>>>> FIN DE CORRECCIÓN DE INDENTACIÓN <<<<<<<<<<<<<<

    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    @login_manager.user_loader
    def load_user(user_id):
        # Asegúrate de usar .get() para la configuración
        if app.config.get('SIMULATION_MODE', False): 
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
            user = User.query.get(int(user_id))
            if user and user.is_active: 
                return user
            return None 

    # --- Rutas de Autenticación y Registro (DENTRO de create_app) ---
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user:
                # Usa la instancia de bcrypt que se inicializó dentro de create_app
                if bcrypt_instance.check_password_hash(user.password, form.password.data):
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
                    flash('Nombre de usuario o contraseña incorrectos.', 'danger')
            else:
                flash('Nombre de usuario o contraseña incorrectos.', 'danger')
        return render_template('auth.html', title='Iniciar Sesión', form=form, form_register=RegistrationForm())

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        form_register = RegistrationForm()
        if form_register.validate_on_submit():
            existing_user = User.query.filter_by(username=form_register.username.data).first()
            existing_email = User.query.filter_by(email=form_register.email.data).first()

            if existing_user:
                flash('Ese nombre de usuario ya está en uso. Por favor, elige otro.', 'danger')
                return render_template('auth.html', title='Registrarse', form=LoginForm(), form_register=form_register)
            if existing_email:
                flash('Ese correo electrónico ya está registrado. Por favor, usa otro.', 'danger')
                return render_template('auth.html', title='Registrarse', form=LoginForm(), form_register=form_register)

            # Usa la instancia de bcrypt de create_app
            hashed_password = bcrypt_instance.generate_password_hash(form_register.password.data).decode('utf-8')
            user = User(username=form_register.username.data, email=form_register.email.data, password=hashed_password, is_active=True)
            db.session.add(user)
            db.session.commit()
            
            flash('¡Tu cuenta ha sido creada con éxito! Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth.html', title='Registrarse', form=LoginForm(), form_register=form_register)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Has cerrado sesión.', 'info')
        return redirect(url_for('login'))

    # --- Rutas de la Raíz (DENTRO de create_app) ---
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('customer_dashboard.index'))
        return redirect(url_for('login'))

    # === Importar Blueprints aquí (DENTRO de create_app, después de las rutas que los usan) ===
    from customer_dashboard.views import customer_dashboard_bp
    from admin.views import admin_bp 

    # --- Registro de Blueprints (DENTRO de create_app, y ANTES del return app) ---
    app.register_blueprint(customer_dashboard_bp, url_prefix='/customer')
    app.register_blueprint(admin_bp)

    return app # <--- ¡Este return debe ser la ÚLTIMA LÍNEA de create_app!

# --- La instancia de la aplicación que Gunicorn y Flask CLI usarán ---
app = create_app()

# --- Comando CLI para seeding (AFUERA de create_app, usando la 'app' global) ---
@app.cli.command("seed-data")
def seed_data_command():
    """Crea el usuario admin y servicios de ejemplo si no existen."""
    with app.app_context():
        try:
            print("Verificando y creando usuario admin y servicios de ejemplo...")
            # Accede a bcrypt a través de current_app.extensions si se inicializó dentro de create_app
            # Flask-Bcrypt guarda su instancia bajo la clave 'flask-bcrypt' en app.extensions
            bcrypt_from_app = current_app.extensions['flask-bcrypt'] 

            if not User.query.filter_by(username='admin').first():
                # Usa la instancia de bcrypt obtenida del contexto
                hashed_password = bcrypt_from_app.generate_password_hash('admin123').decode('utf-8')
                admin_user = User(username='admin', email='admin@example.com', password=hashed_password, is_admin=True, is_active=True)
                db.session.add(admin_user)
                db.session.commit()
                print("Usuario admin creado automáticamente.")
            else:
                print("El usuario admin ya existe, no se creó.")

            if not Service.query.first():
                service1 = Service(name="Internet Fibra Óptica 300Mbps", description="Conexión de alta velocidad para hogar y teletrabajo.", price=35000.00)
                service2 = Service(name="Telefonía Fija Ilimitada", description="Llamadas ilimitadas a números fijos nacionales.", price=15000.00)
                service3 = Service(name="TV Cable Premium", description="Paquete con más de 100 canales HD, incluye deportes y películas.", price=25000.00)
                db.session.add_all([service1, service2, service3])
                db.session.commit()
                print("Servicios de ejemplo creados automáticamente.")
            else:
                print("Los servicios ya existen, no se crearon nuevos.")
            print("Proceso de seeding completado.")

        except Exception as e:
            print(f"Error durante el seeding de datos: {e}")
            import traceback
            traceback.print_exc()

# Bloque de ejecución principal para desarrollo local
if __name__ == '__main__': 
    # Asegúrate de que no haya código de seeding aquí si ya tienes el comando CLI
    app.run(debug=True)