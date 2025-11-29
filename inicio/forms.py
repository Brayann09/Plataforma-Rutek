from django import forms
from .models import Conductor, Vehiculo, Servicio


class ConductorForm(forms.ModelForm):
    class Meta:
        model = Conductor
        fields = [
            'nombre_completo',
            'tipo_documento',
            'numero_documento',
            'telefono',
            'correo',
            'licencia_categoria',
            'licencia_numero',
            'licencia_vencimiento',
            'activo',
        ]
        widgets = {
            'licencia_vencimiento': forms.DateInput(attrs={'type': 'date'}),
        }


class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = [
            'placa',
            'marca',
            'linea',
            'modelo',
            'capacidad_pasajeros',
            'soat_vencimiento',
            'tecnomecanica_vencimiento',
            'poliza_contractual_vencimiento',
            'poliza_extracontractual_vencimiento',
            'activo',
        ]
        widgets = {
            'soat_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'tecnomecanica_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'poliza_contractual_vencimiento': forms.DateInput(attrs={'type': 'date'}),
            'poliza_extracontractual_vencimiento': forms.DateInput(attrs={'type': 'date'}),
        }


class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = [
            'conductor',
            'vehiculo',
            'fecha_servicio',
            'hora_inicio',
            'hora_fin',
            'origen',
            'destino',
            'tipo_servicio',
            'cliente_nombre',
            'cliente_contacto',
            'valor',
            'estado',
        ]
        widgets = {
            'fecha_servicio': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
        }

