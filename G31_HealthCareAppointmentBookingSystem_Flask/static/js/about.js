document.addEventListener('DOMContentLoaded', () => {
    // Select all stat value elements
    const statValues = document.querySelectorAll('.stat-value');
    
    // Create intersection observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Add class to trigger the animation
                entry.target.style.animation = 'countUp 2s ease-out forwards';
                
                // Get the target number from the text content
                const targetValue = entry.target.textContent.replace(/[^0-9.]/g, '');
                
                // Start counting animation
                if (!entry.target.hasAttribute('data-animated')) {
                    entry.target.setAttribute('data-animated', 'true');
                    
                    // For percentage values
                    if (entry.target.textContent.includes('%')) {
                        animateValue(entry.target, 0, parseFloat(targetValue), 2000, '%');
                    }
                    // For values with K+
                    else if (entry.target.textContent.includes('K+')) {
                        animateValue(entry.target, 0, parseFloat(targetValue), 2000, 'K+');
                    }
                    // For regular numbers
                    else {
                        animateValue(entry.target, 0, parseFloat(targetValue), 2000, '+');
                    }
                }
            }
        });
    }, {
        threshold: 0.1
    });

    // Helper function to animate counting
    function animateValue(element, start, end, duration, suffix) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const currentValue = Math.floor(progress * (end - start) + start);
            element.textContent = `${currentValue}${suffix}`;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Observe each stat value element
    statValues.forEach(value => observer.observe(value));
});