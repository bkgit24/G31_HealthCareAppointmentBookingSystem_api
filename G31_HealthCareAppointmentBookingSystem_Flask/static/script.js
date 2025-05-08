
// past....................


const container = document.querySelector('.container');
const registerBtn = document.querySelector('.register-btn');
const loginBtn = document.querySelector('.login-btn');

registerBtn.addEventListener('click', () => {
    container.classList.add('active');
});

loginBtn.addEventListener('click', () => {
    container.classList.remove('active');
});

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        const flashMessages = document.querySelector('.flash-messages');
        if (flashMessages) {
            flashMessages.remove();
        }
    }, 5000);
});
// Handle back/forward browser navigation
window.addEventListener('popstate', function(event) {
    const isSignupPage = window.location.pathname === '/signup';
    const container = document.querySelector('.container');
    if (isSignupPage) {
        container.classList.add('active');
    } else {
        container.classList.remove('active');
    }
});
