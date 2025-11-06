document.addEventListener('DOMContentLoaded', function() {
    // Establecer fechas mínimas en los inputs de fecha
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const checkIn = document.getElementById('check_in');
    const checkOut = document.getElementById('check_out');
    
    // Formato YYYY-MM-DD para el input date
    checkIn.min = today.toISOString().split('T')[0];
    checkOut.min = tomorrow.toISOString().split('T')[0];
    
    // Asegurar que la fecha de salida sea después de la de entrada
    checkIn.addEventListener('change', function() {
        const selectedDate = new Date(this.value);
        const nextDay = new Date(selectedDate);
        nextDay.setDate(nextDay.getDate() + 1);
        checkOut.min = nextDay.toISOString().split('T')[0];
        
        if (new Date(checkOut.value) <= selectedDate) {
            checkOut.value = nextDay.toISOString().split('T')[0];
        }
    });
    
    // Manejar el formulario de búsqueda
    const searchForm = document.querySelector('form[action="/api/rooms/search"]');
    if (searchForm) {
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const params = new URLSearchParams();
            
            for (const [key, value] of formData.entries()) {
                params.append(key, value);
            }
            
            try {
                const response = await fetch(`/api/rooms/search?${params.toString()}`);
                const data = await response.json();
                
                if (data.available_rooms && data.available_rooms.length > 0) {
                    // Redirigir a la página de resultados o mostrar modal
                    window.location.href = `/habitaciones?${params.toString()}`;
                } else {
                    alert('Lo sentimos, no hay habitaciones disponibles para las fechas seleccionadas.');
                }
            } catch (error) {
                console.error('Error al buscar habitaciones:', error);
                alert('Error al buscar habitaciones. Por favor, intente nuevamente.');
            }
        });
    }
});