//Fade out welcome screen
setTimeout(() => {
    const welcome = document.getElementById('welcome');
    welcome.style.opacity = '0';
    setTimeout(() => {
        welcome.style.display = 'none';
        document.getElementById('login-form').style.display = 'flex';
    }, 1000);
}, 5000);

function redirectSignup(){
    window.location.href = "/register";
}