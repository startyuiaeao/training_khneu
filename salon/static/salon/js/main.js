// Допоміжний JavaScript

document.addEventListener('DOMContentLoaded', function () {

    // Автоматичне закриття алертів через 5 секунд
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });

    // Підсвічування активного пункту меню
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll(
        '.navbar-nav .nav-link'
    );
    navLinks.forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

});
