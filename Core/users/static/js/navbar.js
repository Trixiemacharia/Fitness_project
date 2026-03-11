// SIDEBAR

const sidebar        = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const hamburgerBtn   = document.getElementById('hamburgerBtn');
const sidebarClose   = document.getElementById('sidebarClose');

function openSidebar() {
    sidebar.classList.add('open');
    sidebarOverlay.classList.add('show');
    hamburgerBtn.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeSidebar() {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('show');
    hamburgerBtn.classList.remove('open');
    document.body.style.overflow = '';
}

hamburgerBtn?.addEventListener('click', () => {
    sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
});

sidebarClose?.addEventListener('click', closeSidebar);
sidebarOverlay?.addEventListener('click', closeSidebar);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSidebar(); });

// ═══════════════════════════════════════════════════
// SPA SCREEN SWITCHING
// ═══════════════════════════════════════════════════

const screens  = document.querySelectorAll('.spa-screen');
const navLinks = document.querySelectorAll('.nav-link');

const screenTitles = {
    'dashboard-screen': 'My <span>Workouts</span>',
    'progress-screen':  'My <span>Progress</span>',
    'nutrition-screen': 'My<span>Nutrition</span>',
    'profile-screen':   'My <span>Profile</span>',
    'about-screen':     'About <span>FitTrack</span>',
    'contact-screen':   'Get in <span>Touch</span>',
};

function switchScreen(screenId) {
    screens.forEach(s => s.classList.remove('active'));

    const target = document.getElementById(screenId);
    if (target) target.classList.add('active');

    navLinks.forEach(link => {
        link.classList.toggle('active', link.getAttribute('data-screen') === screenId);
    });

    const topBarTitle = document.getElementById('topBarTitle');
    if (topBarTitle && screenTitles[screenId]) {
        topBarTitle.innerHTML = screenTitles[screenId];
    }

    if (screenId === 'progress-screen') loadProgressScreen();
    if (screenId === 'profile-screen')  loadProfileScreen();

    closeSidebar();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

navLinks.forEach(link => {
    link.addEventListener('click', () => {
        const screenId = link.getAttribute('data-screen');
        if (screenId) switchScreen(screenId);
    });
});

// ═══════════════════════════════════════════════════
// DARK / LIGHT MODE
// ═══════════════════════════════════════════════════

function applyTheme(dark) {
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');

    // Swap CSS variable values for light mode
    if (!dark) {
        document.documentElement.style.setProperty('--black',   '#f4f4f4');
        document.documentElement.style.setProperty('--surface', '#e8e8e8');
        document.documentElement.style.setProperty('--card-bg', '#ffffff');
        document.documentElement.style.setProperty('--border',  '#d0d0d0');
        document.documentElement.style.setProperty('--white',   '#111111');
        document.documentElement.style.setProperty('--grey-1',  '#222222');
        document.documentElement.style.setProperty('--grey-2',  '#555555');
        document.documentElement.style.setProperty('--grey-3',  '#aaaaaa');
    } else {
        document.documentElement.style.setProperty('--black',   '#0a0a0a');
        document.documentElement.style.setProperty('--surface', '#111111');
        document.documentElement.style.setProperty('--card-bg', '#181818');
        document.documentElement.style.setProperty('--border',  '#2a2a2a');
        document.documentElement.style.setProperty('--white',   '#ffffff');
        document.documentElement.style.setProperty('--grey-1',  '#f0f0f0');
        document.documentElement.style.setProperty('--grey-2',  '#a0a0a0');
        document.documentElement.style.setProperty('--grey-3',  '#404040');
    }
}

// Load saved theme on init
document.addEventListener('DOMContentLoaded', () => {
    const savedDark = localStorage.getItem('darkMode') !== 'false';
    applyTheme(savedDark);

    const toggle = document.getElementById('pref-dark-mode');
    if (toggle) toggle.checked = savedDark;

    // Check notifications on load
    checkWorkoutReminder();
});

// ═══════════════════════════════════════════════════
// IN-APP NOTIFICATIONS / WORKOUT REMINDERS
// ═══════════════════════════════════════════════════

const DAY_MAP = { 0:'sun', 1:'mon', 2:'tue', 3:'wed', 4:'thu', 5:'fri', 6:'sat' };
const DAY_LABELS = { mon:'Monday', tue:'Tuesday', wed:'Wednesday', thu:'Thursday', fri:'Friday', sat:'Saturday', sun:'Sunday' };

async function checkWorkoutReminder() {
    // Only show if user has notifications on
    try {
        const res   = await fetch('/api/preferences/');
        const prefs = await res.json();

        if (!prefs.notifications) return;

        const todayKey    = DAY_MAP[new Date().getDay()];
        const preferredDays = prefs.preferred_days || [];

        if (!preferredDays.includes(todayKey)) return;

        // Check if they've already done a workout today
        const logRes  = await fetch('/api/logs/');
        const logs    = await logRes.json();
        const today   = new Date().toISOString().split('T')[0];
        const doneToday = logs.some(log => log.updated_at?.startsWith(today) && log.sets_completed > 0);

        if (doneToday) return;  // already worked out, no reminder needed

        showWorkoutReminder(`💪 Today is a workout day! Let's get it done.`);

    } catch (e) {
        // Silently fail — don't break the page
    }
}

function showWorkoutReminder(msg) {
    const banner = document.getElementById('workoutReminder');
    const text   = document.getElementById('reminderText');
    if (!banner || !text) return;
    text.textContent = msg;
    banner.style.display = 'flex';
}

function dismissReminder() {
    const banner = document.getElementById('workoutReminder');
    if (banner) banner.style.display = 'none';
}

// Also used by navbar banner (if used elsewhere)
function dismissNotif() {
    const banner = document.getElementById('notifBanner');
    if (banner) banner.style.display = 'none';
}