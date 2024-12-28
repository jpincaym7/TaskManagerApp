// Manejo del botón de navegación
document.addEventListener('DOMContentLoaded', function() {
    const navTrigger = document.querySelector('.nav-trigger');
    const navBottom = document.querySelector('.nav-bottom');
    let lastScrollTop = 0;
    let isNavVisible = true;

    // Función para mostrar/ocultar la navegación
    function toggleNav() {
        isNavVisible = !isNavVisible;
        navBottom.classList.toggle('hidden');
        navTrigger.classList.toggle('active');
    }

    // Event listener para el botón
    navTrigger.addEventListener('click', toggleNav);

    // Manejo del scroll para ocultar/mostrar automáticamente
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > lastScrollTop && isNavVisible) {
            // Scrolling hacia abajo
            toggleNav();
        } else if (scrollTop < lastScrollTop && !isNavVisible) {
            // Scrolling hacia arriba
            toggleNav();
        }
        
        lastScrollTop = scrollTop;
    }, { passive: true });
});