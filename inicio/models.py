from django.db import models
from django.contrib.auth.models import User


# =====================================================
#  EMPRESAS
# =====================================================

class Empresa(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    nit = models.CharField(max_length=20, unique=True)
    direccion = models.CharField(max_length=150)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    administrador = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="empresa_admin",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.nombre


class EmpresaUsuario(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='miembros'
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='empresa_vinculo'
    )
    es_admin_empresa = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.user.username} → {self.empresa.nombre}'


# =====================================================
#  CÓDIGO DE VERIFICACIÓN
# =====================================================

class CodigoVerificacion(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='codigo_verificacion'
    )
    codigo = models.CharField(max_length=6)
    creado = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)

    def __str__(self):
        return f"Código de verificación para {self.user.username}"


# =====================================================
#  CONDUCTORES
# =====================================================

class Conductor(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='conductores'
    )

    nombre_completo = models.CharField(max_length=150)

    tipo_documento = models.CharField(
        max_length=5,
        help_text="Ej: CC, CE, TI"
    )
    numero_documento = models.CharField(max_length=20)

    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(blank=True)

    licencia_categoria = models.CharField(max_length=5)  # Ej: C1, C2, C3
    licencia_numero = models.CharField(max_length=20)
    licencia_vencimiento = models.DateField(blank=True, null=True)

    activo = models.BooleanField(default=True)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre_completo


# =====================================================
#  VEHÍCULOS
# =====================================================

class Vehiculo(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='vehiculos'
    )

    placa = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    linea = models.CharField(max_length=50, blank=True)
    modelo = models.PositiveIntegerField()  # año modelo, ej: 2026

    capacidad_pasajeros = models.PositiveIntegerField(default=0)

    soat_vencimiento = models.DateField(blank=True, null=True)
    tecnomecanica_vencimiento = models.DateField(blank=True, null=True)
    poliza_contractual_vencimiento = models.DateField(blank=True, null=True)
    poliza_extracontractual_vencimiento = models.DateField(blank=True, null=True)

    activo = models.BooleanField(default=True)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.linea}"


# =====================================================
#  SERVICIOS / VIAJES
# =====================================================

ESTADOS_SERVICIO = [
    ('PROGRAMADO', 'Programado'),
    ('EN_CURSO', 'En curso'),
    ('FINALIZADO', 'Finalizado'),
    ('CANCELADO', 'Cancelado'),
]


class Servicio(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='servicios'
    )

    # Usamos string para evitar problemas de orden de definición
    conductor = models.ForeignKey(
        'Conductor',
        on_delete=models.PROTECT,
        related_name='servicios'
    )

    vehiculo = models.ForeignKey(
        'Vehiculo',
        on_delete=models.PROTECT,
        related_name='servicios'
    )

    fecha_servicio = models.DateField()
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fin = models.TimeField(blank=True, null=True)

    origen = models.CharField(max_length=150)
    destino = models.CharField(max_length=150)

    tipo_servicio = models.CharField(
        max_length=50,
        blank=True,
        help_text="Ej: escolar, empresarial, turismo…"
    )

    cliente_nombre = models.CharField(max_length=150)
    cliente_contacto = models.CharField(max_length=100, blank=True)

    valor = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_SERVICIO,
        default='PROGRAMADO'
    )

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.fecha_servicio} - {self.origen} → {self.destino} ({self.estado})"




