# models.py (VERSIÓN MODIFICADA)

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

# El modelo AreaMunicipal no cambia
class AreaMunicipal(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Área")
    slug = models.SlugField(max_length=100, unique=True, blank=True, help_text="Se genera automáticamente, para la URL")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

# El modelo PerfilUsuario no cambia
class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    area = models.ForeignKey(AreaMunicipal, on_delete=models.PROTECT, verbose_name="Área Asignada")

    def __str__(self):
        return f"{self.user.username} - {self.area.nombre}"


# --- CAMBIO CLAVE EN EL MODELO Archivo ---

# La función 'ruta_archivo_area' ya no es necesaria, puedes borrarla.

class Archivo(models.Model):
    # Campos originales que conservamos
    nombre_personalizado = models.CharField(max_length=255, verbose_name="Nombre del Archivo")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    area = models.ForeignKey(AreaMunicipal, on_delete=models.CASCADE, verbose_name="Área Propietaria")
    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Subido por")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # --- NUEVOS CAMPOS ---
    # Eliminamos 'archivo = models.FileField(...)'.
    # Añadimos campos para el enlace y el ID de Google Drive.
    google_drive_link = models.URLField(max_length=1024, verbose_name="Link de Google Drive")
    google_drive_file_id = models.CharField(max_length=255, verbose_name="ID del Archivo en Google Drive")

    def save(self, *args, **kwargs):
        if not self.slug:
            # Mantenemos la creación del slug para las URLs internas de la app
            self.slug = slugify(self.nombre_personalizado)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre_personalizado