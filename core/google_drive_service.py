# core/google_drive_service.py
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from django.conf import settings
import io

# Define los permisos que tu app necesitará.
# 'drive.file' es un buen balance para crear, ver y administrar archivos creados por la app.
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """
    Autentica y devuelve un objeto de servicio de la API de Drive.
    """
    creds = None
    token_path = os.path.join(settings.BASE_DIR, 'token.json')
    credentials_path = os.path.join(settings.BASE_DIR, 'credentials.json')

    # El archivo token.json almacena los tokens de acceso y actualización del usuario,
    # y se crea automáticamente la primera vez que se completa el flujo de autorización.
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # Si no hay credenciales (válidas), permite que el usuario inicie sesión.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # ¡IMPORTANTE! La primera vez que ejecutes esto, se abrirá una ventana
            # del navegador para que autorices la app.
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            # LÍNEA CORREGIDA
            creds = flow.run_local_server(port=8090)
        
        # Guarda las credenciales para la próxima ejecución
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

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