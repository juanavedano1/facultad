document.addEventListener('DOMContentLoaded', function() {
    const gotoRegisterLink = document.getElementById('goto-register');
    const gotoLoginLink = document.getElementById('goto-login');

    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (gotoRegisterLink) {
        gotoRegisterLink.addEventListener('click', (e) => {
            e.preventDefault();
            loginForm.classList.remove('active');
            loginForm.classList.add('inactive-left');
            
            registerForm.classList.remove('inactive-right');
            registerForm.classList.add('active');
        });
    }

    if (gotoLoginLink) {
        gotoLoginLink.addEventListener('click', (e) => {
            e.preventDefault();
            registerForm.classList.remove('active');
            registerForm.classList.add('inactive-right');

            loginForm.classList.remove('inactive-left');
            loginForm.classList.add('active');
        });
    }
});