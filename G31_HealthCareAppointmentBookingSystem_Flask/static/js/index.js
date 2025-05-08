const menuBtn = document.getElementById("menu-btn");
const navLinks = document.getElementById("nav-links");
const menuBtnIcon = menuBtn.querySelector("i")

menuBtn.addEventListener("click", (e) => {
    navLinks.classList.toggle("open")

    const isOpen = navLinks.classList.contains("open");
    menuBtnIcon.setAttribute("class", isOpen ? "ri-close-line" : "ri-menu-line")
});

navLinks.addEventListener("click", (e) => {
    navLinks.classList.remove("open");
    menuBtnIcon.setAttribute("class", "ri-menu-line");
});

const scrollRevealOption = {
    distance: "50px",
    origin: "bottom",
    duration: 1000,
};

ScrollReveal().reveal(".header__image img", {
    ...scrollRevealOption,
    origin: "right",
});

ScrollReveal().reveal(".header__content h2", {
    ...scrollRevealOption,
    delay: 500,
});

ScrollReveal().reveal(".header__content h1", {
    ...scrollRevealOption,
    delay: 1000,
});

ScrollReveal().reveal(".header__content .section__description", {
    ...scrollRevealOption,
    delay: 1500,
});

ScrollReveal().reveal(".header__form form", {
    ...scrollRevealOption,
    delay: 500,
});

ScrollReveal().reveal(".banner__card", {
    ...scrollRevealOption,
    delay: 500,
});

ScrollReveal().reveal(".client__card", {
    ...scrollRevealOption,
    delay: 500,
});

const swiper = new Swiper('.swiper', {

    slidesPerView: 3,
    spaceBetween: 30,
})

function toggleFocus(clickedCard) {
    // Get all cards
    const cards = document.querySelectorAll('.client__card');
    
    // Check if clicked card is already focused
    const isAlreadyFocused = clickedCard.classList.contains('focused');
    
    // Remove all focus and blur classes first
    cards.forEach(card => {
        card.classList.remove('focused', 'blur');
    });
    
    // If card wasn't focused before, apply focus/blur effects
    if (!isAlreadyFocused) {
        cards.forEach(card => {
            if (card === clickedCard) {
                card.classList.add('focused');
            } else {
                card.classList.add('blur');
            }
        });
    }
}

// Optional: Close focused view when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.client__card')) {
        const cards = document.querySelectorAll('.client__card');
        cards.forEach(card => {
            card.classList.remove('focused', 'blur');
        });
    }
});

function handleLogin() {
    const btn = document.querySelector('.login-btn');
    btn.style.transform = 'scale(0.95)';
    setTimeout(() => {
        btn.style.transform = 'translateY(-2px)';
        alert('Redirecting to the Doctor Login Page');
    }, 150);
}
