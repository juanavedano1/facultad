# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-clave-super-secreta-y-dificil-de-adivinar-para-desarrollo'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SIMULATION_MODE = os.environ.get('SIMULATION_MODE', 'False').lower() == 'true'

    # --- Lógica mejorada para determinar SQLALCHEMY_DATABASE_URI ---
    DATABASE_URL_FROM_ENV = os.environ.get('DATABASE_URL')
    _final_sqlalchemy_database_uri = None # Variable temporal

    if DATABASE_URL_FROM_ENV:
        # Si DATABASE_URL está en el entorno, la usamos.
        # Corregimos "postgres://" a "postgresql://" si es necesario.
        if DATABASE_URL_FROM_ENV.startswith("postgres://"):
            _final_sqlalchemy_database_uri = DATABASE_URL_FROM_ENV.replace("postgres://", "postgresql://", 1)
        else:
            # Si es cualquier otra cosa (ej. una URL de MySQL), la usamos tal cual.
            _final_sqlalchemy_database_uri = DATABASE_URL_FROM_ENV
        print(f"INFO config.py: DATABASE_URL encontrada en el entorno.")
    else:
        # Si DATABASE_URL NO está en el entorno, usamos la configuración local de PostgreSQL.
        PG_USER = os.environ.get('PG_USER') or 'juan'
        PG_PASSWORD = os.environ.get('PG_PASSWORD') or 'juancho16'
        PG_HOST = os.environ.get('PG_HOST') or 'localhost'
        PG_PORT = os.environ.get('PG_PORT') or '5432'
        PG_DB_NAME = os.environ.get('PG_DB_NAME') or 'customer_portal_dev'
        _final_sqlalchemy_database_uri = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}"
        print(f"INFO config.py: DATABASE_URL no encontrada en el entorno. Usando fallback a PostgreSQL local.")

    SQLALCHEMY_DATABASE_URI = _final_sqlalchemy_database_uri

    # Imprimimos la URI que REALMENTE se va a usar (ocultando la contraseña)
    if SQLALCHEMY_DATABASE_URI:
        uri_parts = SQLALCHEMY_DATABASE_URI.split('@')
        auth_part = uri_parts[0].split(':')
        # postgresql://usuario:contraseña@host/db  -> auth_part = ['postgresql://usuario','contraseña']
        # mysql+pymysql://usuario:contraseña@host/db -> auth_part = ['mysql+pymysql://usuario','contraseña']
        if len(auth_part) > 1 and len(uri_parts) > 1:
             print(f"INFO config.py: SQLALCHEMY_DATABASE_URI establecida a: {auth_part[0]}:******@{uri_parts[1]}")
        else: # Si no tiene @ o no tiene : en la parte de auth
             print(f"INFO config.py: SQLALCHEMY_DATABASE_URI establecida a: {SQLALCHEMY_DATABASE_URI} (Formato no esperado para ocultar contraseña)")
    else:
        print("ERROR config.py: SQLALCHEMY_DATABASE_URI no pudo ser establecida.")