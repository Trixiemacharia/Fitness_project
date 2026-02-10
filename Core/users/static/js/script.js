// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const welcomeScreen = document.getElementById('welcome-screen');
    const authContainer = document.getElementBy('login-form');
    
    // Show welcome screen immediately
    welcomeScreen.style.display = 'flex';
    authContainer.style.display = 'none';
    
    // After 5 seconds, transition to login form
    setTimeout(function() {
        // Fade out welcome screen
        welcomeScreen.style.opacity = '0';
        
        // After fade completes, hide welcome and show auth
        setTimeout(function() {
            welcomeScreen.style.display = 'none';
            authContainer.style.display = 'flex';
            
            // Small delay before fading in auth container
            setTimeout(function() {
                authContainer.style.opacity = '1';
            }, 50);
        }, 1000); // Match the 1s transition duration
    }, 5000); // 5 seconds display time
});