// Активация SimpleLightbox для галереи
window.addEventListener('DOMContentLoaded', event => {
    // SimpleLightbox
    new SimpleLightbox({
        elements: '.gallery a'
    });

    // Плавная прокрутка для якорных ссылок
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Анимация навигации при прокрутке
    const navbar = document.body.querySelector('#mainNav');
    if (navbar) {
        const navbarCollapse = navbar.querySelector('.navbar-collapse');
        const collapse = new bootstrap.Collapse(navbarCollapse, {
            toggle: false
        });
        let navbarShrink = function () {
            if (window.scrollY === 0) {
                navbar.classList.remove('navbar-shrink');
            } else {
                navbar.classList.add('navbar-shrink');
            }
        };
        navbarShrink();
        document.addEventListener('scroll', navbarShrink);
    }

    // Активация всплывающих подсказок
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 