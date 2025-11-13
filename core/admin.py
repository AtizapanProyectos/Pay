from django.contrib import admin
from .models import AreaMunicipal, PerfilUsuario, Archivo

# Configuración para Areas
@admin.register(AreaMunicipal)
class AreaMunicipalAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}

# Configuración para Perfil de Usuario (EL PROBLEMA ESTABA AQUÍ)
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    # No podemos poner 'areas' directamente en list_display porque es ManyToMany
    list_display = ('user', 'obtener_areas')
    
    # Usamos filter_horizontal para que sea fácil seleccionar varias áreas
    filter_horizontal = ('areas',)

    # Función auxiliar para mostrar las áreas en la lista
    def obtener_areas(self, obj):
        return ", ".join([a.nombre for a in obj.areas.all()])
    obtener_areas.short_description = 'Áreas Asignadas'

# Configuración para Archivos
@admin.register(Archivo)
class ArchivoAdmin(admin.ModelAdmin):
    list_display = ('nombre_personalizado', 'area', 'subido_por', 'fecha_creacion')
    list_filter = ('area', 'fecha_creacion')
    search_fields = ('nombre_personalizado',)