# migrations/env.py
import logging
from logging.config import fileConfig
import os
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- Importa tu clase Config y tu instancia db directamente ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from config import Config as AppFlaskConfig # Importa tu clase Config desde config.py
    # Si tu 'db' se define en app.py:
    # from app import db as sqlalchemy_db_instance # <--- ESTA LÍNEA COMENTADA O ELIMINADA
    # Si 'db' se define en models.py:
    from models import db as sqlalchemy_db_instance # <--- ESTA LÍNEA ACTIVA (SIN EL # AL INICIO)
except ImportError as e:
    print(f"ERROR en env.py: No se pudo importar 'config' o 'models'. Verifica las rutas y nombres.")
    print(f"PROJECT_ROOT actual: {PROJECT_ROOT}") # Asumiendo que PROJECT_ROOT está definido arriba
    print(f"sys.path actual: {sys.path}") # Asumiendo que sys está importado y sys.path modificado
    raise e

# --- Configuración de Alembic ---
config = context.config 

if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# --- URL de la Base de Datos y Metadatos ---
db_url_for_alembic = AppFlaskConfig.SQLALCHEMY_DATABASE_URI # Usa la URI de la clase Config importada
if not db_url_for_alembic:
    raise Exception("SQLALCHEMY_DATABASE_URI no pudo ser determinada desde AppFlaskConfig en config.py.")

print(f"DEBUG migrations/env.py: URL de AppFlaskConfig para Alembic: {db_url_for_alembic.split('@')[0] if db_url_for_alembic else 'None'}:<PASSWORD_HIDDEN>@{db_url_for_alembic.split('@')[1] if db_url_for_alembic and '@' in db_url_for_alembic else ''}")
config.set_main_option('sqlalchemy.url', db_url_for_alembic)

target_metadata_obj = sqlalchemy_db_instance.metadata
# --- Fin Configuración ---

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata_obj, literal_binds=True, dialect_opts={}
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    # CORRECCIÓN: config.config_ini_section (sin paréntesis al final)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section), # <--- CORREGIDO AQUÍ
        prefix="sqlalchemy.", poolclass=pool.NullPool
    )
    with connectable.connect() as connection:
        conf_args = {}
        try:
            from flask import current_app
            if current_app and 'migrate' in current_app.extensions:
                conf_args = current_app.extensions['migrate'].configure_args
                def process_revision_directives(context, revision, directives):
                    if getattr(config.cmd_opts, 'autogenerate', False):
                        script = directives[0]
                        if script.upgrade_ops.is_empty():
                            directives[:] = []
                            logger.info('No se detectaron cambios en el esquema.')
                if conf_args.get("process_revision_directives") is None:
                    conf_args["process_revision_directives"] = process_revision_directives
        except Exception:
            logger.warning("No se pudo obtener configure_args de Flask-Migrate.")
        
        if "compare_type" not in conf_args: conf_args["compare_type"] = True
        if "compare_server_default" not in conf_args: conf_args["compare_server_default"] = True
            
        context.configure(connection=connection, target_metadata=target_metadata_obj, **conf_args)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()