const carousel = document.querySelector('.carousel');
const prevBtn = document.querySelector('.prev');
const nextBtn = document.querySelector('.next');
const cardWidth = 300; // card width + gap

prevBtn.addEventListener('click', () => {
    carousel.scrollLeft -= cardWidth;
});

nextBtn.addEventListener('click', () => {
    carousel.scrollLeft += cardWidth;
});

document.documentElement.style.scrollBehavior = 'smooth';

document.addEventListener("DOMContentLoaded", function () {
    // Card Hover Animation
    const cards = document.querySelectorAll(".card");
    cards.forEach(card => {
        card.addEventListener("mouseenter", function () {
            this.style.transform = "translateY(-8px)";
            this.style.boxShadow = "0 10px 25px rgba(0, 0, 0, 0.15)";
        });
        card.addEventListener("mouseleave", function () {
            this.style.transform = "translateY(0)";
            this.style.boxShadow = "0 4px 10px rgba(0, 0, 0, 0.1)";
        });
    });

    // Icon Hover Animation
    const icons = document.querySelectorAll(".icon-inner i");
    icons.forEach(icon => {
        icon.addEventListener("mouseenter", function () {
            this.style.transform = "rotate(20deg)";
            this.style.transition = "transform 0.3s ease-in-out";
        });
        icon.addEventListener("mouseleave", function () {
            this.style.transform = "rotate(0deg)";
        });
    });

    // Image Hover Animation
    const images = document.querySelectorAll(".experts img, .convenient-app img");
    images.forEach(img => {
        img.addEventListener("mouseenter", function () {
            this.style.transform = "scale(1.05)";
            this.style.filter = "brightness(1.1)";
            this.style.transition = "transform 0.3s ease-in-out, filter 0.3s ease-in-out";
        });
        img.addEventListener("mouseleave", function () {
            this.style.transform = "scale(1)";
            this.style.filter = "brightness(1)";
        });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    // Function to apply hover effects
    function addHoverEffect(card, gradient, textColor) {
        card.addEventListener("mouseenter", function () {
            this.style.background = gradient;
            this.style.color = textColor;
            this.style.transition = "background 0.5s ease-in-out, color 0.5s ease-in-out";

            // Change the text color of all child elements
            const elements = this.querySelectorAll(".description, .subtitle-text, .kite-list li, .price, .service-label");
            elements.forEach(el => el.style.color = textColor);
        });

        card.addEventListener("mouseleave", function () {
            this.style.background = ""; // Reset to default
            this.style.color = ""; // Reset to default

            const elements = this.querySelectorAll(".description, .subtitle-text, .kite-list li, .price, .service-label");
            elements.forEach(el => el.style.color = "");

            // Ensure .description specifically turns back to #5e1b1b
            const description = this.querySelector(".description");
            if (description) {
                description.style.color = "#5e1b1b";
            }
        });
    }

    // Select the cards
    const card1 = document.querySelector(".card1");
    const card2 = document.querySelector(".card2");

    // Apply hover effects with gradient colors
    if (card1) addHoverEffect(card1, "linear-gradient(135deg, #6a11cb, #2575fc)", "#ffffff"); // Purple to Blue
    if (card2) addHoverEffect(card2, "linear-gradient(135deg, #6a11cb, #2575fc)", "#ffffff"); // Pink to Light Red
});

document.addEventListener("DOMContentLoaded", function () {
    const scrollElements = document.querySelectorAll(".scroll-reveal");

    const scrollReveal = () => {
        scrollElements.forEach((el) => {
            if (el.getBoundingClientRect().top < window.innerHeight * 0.85) {
                el.classList.add("active");
            }
        });
    };

    document.addEventListener("scroll", scrollReveal);
    scrollReveal();
});
