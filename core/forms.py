from django import forms
from .models import AreaMunicipal

# -----------------------------------------------------------------------------
# WIDGETS Y CAMPOS PERSONALIZADOS (Para subir múltiples archivos)
# -----------------------------------------------------------------------------
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

# -----------------------------------------------------------------------------
# FORMULARIO DE SUBIDA (Con lógica inteligente de áreas)
# -----------------------------------------------------------------------------
class UploadFileForm(forms.Form):
    area_destino = forms.ModelChoiceField(
        queryset=AreaMunicipal.objects.none(),
        label="Selecciona el Área de Destino",
        required=True, 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    archivo = MultipleFileField(
        label="Selecciona uno o más archivos",
        widget=MultipleFileInput(attrs={
            'id': 'fileElem', 
            'onchange': 'handleFiles(this.files)'
        })
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(UploadFileForm, self).__init__(*args, **kwargs)
        
        if user and hasattr(user, 'perfilusuario'):
            mis_areas = user.perfilusuario.areas.all()
            self.fields['area_destino'].queryset = mis_areas

            # --- LÓGICA INTELIGENTE ---
            if mis_areas.count() == 1:
                # Si solo tiene 1 área, la pre-seleccionamos y ocultamos el campo
                self.fields['area_destino'].initial = mis_areas.first()
                self.fields['area_destino'].widget = forms.HiddenInput()
            else:
                # Si tiene varias, obligamos a elegir
                self.fields['area_destino'].empty_label = "--- Selecciona un Área ---"

# -----------------------------------------------------------------------------
# FORMULARIO DE LOGIN (Este era el que faltaba)
# -----------------------------------------------------------------------------
class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuario'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )