# views.py (VERSIÓN MODIFICADA)

# --- 1. Importaciones Nativas de Python ---
import os

# --- 2. Importaciones de Django ---
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.utils.crypto import get_random_string

# --- 3. Importaciones de la App Local ---
from .models import Archivo, PerfilUsuario
from .forms import UploadFileForm, LoginForm
# --- NUEVA IMPORTACIÓN ---
from . import google_drive_service # Importamos nuestro nuevo servicio

# -----------------------------------------------------------------------------

@login_required
def dashboard(request):
    """
    Muestra el panel principal, sube archivos a Google Drive y los muestra.
    """
    try:
        area_usuario = request.user.perfilusuario.area
    except PerfilUsuario.DoesNotExist:
        logout(request)
        return redirect('login')

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            for archivo_subido in request.FILES.getlist('archivo'):
                nombre_original, _ = os.path.splitext(archivo_subido.name)
                slug_potencial = slugify(nombre_original)
                
                if Archivo.objects.filter(area=area_usuario, slug=slug_potencial).exists():
                    slug_potencial = f"{slug_potencial}-{get_random_string(4)}"

                # --- CAMBIO: LÓGICA DE SUBIDA A GOOGLE DRIVE ---
                try:
                    # 1. Llamamos a nuestra función para subir el archivo a Drive
                    drive_data = google_drive_service.upload_file_to_drive(
                        file_obj=archivo_subido, 
                        area_slug=area_usuario.slug
                    )
                    
                    # 2. Creamos el objeto Archivo en la BD con los datos de Drive
                    Archivo.objects.create(
                        nombre_personalizado=nombre_original,
                        slug=slug_potencial,
                        area=area_usuario,
                        subido_por=request.user,
                        google_drive_link=drive_data['link'],
                        google_drive_file_id=drive_data['id']
                    )
                except Exception as e:
                    # Aquí podrías añadir un mensaje de error para el usuario
                    print(f"Ocurrió un error al subir el archivo '{archivo_subido.name}': {e}")
                    # Puedes decidir si continuar con los otros archivos o parar
                    continue 
            
            return redirect('dashboard')
    else:
        form = UploadFileForm()

    archivos = Archivo.objects.filter(area=area_usuario).order_by('-fecha_creacion')
    
    context = {
        'form': form,
        'archivos': archivos,
        'area_nombre': area_usuario.nombre
    }
    return render(request, 'core/dashboard.html', context)

# -----------------------------------------------------------------------------

@login_required
def delete_file(request, file_id):
    """
    Elimina el archivo de Google Drive y luego de la base de datos.
    """
    archivo = get_object_or_404(Archivo, id=file_id, area=request.user.perfilusuario.area)
    if request.method == 'POST':
        # --- CAMBIO: ELIMINAR DE GOOGLE DRIVE PRIMERO ---
        google_drive_service.delete_file_from_drive(archivo.google_drive_file_id)
        
        # Luego, eliminar de la base de datos
        archivo.delete()
        
    return redirect('dashboard')

# -----------------------------------------------------------------------------

def serve_file(request, area_slug, file_slug):
    """
    Busca el archivo en la base de datos y redirige al link de Google Drive.
    """
    # --- CAMBIO: LÓGICA DE REDIRECCIÓN ---
    # Ya no servimos el archivo, solo redirigimos.
    archivo = get_object_or_404(Archivo, area__slug=area_slug, slug=file_slug)
    return redirect(archivo.google_drive_link)

# -----------------------------------------------------------------------------
# Las vistas login_view y logout_view no necesitan cambios.
# -----------------------------------------------------------------------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                form.add_error(None, "El usuario o la contraseña son incorrectos.")
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

# -----------------------------------------------------------------------------

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')