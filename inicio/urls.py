from django.urls import path
from . import views

urlpatterns = [
    # Página de inicio
    path('', views.home, name='home'),

    # Página de contacto (formulario que envía correo a soporte)
    path('contacto/', views.contacto, name='contacto'),

    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('verificacion/', views.verificacion_view, name='verificacion'),

    # Recuperar contraseña 
    path(
        'password/olvide/',
        views.password_reset_request,
        name='password_reset_request'
    ),
    path(
        'password/restablecer/',
        views.password_reset_confirm,
        name='password_reset_confirm'
    ),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Conductores
    path('conductores/', views.conductores_lista, name='conductores_lista'),
    path('conductores/nuevo/', views.conductor_crear, name='conductor_crear'),
    path('conductores/<int:pk>/editar/', views.conductor_editar, name='conductor_editar'),
    path('conductores/<int:pk>/', views.conductor_detalle, name='conductor_detalle'),

    # Vehículos
    path('vehiculos/', views.vehiculos_lista, name='vehiculos_lista'),
    path('vehiculos/nuevo/', views.vehiculo_crear, name='vehiculo_crear'),
    path('vehiculos/<int:pk>/editar/', views.vehiculo_editar, name='vehiculo_editar'),
    path('vehiculos/<int:pk>/', views.vehiculo_detalle, name='vehiculo_detalle'),

    # Servicios / Viajes
    path('servicios/', views.servicios_lista, name='servicios_lista'),
    path('servicios/nuevo/', views.servicio_crear, name='servicio_crear'),
    path('servicios/<int:pk>/editar/', views.servicio_editar, name='servicio_editar'),
    path('servicios/<int:pk>/', views.servicio_detalle, name='servicio_detalle'),

    # FUEC en PDF para un servicio
    path(
        'servicios/<int:pk>/fuec/',
        views.servicio_fuec_pdf,
        name='servicio_fuec_pdf'
    ),

    # Vencimientos / Alertas
    path('vencimientos/', views.vencimientos_lista, name='vencimientos_lista'),
]



