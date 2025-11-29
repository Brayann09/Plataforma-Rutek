from django.contrib import admin
from .models import Empresa, EmpresaUsuario, CodigoVerificacion, Conductor, Vehiculo, Servicio



@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nit", "email")
    search_fields = ("nombre", "nit")


@admin.register(EmpresaUsuario)
class EmpresaUsuarioAdmin(admin.ModelAdmin):
    list_display = ("user", "empresa", "es_admin_empresa")
    list_filter = ("empresa", "es_admin_empresa")
    search_fields = ("user__username", "empresa__nombre")


@admin.register(CodigoVerificacion)
class CodigoVerificacionAdmin(admin.ModelAdmin):
    list_display = ("user", "codigo", "creado", "usado")
    list_filter = ("usado", "creado")
    search_fields = ("user__username", "codigo")


@admin.register(Conductor)
class ConductorAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_completo",
        "numero_documento",
        "telefono",
        "licencia_categoria",
        "licencia_vencimiento",
        "activo",
        "empresa",
    )
    search_fields = ("nombre_completo", "numero_documento", "telefono")
    list_filter = ("activo", "licencia_categoria", "licencia_vencimiento", "empresa")


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_servicio",
        "origen",
        "destino",
        "conductor",
        "vehiculo",
        "estado",
        "valor",
        "empresa",
    )
    list_filter = ("empresa", "estado", "fecha_servicio")
    search_fields = ("origen", "destino", "cliente_nombre", "conductor__nombre_completo", "vehiculo__placa")

