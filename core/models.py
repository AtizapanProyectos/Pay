# models.py (VERSIÓN MULTI-ÁREA)

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify

class AreaMunicipal(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Área")
    slug = models.SlugField(max_length=100, unique=True, blank=True, help_text="Se genera automáticamente")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # --- CAMBIO: RELACIÓN MANY-TO-MANY ---
    # Esto permite que un usuario tenga múltiples áreas asignadas
    areas = models.ManyToManyField(AreaMunicipal, verbose_name="Áreas Asignadas")

    def __str__(self):
        areas_names = ", ".join([a.nombre for a in self.areas.all()])
        return f"{self.user.username} - [{areas_names}]"

class Archivo(models.Model):
    nombre_personalizado = models.CharField(max_length=255, verbose_name="Nombre del Archivo")
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    
    # El archivo sigue perteneciendo a UNA sola área
    area = models.ForeignKey(AreaMunicipal, on_delete=models.CASCADE, verbose_name="Área Propietaria")
    
    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Subido por")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    google_drive_link = models.URLField(max_length=1024, verbose_name="Link de Google Drive")
    google_drive_file_id = models.CharField(max_length=255, verbose_name="ID del Archivo en Google Drive")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nombre_personalizado)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre_personalizado