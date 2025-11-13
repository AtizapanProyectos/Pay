# views.py (VERSIÓN MULTI-ÁREA)

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.http import HttpResponseForbidden

from .models import Archivo, PerfilUsuario
from .forms import UploadFileForm, LoginForm
from . import google_drive_service 

@login_required
def dashboard(request):
    """
    Muestra el panel principal con múltiples áreas y gestiona subidas.
    """
    try:
        perfil = request.user.perfilusuario
        user_areas = perfil.areas.all() # Obtenemos TODAS las áreas del usuario
    except PerfilUsuario.DoesNotExist:
        logout(request)
        return redirect('login')

    if not user_areas.exists():
        # Manejo de caso borde: usuario sin áreas asignadas
        return render(request, 'core/dashboard.html', {
            'error_msg': 'No tienes áreas asignadas. Contacta al administrador.',
            'dashboard_data': []
        })

    if request.method == 'POST':
        # Pasamos el 'user' al form para que valide que el área elegida es permitida
        form = UploadFileForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            area_seleccionada = form.cleaned_data['area_destino']
            archivos_subidos = request.FILES.getlist('archivo')

            for archivo_subido in archivos_subidos:
                nombre_original, _ = os.path.splitext(archivo_subido.name)
                slug_potencial = slugify(nombre_original)
                
                # Verificamos duplicados en esa área específica
                if Archivo.objects.filter(area=area_seleccionada, slug=slug_potencial).exists():
                    slug_potencial = f"{slug_potencial}-{get_random_string(4)}"

                try:
                    # Subida a Drive usando el slug del área seleccionada
                    drive_data = google_drive_service.upload_file_to_drive(
                        file_obj=archivo_subido, 
                        area_slug=area_seleccionada.slug
                    )
                    
                    Archivo.objects.create(
                        nombre_personalizado=nombre_original,
                        slug=slug_potencial,
                        area=area_seleccionada, # Asignamos al área elegida
                        subido_por=request.user,
                        google_drive_link=drive_data['link'],
                        google_drive_file_id=drive_data['id']
                    )
                except Exception as e:
                    print(f"Error al subir '{archivo_subido.name}': {e}")
                    continue 
            
            return redirect('dashboard')
    else:
        form = UploadFileForm(user=request.user)

    # --- PREPARACIÓN DE DATOS PARA LA VISTA ---
    # Creamos una lista de diccionarios. Cada item tiene el objeto Area y sus archivos.
    dashboard_data = []
    for area in user_areas:
        archivos_area = Archivo.objects.filter(area=area).order_by('-fecha_creacion')
        dashboard_data.append({
            'area_obj': area,
            'archivos': archivos_area
        })
    
    context = {
        'form': form,
        'dashboard_data': dashboard_data, # Lista estructurada
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def delete_file(request, file_id):
    """
    Elimina archivo validando que el usuario pertenezca al área del archivo.
    """
    archivo = get_object_or_404(Archivo, id=file_id)
    
    # SEGURIDAD: Verificar si el área del archivo está entre las áreas del usuario
    if archivo.area not in request.user.perfilusuario.areas.all():
        return HttpResponseForbidden("No tienes permiso para eliminar archivos de esta área.")

    if request.method == 'POST':
        try:
            google_drive_service.delete_file_from_drive(archivo.google_drive_file_id)
            archivo.delete()
        except Exception as e:
            print(f"Error eliminando archivo: {e}")
        
    return redirect('dashboard')

def serve_file(request, area_slug, file_slug):
    """
    Redirección pública (sin cambios de lógica, solo búsqueda).
    """
    archivo = get_object_or_404(Archivo, area__slug=area_slug, slug=file_slug)
    return redirect(archivo.google_drive_link)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect('dashboard')
            else:
                form.add_error(None, "Credenciales incorrectas.")
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')