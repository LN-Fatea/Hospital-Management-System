// Intersection Observer for fade-in animations
const fadeInObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in-visible');
            fadeInObserver.unobserve(entry.target);
        }
    });
}, {
    threshold: 0.1
});

// Slide-in animation observer
const slideInObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('slide-in-visible');
            slideInObserver.unobserve(entry.target);
        }
    });
}, {
    threshold: 0.1
});

// Card hover effect
function initializeCardHoverEffects() {
    const cards = document.querySelectorAll('.login-card, .feature-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
        });

        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
        });
    });
}

// Button hover animation
function initializeButtonAnimations() {
    const buttons = document.querySelectorAll('.card-link, .btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', (e) => {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            button.style.setProperty('--x', `${x}px`);
            button.style.setProperty('--y', `${y}px`);
            button.classList.add('pulse');
        });

        button.addEventListener('mouseleave', () => {
            button.classList.remove('pulse');
        });
    });
}

// Gradient text animation
function initializeGradientTextAnimation() {
    const gradientTexts = document.querySelectorAll('.gradient-text');
    gradientTexts.forEach(text => {
        text.style.backgroundSize = '200% auto';
        setInterval(() => {
            text.style.backgroundPosition = text.style.backgroundPosition === '200% center' 
                ? '0% center' 
                : '200% center';
        }, 3000);
    });
}

// Initialize animations when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add fade-in animation to elements
    document.querySelectorAll('.fade-in').forEach(el => fadeInObserver.observe(el));
    
    // Add slide-in animation to elements
    document.querySelectorAll('.slide-in').forEach(el => slideInObserver.observe(el));
    
    // Initialize all animations
    initializeCardHoverEffects();
    initializeButtonAnimations();
    initializeGradientTextAnimation();
    
    // Add smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});
