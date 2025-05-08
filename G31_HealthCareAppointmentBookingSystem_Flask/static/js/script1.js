// Update URL without page reload when toggling
document.querySelector('.register-btn').addEventListener('click', function(e) {
    e.preventDefault();
    const container = document.querySelector('.container');
    container.classList.add('active');
    history.pushState({}, '', '/signup');
});

document.querySelector('.login-btn').addEventListener('click', function(e) {
    e.preventDefault();
    const container = document.querySelector('.container');
    container.classList.remove('active');
    history.pushState({}, '', '/login');
});

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get elements
    const loginForm = document.querySelector('.form-box.login');
    const registerForm = document.querySelector('.form-box.register');
    const loginBtn = document.querySelector('.login-btn');
    const registerBtn = document.querySelector('.register-btn');
    
    // Check if elements exist on the page
    if (loginForm && registerForm && loginBtn && registerBtn) {
        // Handle login button click
        loginBtn.addEventListener('click', function() {
            loginForm.style.display = 'block';
            registerForm.style.display = 'none';
        });
        
        // Handle register button click
        registerBtn.addEventListener('click', function() {
            loginForm.style.display = 'none';
            registerForm.style.display = 'block';
        });
        
        // Set initial state - show login form by default
        loginForm.style.display = 'block';
        registerForm.style.display = 'none';
    }
});