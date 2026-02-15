// Smooth scroll reveal animation
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('.category-card');
    
    // Add fade-in class to cards
    cards.forEach((card, index) => {
        card.style.animation = `fadeIn 0.4s ease-out ${index * 0.05}s forwards`;
        card.style.opacity = '0';
    });
});

// Handle back button on iOS/mobile
if (document.querySelector('.back-btn')) {
    document.querySelector('.back-btn').addEventListener('click', function(e) {
        e.preventDefault();
        if (document.referrer) {
            history.back();
        } else {
            window.location.href = '/dashboard/';
        }
    });
}

// Add touch feedback for mobile
const cards = document.querySelectorAll('.category-card');
cards.forEach(card => {
    card.addEventListener('touchstart', function() {
        this.style.transform = 'translateY(-2px)';
        this.style.boxShadow = '0 12px 28px rgba(0, 0, 0, 0.08)';
    });
    
    card.addEventListener('touchend', function() {
        this.style.transform = '';
        this.style.boxShadow = '';
    });
});