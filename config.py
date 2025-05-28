# config.py
import os
import re # Importamos 're' para una mejor ocultación de contraseña en el log

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'una-clave-super-secreta-y-dificil-de-adivinar-para-desarrollo'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SIMULATION_MODE = os.environ.get('SIMULATION_MODE', 'False').lower() == 'true'

    # --- Lógica para determinar SQLALCHEMY_DATABASE_URI ---
    DATABASE_URL_FROM_ENV = os.environ.get('DATABASE_URL')
    _final_sqlalchemy_database_uri = None # Variable temporal

    if DATABASE_URL_FROM_ENV:
        # Si DATABASE_URL está en el entorno, la usamos.
        if DATABASE_URL_FROM_ENV.startswith("postgres://"):
            _final_sqlalchemy_database_uri = DATABASE_URL_FROM_ENV.replace("postgres://", "postgresql://", 1)
        else:
            _final_sqlalchemy_database_uri = DATABASE_URL_FROM_ENV
        print(f"INFO config.py: Usando DATABASE_URL del entorno.")
    else:
        # Si DATABASE_URL NO está en el entorno, usamos la configuración local de PostgreSQL.
        PG_USER = os.environ.get('PG_USER') or 'juan'
        PG_PASSWORD = os.environ.get('PG_PASSWORD') or 'juancho16'
        PG_HOST = os.environ.get('PG_HOST') or 'localhost'
        PG_PORT = os.environ.get('PG_PORT') or '5432'
        PG_DB_NAME = os.environ.get('PG_DB_NAME') or 'customer_portal_dev'
        
        # ESTA LÍNEA ES CRUCIAL Y YA ESTABA CORRECTA EN TU CÓDIGO:
        _final_sqlalchemy_database_uri = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB_NAME}"
        
        print(f"INFO config.py: DATABASE_URL no encontrada en el entorno. Usando fallback a PostgreSQL local.")
        # NUEVO PRINT DE DEPURACIÓN: Muestra la URI cruda tal cual se construye
        # Esto te permitirá ver si es correcta ANTES de intentar ocultar la contraseña.
        print(f"DEBUG config.py: URI local cruda construida: {_final_sqlalchemy_database_uri}")

    SQLALCHEMY_DATABASE_URI = _final_sqlalchemy_database_uri

    # --- Imprimimos la URI que REALMENTE se va a usar, intentando ocultar la contraseña ---
    if SQLALCHEMY_DATABASE_URI:
        try:
            # Intenta encontrar usuario:contraseña@ y reemplazar la contraseña
            match = re.match(r"^(?P<scheme_user>[^:]+://[^:]+):(?P<password>[^@]+)@(?P<rest_of_uri>.+)$", SQLALCHEMY_DATABASE_URI)
            if match:
                parts = match.groupdict()
                masked_uri_display = f"{parts['scheme_user']}:******@{parts['rest_of_uri']}"
                print(f"INFO config.py: SQLALCHEMY_DATABASE_URI establecida a: {masked_uri_display}")
            else:
                # Si el patrón complejo no coincide (ej. no hay usuario/contraseña, o es solo DSN)
                # Intenta un ocultamiento más simple si hay un '@'
                uri_parts_at = SQLALCHEMY_DATABASE_URI.split('@')
                if len(uri_parts_at) > 1: # Si hay un '@', asumimos que lo anterior es esquema://usuario:contraseña
                    # Esto es una suposición y podría no ser perfecto para todos los formatos de URI
                    # Muestra solo el esquema y el usuario (si está antes de ':') o solo el esquema
                    auth_part_display = uri_parts_at[0].split(':')[0] 
                    user_maybe = uri_parts_at[0].split('://')[-1].split(':')[0]
                    if user_maybe and user_maybe != auth_part_display: # Si hay un usuario visible
                        auth_part_display = f"{auth_part_display}://{user_maybe}:******"
                    else: # Solo muestra el esquema
                        auth_part_display = f"{auth_part_display}://******"

                    print(f"INFO config.py: SQLALCHEMY_DATABASE_URI establecida a: {auth_part_display}@{uri_parts_at[1]}")
                else:
                    print(f"INFO config.py: SQLALCHEMY_DATABASE_URI establecida a: {SQLALCHEMY_DATABASE_URI} (No se pudo aplicar ocultamiento de contraseña estándar)")
        except Exception as e:
            print(f"INFO config.py: SQLALCHEMY_DATABASE_URI establecida a: {SQLALCHEMY_DATABASE_URI} (Error al intentar ocultar contraseña: {e})")
    else:
        print("ERROR config.py: SQLALCHEMY_DATABASE_URI no pudo ser establecida.")