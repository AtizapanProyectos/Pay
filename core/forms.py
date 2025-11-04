# link_generator/core/forms.py

from django import forms

# -----------------------------------------------------------------------------
# PASO 1: CREAR UN WIDGET PERSONALIZADO
# -----------------------------------------------------------------------------
# Creamos una clase que le dice a Django que está bien renderizar
# un input con el atributo 'multiple'.
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

# -----------------------------------------------------------------------------
# PASO 2: CREAR UN CAMPO DE FORMULARIO PERSONALIZADO
# -----------------------------------------------------------------------------
# Creamos un campo que sabe cómo recibir y procesar una LISTA de archivos,
# en lugar de solo uno.
class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        # Le decimos que por defecto use nuestro widget personalizado.
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        # Obtenemos la función de limpieza del padre (para un solo archivo)
        single_file_clean = super().clean
        
        # Si 'data' es una lista (varios archivos subidos), limpiamos cada uno.
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        # Si no, simplemente limpiamos el único archivo.
        else:
            result = single_file_clean(data, initial)
        
        return result

# -----------------------------------------------------------------------------
# PASO 3: USAR NUESTRO CAMPO PERSONALIZADO EN EL FORMULARIO
# -----------------------------------------------------------------------------
class UploadFileForm(forms.Form):
    # En lugar de forms.FileField, usamos nuestro MultipleFileField.
    # Este campo ya sabe que debe aceptar múltiples archivos.
    archivo = MultipleFileField(
        label="Selecciona uno o más archivos",
        widget=MultipleFileInput(attrs={
            'id': 'fileElem', # Mantenemos el ID para controlarlo con JS
            'onchange': 'handleFiles(this.files)'
        })
    )

# -----------------------------------------------------------------------------
# La clase LoginForm no cambia
# -----------------------------------------------------------------------------
class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}))