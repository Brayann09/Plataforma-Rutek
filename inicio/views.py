from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.conf import settings

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string, get_template
from django.utils.html import strip_tags
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from datetime import datetime, date, timedelta
import random
from io import BytesIO

from django.db.models import Q  # para búsquedas

from xhtml2pdf import pisa

from .models import (
    CodigoVerificacion,
    Empresa,
    EmpresaUsuario,
    Conductor,
    Vehiculo,
    Servicio,
)
from .forms import ConductorForm, VehiculoForm, ServicioForm


# =====================================================
#  HELPER: OBTENER EMPRESA ACTUAL
# =====================================================

def obtener_empresa_actual(user):
    """
    Devuelve la empresa asociada al usuario.
    Si el usuario no tiene EmpresaUsuario (ej: superuser admin),
    devuelve/crea la empresa por defecto 'Rutek Tours'.
    """
    empresa_vinculo = getattr(user, 'empresa_vinculo', None)
    if empresa_vinculo:
        return empresa_vinculo.empresa

    empresa_rutek, _ = Empresa.objects.get_or_create(
        nombre='Rutek Tours',
        defaults={
            'nit': '901000000-0',
            'direccion': 'Bogotá, Colombia',
            'telefono': '3000000000',
            'email': 'contacto@rutek.tours',
        }
    )
    return empresa_rutek


# =====================================================
#  HELPER: OBTENER ALERTAS DE VENCIMIENTO
# =====================================================

def obtener_alertas_vencimiento(empresa, dias_alerta=30):
    """
    Devuelve una lista de dicts con alertas de:
    - Licencias de conductores
    - SOAT / Tecnomecánica / Pólizas de vehículos

    Solo se incluyen los que:
    - Ya están vencidos, o
    - Vencen en los próximos 'dias_alerta' días
    """
    hoy = date.today()
    limite = hoy + timedelta(days=dias_alerta)
    alertas = []

    # --- Conductores: licencia de conducción ---
    conductores = Conductor.objects.filter(
        empresa=empresa,
        licencia_vencimiento__isnull=False,
        licencia_vencimiento__lte=limite,
    )

    for c in conductores:
        dias = (c.licencia_vencimiento - hoy).days
        estado = 'VENCIDO' if dias < 0 else 'POR_VENCER'
        dias_texto = abs(dias)  # siempre en positivo para mostrar en tabla

        alertas.append({
            'origen': 'CONDUCTOR',
            'tipo': 'Licencia de conducción',
            'nombre': c.nombre_completo,
            'identificacion': c.numero_documento,
            'fecha': c.licencia_vencimiento,
            'dias_restantes': dias,   # puede ser negativo
            'dias_texto': dias_texto, # siempre positivo
            'estado_alerta': estado,
        })

    # --- Vehículos: SOAT, Tecnomecánica, Pólizas ---
    vehiculos = Vehiculo.objects.filter(empresa=empresa)
    campos_vehiculo = [
        ('SOAT', 'soat_vencimiento'),
        ('Tecnomecánica', 'tecnomecanica_vencimiento'),
        ('Póliza contractual', 'poliza_contractual_vencimiento'),
        ('Póliza extracontractual', 'poliza_extracontractual_vencimiento'),
    ]

    for v in vehiculos:
        for tipo, campo in campos_vehiculo:
            fecha = getattr(v, campo)
            if fecha and fecha <= limite:
                dias = (fecha - hoy).days
                estado = 'VENCIDO' if dias < 0 else 'POR_VENCER'
                dias_texto = abs(dias)

                alertas.append({
                    'origen': 'VEHICULO',
                    'tipo': tipo,
                    'placa': v.placa,
                    'descripcion': f'{v.marca} {v.linea}',
                    'fecha': fecha,
                    'dias_restantes': dias,
                    'dias_texto': dias_texto,
                    'estado_alerta': estado,
                })

    # Ordenamos por fecha de vencimiento
    alertas.sort(key=lambda a: a['fecha'])
    return alertas


# =====================================================
#  HELPER: RENDERIZAR HTML → PDF (xhtml2pdf)
# =====================================================

def render_to_pdf(template_src, context_dict=None):
    """
    Renderiza una plantilla HTML a PDF usando xhtml2pdf.
    Devuelve los bytes del PDF o None si hubo error.
    """
    if context_dict is None:
        context_dict = {}
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.CreatePDF(html, dest=result, encoding='UTF-8')
    if pdf.err:
        return None
    return result.getvalue()


# =====================================================
#  PÁGINA DE INICIO
# =====================================================

def home(request):
    """Landing / página de inicio."""
    return render(request, 'index.html')


# =====================================================
#  DASHBOARD
# =====================================================

@login_required
def dashboard_view(request):
    """
    Panel principal después de iniciar sesión.
    Muestra info básica del usuario y su empresa.
    """
    empresa = obtener_empresa_actual(request.user)

    # Conductores activos
    conductores_activos = Conductor.objects.filter(
        empresa=empresa,
        activo=True
    ).count()

    # Vehículos activos
    vehiculos_activos = Vehiculo.objects.filter(
        empresa=empresa,
        activo=True
    ).count()

    # Servicios programados para HOY (excepto cancelados)
    hoy = datetime.today().date()
    servicios_hoy = Servicio.objects.filter(
        empresa=empresa,
        fecha_servicio=hoy
    ).exclude(estado='CANCELADO').count()

    # Alertas de vencimiento (próximos 30 días)
    alertas = obtener_alertas_vencimiento(empresa, dias_alerta=30)

    # Para el dashboard solo mostramos las primeras 5 como texto
    alertas_dashboard = []
    for a in alertas[:5]:
        if a['dias_restantes'] < 0:
            msg_dias = f"vencido hace {abs(a['dias_restantes'])} días"
        elif a['dias_restantes'] == 0:
            msg_dias = "vence hoy"
        else:
            msg_dias = f"vence en {a['dias_restantes']} días"

        if a['origen'] == 'CONDUCTOR':
            texto = (
                f"Licencia de {a['nombre']} (doc. {a['identificacion']}) "
                f"{msg_dias}."
            )
        else:
            texto = (
                f"{a['tipo']} del vehículo {a['placa']} "
                f"{msg_dias}."
            )

        alertas_dashboard.append(texto)

    context = {
        'usuario': request.user,
        'empresa': empresa,
        'conductores_activos': conductores_activos,
        'vehiculos_activos': vehiculos_activos,
        'servicios_hoy': servicios_hoy,
        'alertas_vencimiento': alertas_dashboard,
    }
    return render(request, 'dashboard.html', context)


# =====================================================
#  VENCIMIENTOS – LISTA DETALLADA
# =====================================================

@login_required
def vencimientos_lista(request):
    """
    Pantalla con todas las alertas de vencimiento de la empresa.
    Permite variar el rango de días (por defecto 30).
    """
    empresa = obtener_empresa_actual(request.user)

    dias_param = request.GET.get('dias', '').strip()
    try:
        dias_alerta = int(dias_param) if dias_param else 30
    except ValueError:
        dias_alerta = 30

    alertas = obtener_alertas_vencimiento(empresa, dias_alerta)

    context = {
        'empresa': empresa,
        'alertas': alertas,
        'dias_alerta': dias_alerta,
    }
    return render(request, 'vencimientos/lista.html', context)


# =====================================================
#  MÓDULO CONDUCTORES – LISTA
# =====================================================

@login_required
def conductores_lista(request):
    """
    Lista de conductores de la empresa actual.
    Permite:
    - Buscar por nombre o número de documento (?q=)
    - Filtrar por activos / inactivos (?estado=activos|inactivos)
    """
    empresa = obtener_empresa_actual(request.user)

    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()

    conductores = Conductor.objects.filter(empresa=empresa)

    if q:
        conductores = conductores.filter(
            Q(nombre_completo__icontains=q) |
            Q(numero_documento__icontains=q)
        )

    if estado == 'activos':
        conductores = conductores.filter(activo=True)
    elif estado == 'inactivos':
        conductores = conductores.filter(activo=False)

    context = {
        'empresa': empresa,
        'conductores': conductores,
        'q': q,
        'estado': estado,
    }
    return render(request, 'conductores/lista.html', context)


# =====================================================
#  MÓDULO CONDUCTORES – CREAR
# =====================================================

@login_required
def conductor_crear(request):
    """Crea un nuevo conductor asociado a la empresa actual."""
    empresa = obtener_empresa_actual(request.user)

    if request.method == 'POST':
        form = ConductorForm(request.POST)
        if form.is_valid():
            conductor = form.save(commit=False)
            conductor.empresa = empresa
            conductor.save()
            messages.success(request, "Conductor creado correctamente.")
            return redirect('conductores_lista')
    else:
        form = ConductorForm()

    context = {
        'empresa': empresa,
        'form': form,
        'es_edicion': False,
        'conductor': None,
    }
    return render(request, 'conductores/form.html', context)


# =====================================================
#  MÓDULO CONDUCTORES – EDITAR
# =====================================================

@login_required
def conductor_editar(request, pk):
    """Edita un conductor existente de la empresa actual."""
    empresa = obtener_empresa_actual(request.user)
    conductor = get_object_or_404(Conductor, pk=pk, empresa=empresa)

    if request.method == 'POST':
        form = ConductorForm(request.POST, instance=conductor)
        if form.is_valid():
            form.save()
            messages.success(request, "Conductor actualizado correctamente.")
            return redirect('conductores_lista')
    else:
        form = ConductorForm(instance=conductor)

    context = {
        'empresa': empresa,
        'form': form,
        'es_edicion': True,
        'conductor': conductor,
    }
    return render(request, 'conductores/form.html', context)


# =====================================================
#  MÓDULO CONDUCTORES – DETALLE
# =====================================================

@login_required
def conductor_detalle(request, pk):
    """Muestra el detalle de un conductor de la empresa actual."""
    empresa = obtener_empresa_actual(request.user)
    conductor = get_object_or_404(Conductor, pk=pk, empresa=empresa)

    context = {
        'empresa': empresa,
        'conductor': conductor,
    }
    return render(request, 'conductores/detalle.html', context)


# =====================================================
#  MÓDULO VEHÍCULOS – LISTA
# =====================================================

@login_required
def vehiculos_lista(request):
    """
    Lista de vehículos de la empresa actual.
    Permite:
    - Buscar por placa / marca / línea (?q=)
    - Filtrar por activos / inactivos (?estado=activos|inactivos)
    """
    empresa = obtener_empresa_actual(request.user)

    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()

    vehiculos = Vehiculo.objects.filter(empresa=empresa)

    if q:
        vehiculos = vehiculos.filter(
            Q(placa__icontains=q) |
            Q(marca__icontains=q) |
            Q(linea__icontains=q)
        )

    if estado == 'activos':
        vehiculos = vehiculos.filter(activo=True)
    elif estado == 'inactivos':
        vehiculos = vehiculos.filter(activo=False)

    context = {
        'empresa': empresa,
        'vehiculos': vehiculos,
        'q': q,
        'estado': estado,
    }
    return render(request, 'vehiculos/lista.html', context)


# =====================================================
#  MÓDULO VEHÍCULOS – CREAR
# =====================================================

@login_required
def vehiculo_crear(request):
    """Crea un nuevo vehículo asociado a la empresa actual."""
    empresa = obtener_empresa_actual(request.user)

    if request.method == 'POST':
        form = VehiculoForm(request.POST)
        if form.is_valid():
            vehiculo = form.save(commit=False)
            vehiculo.empresa = empresa
            vehiculo.save()
            messages.success(request, "Vehículo creado correctamente.")
            return redirect('vehiculos_lista')
    else:
        form = VehiculoForm()

    context = {
        'empresa': empresa,
        'form': form,
        'es_edicion': False,
        'vehiculo': None,
    }
    return render(request, 'vehiculos/form.html', context)


# =====================================================
#  MÓDULO VEHÍCULOS – EDITAR
# =====================================================

@login_required
def vehiculo_editar(request, pk):
    """Edita un vehículo existente de la empresa actual."""
    empresa = obtener_empresa_actual(request.user)
    vehiculo = get_object_or_404(Vehiculo, pk=pk, empresa=empresa)

    if request.method == 'POST':
        form = VehiculoForm(request.POST, instance=vehiculo)
        if form.is_valid():
            form.save()
            messages.success(request, "Vehículo actualizado correctamente.")
            return redirect('vehiculos_lista')
    else:
        form = VehiculoForm(instance=vehiculo)

    context = {
        'empresa': empresa,
        'form': form,
        'es_edicion': True,
        'vehiculo': vehiculo,
    }
    return render(request, 'vehiculos/form.html', context)


# =====================================================
#  MÓDULO VEHÍCULOS – DETALLE
# =====================================================

@login_required
def vehiculo_detalle(request, pk):
    """Muestra el detalle de un vehículo de la empresa actual."""
    empresa = obtener_empresa_actual(request.user)
    vehiculo = get_object_or_404(Vehiculo, pk=pk, empresa=empresa)

    context = {
        'empresa': empresa,
        'vehiculo': vehiculo,
    }
    return render(request, 'vehiculos/detalle.html', context)


# =====================================================
#  MÓDULO SERVICIOS – LISTA
# =====================================================

@login_required
def servicios_lista(request):
    """
    Lista de servicios de la empresa actual.
    Filtros:
    - rango de fechas
    - conductor
    - vehículo
    - estado
    - texto (origen/destino/cliente)
    """
    empresa = obtener_empresa_actual(request.user)

    servicios = Servicio.objects.filter(empresa=empresa)

    # Filtros
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '').strip()
    desde = request.GET.get('desde', '').strip()
    hasta = request.GET.get('hasta', '').strip()
    conductor_id = request.GET.get('conductor', '').strip()
    vehiculo_id = request.GET.get('vehiculo', '').strip()

    if q:
        servicios = servicios.filter(
            Q(origen__icontains=q) |
            Q(destino__icontains=q) |
            Q(cliente_nombre__icontains=q)
        )

    if estado:
        servicios = servicios.filter(estado=estado)

    if desde:
        servicios = servicios.filter(fecha_servicio__gte=desde)

    if hasta:
        servicios = servicios.filter(fecha_servicio__lte=hasta)

    if conductor_id:
        servicios = servicios.filter(conductor_id=conductor_id)

    if vehiculo_id:
        servicios = servicios.filter(vehiculo_id=vehiculo_id)

    # Para combos de filtro
    conductores = Conductor.objects.filter(empresa=empresa, activo=True)
    vehiculos = Vehiculo.objects.filter(empresa=empresa, activo=True)

    context = {
        'empresa': empresa,
        'servicios': servicios.order_by('-fecha_servicio', '-hora_inicio'),
        'q': q,
        'estado': estado,
        'desde': desde,
        'hasta': hasta,
        'conductor_id': conductor_id,
        'vehiculo_id': vehiculo_id,
        'conductores': conductores,
        'vehiculos': vehiculos,
    }
    return render(request, 'servicios/lista.html', context)


# =====================================================
#  MÓDULO SERVICIOS – CREAR
# =====================================================

@login_required
def servicio_crear(request):
    """Crea un nuevo servicio asociado a la empresa actual."""
    empresa = obtener_empresa_actual(request.user)

    if request.method == 'POST':
        form = ServicioForm(request.POST)
        # limitar queryset a la empresa
        form.fields['conductor'].queryset = Conductor.objects.filter(empresa=empresa, activo=True)
        form.fields['vehiculo'].queryset = Vehiculo.objects.filter(empresa=empresa, activo=True)

        if form.is_valid():
            servicio = form.save(commit=False)
            servicio.empresa = empresa
            servicio.save()
            messages.success(request, "Servicio creado correctamente.")
            return redirect('servicios_lista')
    else:
        form = ServicioForm()
        form.fields['conductor'].queryset = Conductor.objects.filter(empresa=empresa, activo=True)
        form.fields['vehiculo'].queryset = Vehiculo.objects.filter(empresa=empresa, activo=True)

    context = {
        'empresa': empresa,
        'form': form,
        'es_edicion': False,
        'servicio': None,
    }
    return render(request, 'servicios/form.html', context)


# =====================================================
#  MÓDULO SERVICIOS – EDITAR
# =====================================================

@login_required
def servicio_editar(request, pk):
    """Edita un servicio existente de la empresa actual."""
    empresa = obtener_empresa_actual(request.user)
    servicio = get_object_or_404(Servicio, pk=pk, empresa=empresa)

    if request.method == 'POST':
        form = ServicioForm(request.POST, instance=servicio)
        form.fields['conductor'].queryset = Conductor.objects.filter(empresa=empresa, activo=True)
        form.fields['vehiculo'].queryset = Vehiculo.objects.filter(empresa=empresa, activo=True)

        if form.is_valid():
            form.save()
            messages.success(request, "Servicio actualizado correctamente.")
            return redirect('servicios_lista')
    else:
        form = ServicioForm(instance=servicio)
        form.fields['conductor'].queryset = Conductor.objects.filter(empresa=empresa, activo=True)
        form.fields['vehiculo'].queryset = Vehiculo.objects.filter(empresa=empresa, activo=True)

    context = {
        'empresa': empresa,
        'form': form,
        'es_edicion': True,
        'servicio': servicio,
    }
    return render(request, 'servicios/form.html', context)


# =====================================================
#  MÓDULO SERVICIOS – DETALLE
# =====================================================

@login_required
def servicio_detalle(request, pk):
    """Muestra el detalle de un servicio de la empresa actual."""
    empresa = obtener_empresa_actual(request.user)
    servicio = get_object_or_404(Servicio, pk=pk, empresa=empresa)

    context = {
        'empresa': empresa,
        'servicio': servicio,
    }
    return render(request, 'servicios/detalle.html', context)


# =====================================================
#  MÓDULO SERVICIOS – FUEC EN PDF
# =====================================================

@login_required
def servicio_fuec_pdf(request, pk):
    """
    Genera el FUEC en PDF para un servicio específico
    y lo descarga como archivo.
    """
    empresa = obtener_empresa_actual(request.user)
    servicio = get_object_or_404(Servicio, pk=pk, empresa=empresa)

    context = {
        'empresa': empresa,
        'servicio': servicio,
        'hoy': date.today(),
    }

    pdf_bytes = render_to_pdf('servicios/fuec_pdf.html', context)

    if pdf_bytes is None:
        messages.error(request, 'No se pudo generar el PDF del FUEC.')
        return redirect('servicio_detalle', pk=pk)

    filename = f"FUEC_{servicio.id}_{servicio.fecha_servicio}.pdf"

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# =====================================================
#  LOGIN
# =====================================================

def login_view(request):
    """
    Login SIN selector de empresa.
    Permite iniciar sesión usando:
    - Email
    - Username
    """
    if request.method == 'POST':
        email_or_user = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember')

        # Por defecto, asumimos que lo que llega es el username
        username = email_or_user

        # Si coincide con un correo de un usuario, usamos su username real
        user_obj = User.objects.filter(email=email_or_user).first()
        if user_obj:
            username = user_obj.username

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, 'Credenciales inválidas.')
            return render(request, 'login.html')

        if not user.is_active:
            messages.error(request, 'Tu cuenta aún no ha sido verificada.')
            return render(request, 'login.html')

        # Login exitoso
        login(request, user)

        # Recordarme
        if remember:
            request.session.set_expiry(1209600)  # 14 días
        else:
            request.session.set_expiry(0)        # hasta cerrar navegador

        return redirect('dashboard')

    return render(request, 'login.html')


# =====================================================
#  LOGOUT
# =====================================================

def logout_view(request):
    logout(request)
    return redirect('home')


# =====================================================
#  REGISTRO
# =====================================================

def generar_codigo():
    """Genera un código de 6 números, ej: 593028."""
    return ''.join(random.choices('0123456789', k=6))


def registro_view(request):
    """
    Registro:
    - Crea usuario inactivo
    - Lo asocia a la empresa por defecto: Rutek Tours
    - Genera código de verificación
    - Intenta enviar correo HTML.
      Si el correo falla, activa al usuario directamente (modo demo).
    """
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        # Validaciones básicas
        if not nombre or not email or not password or not password2:
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, 'registro.html')

        if password != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'registro.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe una cuenta con este correo.')
            return render(request, 'registro.html')

        # Crear usuario
        user = User.objects.create_user(
            username=email,      # username = correo
            email=email,
            password=password,
            first_name=nombre
        )
        user.is_active = False
        user.save()

        # Asociar a empresa por defecto
        empresa_rutek = obtener_empresa_actual(user)

        # Si la empresa aún no tiene admin, este será el admin
        if empresa_rutek.administrador is None:
            empresa_rutek.administrador = user
            empresa_rutek.save()
            es_admin = True
        else:
            es_admin = False

        EmpresaUsuario.objects.create(
            empresa=empresa_rutek,
            user=user,
            es_admin_empresa=es_admin
        )

        # Crear / actualizar código de verificación
        codigo = generar_codigo()
        CodigoVerificacion.objects.update_or_create(
            user=user,
            defaults={'codigo': codigo, 'usado': False}
        )

        # Enviar correo con plantilla HTML
        asunto = "Código de verificación - Rutek"
        context = {
            'nombre': nombre,
            'codigo': codigo,
            'year': datetime.now().year,
        }

        html_body = render_to_string('email_verificacion.html', context)
        text_body = strip_tags(html_body)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)

        email_message = EmailMultiAlternatives(
            subject=asunto,
            body=text_body,
            from_email=from_email,
            to=[email],
        )
        email_message.attach_alternative(html_body, "text/html")

        try:
            # Puede fallar en Render si hay problemas con Gmail
            email_message.send()

            # Guardar usuario pendiente en sesión SOLO si se envió el correo
            request.session['pending_user_id'] = user.id
            messages.success(request, 'Te enviamos un código de verificación a tu correo.')
            return redirect('verificacion')

        except Exception as e:
            # Se verá en los logs de Render
            print(f"Error enviando correo de verificación: {e}")

            # Activamos al usuario directamente para no bloquear la app (modo demo)
            user.is_active = True
            user.save()

            messages.warning(
                request,
                'Tu usuario se creó correctamente, pero no pudimos enviar el correo de '
                'verificación. Por ser una demo, tu cuenta fue activada automáticamente.'
            )
            return redirect('login')

    return render(request, 'registro.html')


# =====================================================
#  VERIFICACIÓN DE CORREO
# =====================================================

def verificacion_view(request):
    """
    Verifica código:
    - Si coincide → activa cuenta y loguea
    """
    user_id = request.session.get('pending_user_id')
    if not user_id:
        messages.error(request, 'No hay registro pendiente de verificación.')
        return redirect('login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('login')

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo', '').strip()

        try:
            registro_codigo = CodigoVerificacion.objects.get(
                user=user,
                codigo=codigo_ingresado,
                usado=False
            )
        except CodigoVerificacion.DoesNotExist:
            messages.error(request, 'Código incorrecto o ya utilizado.')
            return render(request, 'verificacion.html', {'email': user.email})

        # Marcar código como usado
        registro_codigo.usado = True
        registro_codigo.save()

        # Activar usuario
        user.is_active = True
        user.save()

        # Limpiar sesión
        del request.session['pending_user_id']

        # Login automático
        login(request, user)
        messages.success(request, 'Cuenta verificada correctamente. ¡Bienvenido!')

        return redirect('dashboard')

    return render(request, 'verificacion.html', {'email': user.email})


# =====================================================
#  RECUPERAR CONTRASEÑA – PASO 1 (PEDIR CORREO)
# =====================================================

def password_reset_request(request):
    """
    Paso 1:
    - El usuario ingresa su correo
    - Si existe, se genera un código y se envía por email
    - Se guarda el id del usuario en sesión como 'reset_user_id'
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()

        if not email:
            messages.error(request, 'Debes ingresar un correo electrónico.')
            return render(request, 'password_reset_request.html')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Por seguridad, no revelamos si existe o no
            messages.success(
                request,
                'Si el correo está registrado, te enviaremos un código de recuperación.'
            )
            return redirect('password_reset_request')

        # Reutilizamos generar_codigo + CodigoVerificacion
        codigo = generar_codigo()
        CodigoVerificacion.objects.update_or_create(
            user=user,
            defaults={'codigo': codigo, 'usado': False}
        )

        asunto = "Recuperación de contraseña - Rutek"
        context = {
            'nombre': user.first_name or user.username,
            'codigo': codigo,
            'year': datetime.now().year,
        }

        html_body = render_to_string('email_reset_password.html', context)
        text_body = strip_tags(html_body)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)

        email_message = EmailMultiAlternatives(
            subject=asunto,
            body=text_body,
            from_email=from_email,
            to=[email],
        )
        email_message.attach_alternative(html_body, "text/html")
        email_message.send()

        request.session['reset_user_id'] = user.id

        messages.success(
            request,
            'Te enviamos un código de recuperación a tu correo.'
        )
        return redirect('password_reset_confirm')

    return render(request, 'password_reset_request.html')


# =====================================================
#  RECUPERAR CONTRASEÑA – PASO 2 (CÓDIGO + NUEVA CLAVE)
# =====================================================

def password_reset_confirm(request):
    """
    Paso 2:
    - El usuario ingresa el código recibido y la nueva contraseña
    - Si el código es correcto, se cambia la contraseña
    """
    user_id = request.session.get('reset_user_id')
    if not user_id:
        messages.error(request, 'No hay un proceso de recuperación activo.')
        return redirect('password_reset_request')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('password_reset_request')

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if not codigo_ingresado or not password or not password2:
            messages.error(request, 'Debes completar todos los campos.')
            return render(request, 'password_reset_confirm.html', {'email': user.email})

        if password != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'password_reset_confirm.html', {'email': user.email})

        try:
            registro_codigo = CodigoVerificacion.objects.get(
                user=user,
                codigo=codigo_ingresado,
                usado=False
            )
        except CodigoVerificacion.DoesNotExist:
            messages.error(request, 'Código incorrecto o ya utilizado.')
            return render(request, 'password_reset_confirm.html', {'email': user.email})

        registro_codigo.usado = True
        registro_codigo.save()

        user.set_password(password)
        user.save()

        del request.session['reset_user_id']

        messages.success(request, 'Tu contraseña se ha actualizado correctamente. Ahora puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'password_reset_confirm.html', {'email': user.email})

