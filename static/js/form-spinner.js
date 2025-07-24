// En static/js/form-spinner.js

document.addEventListener('DOMContentLoaded', function() {
    // Buscamos el formulario por su nuevo ID
    const form = document.getElementById('modify-service-form');

    if (form) {
        // Escuchamos el evento 'submit' del formulario
        form.addEventListener('submit', function() {
            // Buscamos el botón de envío DENTRO del formulario
            const submitButton = form.querySelector('input[type="submit"]');

            if (submitButton) {
                // Desactivamos el botón y mostramos el spinner
                submitButton.disabled = true;
                submitButton.value = 'Guardando...'; // Cambiamos el texto
            }
        });
    }
});
// En static/js/form-spinner.js

document.addEventListener('DOMContentLoaded', function() {
    // Buscamos el formulario de edición por su ID
    const editForm = document.getElementById('edit-user-form');

    if (editForm) {
        // Escuchamos el evento 'submit' del formulario
        editForm.addEventListener('submit', function() {
            // Buscamos el botón de envío DENTRO de ese formulario
            const submitButton = editForm.querySelector('input[type="submit"]');

            if (submitButton) {
                // Desactivamos el botón y mostramos el spinner
                submitButton.disabled = true;
                // Cambiamos el valor del botón para que muestre el texto de carga
                submitButton.value = 'Guardando...';
            }
        });
    }
});