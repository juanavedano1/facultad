# C:\Users\Juan Avedano\Desktop\Facultad\Proyecto\customer_dashboard\views.py

from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, Response
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import os
from models import db, User, Service
from forms import ContractServiceForm, ModifyServiceForm, ChangePasswordForm
from io import BytesIO
from fpdf import FPDF


# Define tu Blueprint. Ajusta el template_folder para que apunte a 'templates/customer_dashboard'
# La ruta es relativa a la ubicación del app.py
customer_dashboard_bp = Blueprint('customer_dashboard', __name__, template_folder='../templates/customer_dashboard') # <-- CAMBIO CLAVE AQUI
# NOTA: '../../' significa que sube dos niveles desde views.py (customer_dashboard -> Proyecto) y luego entra a templates/customer_dashboard

# Pega esta función en customer_dashboard/views.py
# Reemplaza cualquier versión anterior de download_invoice

@customer_dashboard_bp.route('/invoice/download')
@login_required
def download_invoice():
    # 1. Obtener datos del usuario y sus servicios (esta parte es similar)
    user_obj = None
    user_services = []

    if current_app.config.get('SIMULATION_MODE', False):
        # --- DATOS DE SIMULACIÓN (SI USAS SIMULATION_MODE) ---
        user_services_data = [
            {'name': 'Internet Fibra Óptica 300Mbps', 'description': 'Alta velocidad simulada', 'price': 35000.00},
            {'name': 'TV Cable Premium', 'description': 'Full HD simulada', 'price': 25000.00},
        ]
        class MockService: # Objeto simple para simular un servicio
            def __init__(self, name, description, price):
                self.name = name
                self.description = description
                self.price = price
        user_services = [MockService(**s) for s in user_services_data]

        user_mock_attrs = { # Atributos simulados para el usuario
            'username': current_user.username if hasattr(current_user, 'username') else 'ClienteDemo',
            'email': current_user.email if hasattr(current_user, 'email') else 'cliente.demo@example.com',
            'id': current_user.id if hasattr(current_user, 'id') else 101 
        }
        user_obj = type('User', (object,), user_mock_attrs)() # Crea un objeto usuario simulado
        # --- FIN DATOS DE SIMULACIÓN ---
    else: # Modo NO simulación (base de datos real)
        if not hasattr(current_user, 'services_contracted'):
            flash('Error: No se pueden obtener los servicios del usuario.', 'danger')
            return redirect(url_for('customer_dashboard.index'))

        user_services = current_user.services_contracted.all()
        user_obj = current_user # El usuario logueado

    if not user_services and not current_app.config.get('SIMULATION_MODE', False):
        flash('No tienes servicios contratados actualmente para generar una factura.', 'warning')
        return redirect(url_for('customer_dashboard.index'))

    # --- Cálculos y detalles de la factura (personaliza según necesites) ---
    total_amount = sum(service.price for service in user_services)
    invoice_details = {
        'number': f"INV-{datetime.now().strftime('%Y%m%d')}-{user_obj.id}",
        'date': datetime.now().strftime('%Y-%m-%d'),
        'due_date': (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d') # Ejemplo
    }
    company_details = { # <<--- ¡PERSONALIZA ESTOS DATOS!
        'name': 'Customer Portal Telecom S.A.',
        'address_line1': 'Av. Siempreviva 742',
        'address_line2': 'Springfield, CP 12345, País',
        'phone': '+00 123 456 7890',
        'email': 'facturacion@tuportal.com',
        'cuit': 'CUIT: 30-12345678-9' # Ejemplo de CUIT
    }
    # --- FIN Cálculos y detalles ---

    # ==============================================
    # === INICIO DE GENERACIÓN DE PDF CON FPDF2 ===
    # ==============================================
    pdf = FPDF(orientation='P', unit='mm', format='A4') # P: Portrait, mm: milímetros, A4
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15) # Margen inferior para evitar cortes

    # --- Márgenes Generales ---
    page_width = pdf.w - 20 # Ancho de página menos márgenes (10mm de cada lado)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.set_top_margin(10)

    # --- Sección 1: Logo y Título "FACTURA" ---
    logo_filename = 'custom.png' # <<--- VERIFICA EL NOMBRE DE TU LOGO
    logo_path_local = os.path.join(current_app.root_path, 'static', 'imgs', logo_filename)

    if os.path.exists(logo_path_local):
        pdf.image(logo_path_local, x=10, y=12, w=45) # Ajusta x,y,w según tu logo

    pdf.set_font('Arial', 'B', 24) # Fuente para el título "FACTURA"
    pdf.set_xy(page_width - 70, 15) # Posiciona el título a la derecha
    pdf.cell(70, 10, 'FACTURA', 0, 1, 'R')

    pdf.set_font('Arial', '', 9) # Fuente más pequeña para los detalles de la factura
    pdf.set_xy(page_width - 70, pdf.get_y())
    pdf.cell(70, 5, f"Nro: {invoice_details['number']}", 0, 1, 'R')
    pdf.set_xy(page_width - 70, pdf.get_y())
    pdf.cell(70, 5, f"Emisión: {invoice_details['date']}", 0, 1, 'R')
    pdf.set_xy(page_width - 70, pdf.get_y())
    pdf.cell(70, 5, f"Vencimiento: {invoice_details['due_date']}", 0, 1, 'R')

    pdf.ln(15) # Espacio después del encabezado

    # --- Sección 2: Datos de la Empresa y Cliente ---
    current_y_info = pdf.get_y()
    col_width_info = page_width / 2 - 5 # Ancho para cada columna de info (Empresa/Cliente)

    # Datos Empresa (Izquierda)
    pdf.set_font('Arial', 'B', 10)
    pdf.multi_cell(col_width_info, 5, company_details['name'], 0, 'L')
    pdf.set_font('Arial', '', 9)
    pdf.set_x(10) # Vuelve al margen izquierdo
    pdf.multi_cell(col_width_info, 5, f"{company_details['address_line1']}\n{company_details['address_line2']}", 0, 'L')
    pdf.set_x(10)
    pdf.multi_cell(col_width_info, 5, f"Tel: {company_details['phone']}", 0, 'L')
    if company_details.get('email'):
        pdf.set_x(10)
        pdf.multi_cell(col_width_info, 5, f"Email: {company_details['email']}", 0, 'L')
    if company_details.get('cuit'):
        pdf.set_x(10)
        pdf.multi_cell(col_width_info, 5, company_details['cuit'], 0, 'L')

    # Datos Cliente (Derecha)
    pdf.set_y(current_y_info) # Vuelve a la Y inicial de esta sección
    pdf.set_x(10 + col_width_info + 10) # Posiciona a la derecha
    pdf.set_font('Arial', 'B', 10)
    pdf.multi_cell(col_width_info, 5, "Facturado a:", 0, 'L')
    pdf.set_x(10 + col_width_info + 10)
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(col_width_info, 5, user_obj.username, 0, 'L')
    pdf.set_x(10 + col_width_info + 10)
    pdf.multi_cell(col_width_info, 5, user_obj.email, 0, 'L')
    # Aquí podrías agregar más datos del cliente si los tuvieras

    pdf.ln(10) # Espacio después de la info

    # --- Sección 3: Tabla de Servicios ---
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(220, 220, 220) # Gris claro para encabezado de tabla
    line_height_table = 7

    # Encabezados de la tabla
    pdf.cell(page_width * 0.7, line_height_table, 'Descripción del Servicio', 1, 0, 'C', True) # 70% del ancho
    pdf.cell(page_width * 0.3, line_height_table, 'Precio', 1, 1, 'C', True)       # 30% del ancho, con salto de línea

    pdf.set_font('Arial', '', 9)
    pdf.set_fill_color(255, 255, 255) # Blanco para las celdas de datos
    if user_services:
        for service in user_services:
            # Guardar Y actual antes de multi_cell para la descripción
            y_before_desc = pdf.get_y()
            pdf.multi_cell(page_width * 0.7, line_height_table, f"{service.name}\n{service.description}", 1, 'L', True)
            y_after_desc = pdf.get_y()
            height_of_desc_cell = y_after_desc - y_before_desc

            # Celda de precio (debe tener la misma altura que la celda de descripción)
            pdf.set_xy(10 + (page_width * 0.7), y_before_desc) # Posicionar al inicio de la celda de precio
            pdf.cell(page_width * 0.3, height_of_desc_cell, f"${service.price:,.2f}", 1, 1, 'R', True)
    else:
        pdf.cell(page_width, line_height_table, 'No hay servicios contratados.', 1, 1, 'C', True)

    pdf.ln(1) # Pequeño espacio antes del total

    # --- Sección 4: Total ---
    pdf.set_font('Arial', 'B', 11)
    total_label_width = page_width * 0.7 # Ancho para la etiqueta "TOTAL"
    total_value_width = page_width * 0.3 # Ancho para el valor del total

    pdf.set_x(10 + total_label_width) # Alinear a la derecha
    pdf.cell(total_value_width, 8, f"TOTAL: ${total_amount:,.2f}", 1, 1, 'R')

    pdf.ln(10) # Espacio

    # --- Sección 5: Pie de página simple ---
    pdf.set_font('Arial', 'I', 8) # Fuente itálica y pequeña
    pdf.cell(0, 10, 'Gracias por utilizar nuestros servicios.', 0, 1, 'C')
    # ============================================
    # === FIN DE GENERACIÓN DE PDF CON FPDF2 ===
    # ============================================

    # --- Preparar la respuesta para descargar el PDF ---
    pdf_output_bytes_io = BytesIO() # Crear un buffer en memoria
    pdf.output(pdf_output_bytes_io, 'F') # Escribir el PDF en el buffer
    pdf_output_bytes = pdf_output_bytes_io.getvalue() # Obtener los bytes del PDF
    pdf_output_bytes_io.close() # Cerrar el buffer

    response = Response(pdf_output_bytes, mimetype='application/pdf')
    download_filename = f"factura_{user_obj.username}_{invoice_details['date']}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename="{download_filename}"'

    return response

# ... (Aquí pueden ir el resto de tus rutas del customer_dashboard_bp)

@customer_dashboard_bp.route('/')
@customer_dashboard_bp.route('/index')
@login_required
def index():
    user_services = []
    if not current_app.config.get('SIMULATION_MODE', False):
        if hasattr(current_user, 'services_contracted'):
            user_services = current_user.services_contracted.all()

    # CAMBIO DE NOMBRE DE LA PLANTILLA:
    return render_template('dashboard_index.html', user_services=user_services, active_tab='dashboard')


# --- RUTA: Ver Perfil/Datos del Usuario ---
@customer_dashboard_bp.route('/profile')
@login_required
def view_profile():
    user_data = current_user
    user_services = []

    if current_app.config.get('SIMULATION_MODE', False):
        # Mock de datos para la vista de perfil en simulación
        if user_data.id == '2':
            user_data = type('User', (object,), {
                'id': '2', 'username': 'cliente', 'email': 'cliente@example.com',
                'registration_date': datetime(2023, 2, 15, 12, 0, 0),
                'last_login': datetime.now(),
                'is_active': True,
                'is_admin': False,
                'get_id': lambda: '2', 'is_authenticated': True, 'is_active': True, 'is_anonymous': False
            })()
            user_services = [
                {'name': 'Internet Fibra Óptica', 'type': 'Internet', 'price': 35000.00, 'description': 'Conexión de alta velocidad'},
                {'name': 'Telefonía Móvil', 'type': 'Móvil', 'price': 20000.00, 'description': 'Plan con 10GB de datos'},
            ]
        elif user_data.id == '1':
            user_data = type('User', (object,), {
                'id': '1', 'username': 'admin', 'email': 'admin@example.com',
                'registration_date': datetime(2023, 1, 1, 10, 0, 0),
                'last_login': datetime.now(),
                'is_active': True,
                'is_admin': True,
                'get_id': lambda: '1', 'is_authenticated': True, 'is_active': True, 'is_anonymous': False
            })()
            user_services = []

    else:
        if hasattr(current_user, 'services_contracted'):
            user_services = current_user.services_contracted.all()

    # La plantilla 'profile.html' está directamente dentro de 'templates/customer_dashboard'
    return render_template('profile.html', user=user_data, user_services=user_services, active_tab='profile')


# --- RUTA: Cambiar Contraseña ---
@customer_dashboard_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_app.config.get('SIMULATION_MODE', False):
            flash('El cambio de contraseña no está disponible en modo simulación.', 'warning')
            return redirect(url_for('customer_dashboard.change_password'))
        else:
            # Esta línea ya no dará AttributeError una vez que models.py esté actualizado
            if not current_user.check_password(form.old_password.data):
                flash('La contraseña actual es incorrecta.', 'danger')
                return render_template('change_password.html', form=form, active_tab='change_password')

            # Esta línea ya no dará AttributeError una vez que models.py esté actualizado
            current_user.set_password(form.new_password.data) # Usa el método para hashear y guardar
            db.session.commit()
            flash('Tu contraseña ha sido actualizada exitosamente.', 'success')
            return redirect(url_for('customer_dashboard.view_profile'))
    return render_template('change_password.html', form=form, active_tab='change_password')


# --- RUTA PARA CONTRATAR SERVICIOS ---
@customer_dashboard_bp.route('/contract_service', methods=['GET', 'POST'])
@login_required
def customer_contract_service():
    form = ContractServiceForm()

    available_services = Service.query.all()
    form.services.choices = [(service.id, f"{service.name} (${service.price:,.2f})") for service in available_services]

    if form.validate_on_submit():
        selected_service_ids = form.services.data

        for service_id in selected_service_ids:
            service = Service.query.get(service_id)
            if service and service not in current_user.services_contracted:
                current_user.services_contracted.append(service)

        db.session.commit()
        flash('Servicios contratados exitosamente!', 'success')
        return redirect(url_for('customer_dashboard.index'))

    # La plantilla 'contract_service.html' está directamente dentro de 'templates/customer_dashboard'
    return render_template('contract_service.html', form=form, active_tab='contract_service')

# --- RUTA: Gestión de Servicios (donde se listan para modificar) ---
@customer_dashboard_bp.route('/service_management')
@login_required
def service_management():
    user_services = current_user.services_contracted.all()
    # La plantilla 'service_management.html' está directamente dentro de 'templates/customer_dashboard'
    return render_template('service_management.html', user_services=user_services, active_tab='service_management')


# --- RUTA: Modificar un Servicio Específico ---
@customer_dashboard_bp.route('/services/modify/<int:service_id>', methods=['GET', 'POST'])
@login_required
def modify_service(service_id):
    service_to_modify = Service.query.get_or_404(service_id)

    if service_to_modify not in current_user.services_contracted:
        flash('No tienes permiso para modificar este servicio.', 'danger')
        return redirect(url_for('customer_dashboard.service_management'))

    form = ModifyServiceForm()

    available_plans = [
        (service.id, f"{service.name} (${service.price:,.2f})")
        for service in Service.query.filter_by(type=service_to_modify.type).all()
    ]
    form.plan.choices = available_plans

    if form.validate_on_submit():
        new_plan_service_id = form.plan.data
        new_plan_service = Service.query.get(new_plan_service_id)

        if new_plan_service:
            if new_plan_service.id != service_to_modify.id:
                current_user.services_contracted.remove(service_to_modify)
                current_user.services_contracted.append(new_plan_service)

                db.session.commit()
                flash(f'Tu servicio "{service_to_modify.name}" ha sido actualizado a "{new_plan_service.name}" exitosamente!', 'success')
            else:
                flash('No se realizaron cambios porque el plan seleccionado es el mismo que ya tienes.', 'info')
        else:
            flash('El plan de servicio seleccionado no es válido.', 'danger')

        return redirect(url_for('customer_dashboard.service_management'))

    elif request.method == 'GET':
        form.plan.data = service_to_modify.id

    # La plantilla 'modify_service.html' está directamente dentro de 'templates/customer_dashboard'
    return render_template('modify_service.html',
                            form=form,
                            service=service_to_modify,
                            active_tab='service_management')


@customer_dashboard_bp.route('/services/unsubscribe/<int:service_id>', methods=['POST'])
@login_required
def unsubscribe_service(service_id):
    service_to_unsubscribe = Service.query.get_or_404(service_id)

    if service_to_unsubscribe not in current_user.services_contracted:
        flash('No tienes permiso para dar de baja este servicio o no está contratado por ti.', 'danger')
        return redirect(url_for('customer_dashboard.service_management'))

    try:
        current_user.services_contracted.remove(service_to_unsubscribe)
        db.session.commit()

        flash(f'El servicio "{service_to_unsubscribe.name}" ha sido dado de baja exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocurrió un error al intentar dar de baja el servicio: {e}', 'danger')

    return redirect(url_for('customer_dashboard.service_management'))