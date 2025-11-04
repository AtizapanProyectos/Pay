# core/google_drive_service.py
import os
import io
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from django.conf import settings
from google.auth.exceptions import RefreshError # Para manejar errores de token
# Si necesitas un token fresco y no tienes el refresh_token, 
# la siguiente línea es la que realizaría el flujo interactivo (pero la quitamos)
# from google_auth_oauthlib.flow import InstalledAppFlow 

# Define los permisos que tu app necesitará.
SCOPES = ['https://www.googleapis.com/auth/drive']
# Dirección base de OAuth 2.0 de Google (necesaria para el refresh)
TOKEN_URI = 'https://oauth2.googleapis.com/token'


def get_drive_service():
    """
    Autentica y devuelve un objeto de servicio de la API de Drive
    usando variables de settings.py (con REFRESH_TOKEN para persistencia).
    """
    creds = None
    
    # --- 1. Obtener las variables de settings.py ---
    client_id = getattr(settings, 'GOOGLE_DRIVE_CLIENT_ID', None)
    client_secret = getattr(settings, 'GOOGLE_DRIVE_CLIENT_SECRET', None)
    refresh_token = getattr(settings, 'GOOGLE_DRIVE_REFRESH_TOKEN', None)
    # El access_token se puede dejar en None. El refresh lo generará.
    access_token = getattr(settings, 'GOOGLE_DRIVE_ACCESS_TOKEN', None) 
    
    if not all([client_id, client_secret, refresh_token]):
        # NOTA: En este punto, tu app fallaría si no encuentra los secretos.
        raise ValueError("Faltan variables de configuración de Google Drive (CLIENT_ID, CLIENT_SECRET, o REFRESH_TOKEN) en settings.py")
    
    # --- 2. Crear el objeto Credentials con los datos de settings.py ---
    creds = Credentials(
        token=access_token, 
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri=TOKEN_URI,
        scopes=SCOPES
    )
    
    # --- 3. Refrescar el token si está expirado o no presente ---
    # Esto usa el refresh_token para obtener un nuevo access_token sin interacción.
    if not creds.valid or not creds.token:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as e:
                print(f"ERROR: No se pudo refrescar el token. Revise GOOGLE_DRIVE_REFRESH_TOKEN. Detalle: {e}")
                raise
        elif creds and creds.refresh_token:
             # Forzar refresh si no hay token al inicio (token=None)
            try:
                creds.refresh(Request())
            except RefreshError as e:
                print(f"ERROR: No se pudo generar el token inicial. Revise GOOGLE_DRIVE_REFRESH_TOKEN. Detalle: {e}")
                raise
        else:
            # Esto NO DEBERÍA pasar si tienes el refresh_token
            raise Exception("No hay credenciales válidas ni refresh_token disponible para Drive.")


    return build('drive', 'v3', credentials=creds)

def create_folder_if_not_exists(service, folder_name):
    """
    Busca una carpeta por nombre. Si no existe, la crea.
    Devuelve el ID de la carpeta.
    """
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])

    if files:
        return files[0].get('id')
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')


def upload_file_to_drive(file_obj, area_slug):
    """
    Sube un archivo a una carpeta específica en Google Drive, lo hace público y devuelve su ID y enlace.
    """
    service = get_drive_service()
    
    # 1. Obtiene o crea la carpeta para el área municipal
    folder_id = create_folder_if_not_exists(service, area_slug)
    
    # 2. Prepara los metadatos del archivo
    file_metadata = {
        'name': file_obj.name,
        'parents': [folder_id]
    }
    
    # 3. Prepara el contenido del archivo para la subida
    # Asegúrate de rebobinar el file_obj si ya se leyó antes (comentado si viene de un upload nuevo)
    file_obj.seek(0)
    media = MediaIoBaseUpload(
        io.BytesIO(file_obj.read()),
        mimetype=file_obj.content_type,
        resumable=True
    )
    
    # 4. Sube el archivo
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()
    
    file_id = file.get('id')
    
    # 5. Hace el archivo público (cualquier persona con el enlace puede verlo)
    permission = {
        'type': 'anyone',
        'role': 'reader'
    }
    service.permissions().create(fileId=file_id, body=permission).execute()

    # 6. Devuelve el ID y el enlace para guardarlo en la base de datos
    return {
        'id': file_id,
        'link': file.get('webViewLink')
    }

def delete_file_from_drive(file_id):
    """
    Elimina permanentemente un archivo de Google Drive usando su ID.
    """
    try:
        service = get_drive_service()
        service.files().delete(fileId=file_id).execute()
        return True
    except Exception as e:
        print(f"Error al eliminar el archivo de Drive: {e}")
        return False