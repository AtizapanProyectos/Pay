/* ---
   Script Principal para la Aplicación
   Funcionalidades del Dashboard
--- */

document.addEventListener('DOMContentLoaded', () => {
    
    // --- Lógica para la Zona de Arrastrar y Soltar (Drag and Drop) ---
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('fileElem'); // Asegúrate que tu input tenga id="fileElem"

    if (dropArea && fileInput) {
        // Evento para abrir el selector de archivos al hacer clic
        dropArea.addEventListener('click', () => {
            fileInput.click();
        });

        // Prevenir comportamientos por defecto del navegador
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        // Añadir/quitar clase de resaltado
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.add('highlight'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, () => dropArea.classList.remove('highlight'), false);
        });

        // Manejar los archivos soltados
        dropArea.addEventListener('drop', handleDrop, false);

        function handleDrop(e) {
            let dt = e.dataTransfer;
            let files = dt.files;
            fileInput.files = files; // Asignar archivos al input real
            handleFiles(files);
        }

        // Actualizar la UI cuando se seleccionan archivos (tanto por clic como por drop)
        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });

        function handleFiles(files) {
            const gallery = document.getElementById('gallery');
            gallery.innerHTML = "";
            if (!files || files.length === 0) {
                gallery.innerHTML = '<p>No se seleccionó ningún archivo.</p>';
                return;
            }
            if (files.length === 1) {
                gallery.innerHTML = `<p>Archivo seleccionado: <strong>${files[0].name}</strong></p>`;
            } else {
                gallery.innerHTML = `<p><strong>${files.length}</strong> archivos seleccionados.</p>`;
            }
        }
    }

});

/**
 * Copia un texto al portapapeles y da feedback visual al usuario.
 * @param {string} textToCopy - El texto (la URL) que se va a copiar.
 * @param {HTMLElement} buttonElement - El elemento <button> que fue presionado.
 */
function copyLink(textToCopy, buttonElement) {
    // Usamos la API moderna y segura del navegador para copiar al portapapeles
    navigator.clipboard.writeText(textToCopy).then(() => {
        // Si la copia fue exitosa...
        const originalText = buttonElement.textContent;
        buttonElement.textContent = '¡Copiado!'; // Cambia el texto del botón
        buttonElement.disabled = true;       // Deshabilita el botón temporalmente

        // Después de 2 segundos, restaura el botón a su estado original
        setTimeout(() => {
            buttonElement.textContent = originalText;
            buttonElement.disabled = false;
        }, 2000);

    }).catch(err => {
        // Si hubo un error (por ej. por permisos del navegador)
        console.error('Error al copiar el enlace: ', err);
        alert('No se pudo copiar el enlace.'); // Muestra una alerta de error
    });
}