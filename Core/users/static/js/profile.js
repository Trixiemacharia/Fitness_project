// ═══════════════════════════════════════════════════
// PROFILE / SETTINGS SCREEN
// ═══════════════════════════════════════════════════

let prefsLoaded = false;

async function loadProfileScreen() {
    if (prefsLoaded) return;

    try {
        const res   = await fetch('/api/preferences/');
        const prefs = await res.json();

        const goalSelect = document.getElementById('pref-goal');
        if (goalSelect) goalSelect.value = prefs.fitness_goal || 'stay_active';

        const unitsSelect = document.getElementById('pref-units');
        if (unitsSelect) unitsSelect.value = prefs.units || 'metric';

        const darkToggle = document.getElementById('pref-dark-mode');
        if (darkToggle) darkToggle.checked = prefs.dark_mode !== false;

        const notifToggle = document.getElementById('pref-notifications');
        if (notifToggle) notifToggle.checked = prefs.notifications !== false;

        const days = prefs.preferred_days || [];
        document.querySelectorAll('.day-chip').forEach(chip => {
            chip.classList.toggle('selected', days.includes(chip.getAttribute('data-day')));
        });

        prefsLoaded = true;
    } catch (e) {
        console.error('Prefs load failed:', e);
    }
}

// ── Day chip toggle ──
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.day-chip').forEach(chip => {
        chip.addEventListener('click', () => chip.classList.toggle('selected'));
    });

    // Dark mode toggle — instant apply, no save needed
    const darkToggle = document.getElementById('pref-dark-mode');
    darkToggle?.addEventListener('change', () => {
        applyTheme(darkToggle.checked);
        localStorage.setItem('darkMode', darkToggle.checked);
    });

    // Notifications toggle — update banner check immediately
    const notifToggle = document.getElementById('pref-notifications');
    notifToggle?.addEventListener('change', () => {
        if (notifToggle.checked) {
            checkWorkoutReminder();
        } else {
            dismissReminder();
        }
    });
});

// ── Save all preferences ──
async function savePreferences() {
    const goal  = document.getElementById('pref-goal')?.value;
    const units = document.getElementById('pref-units')?.value;
    const dark  = document.getElementById('pref-dark-mode')?.checked;
    const notif = document.getElementById('pref-notifications')?.checked;
    const days  = [...document.querySelectorAll('.day-chip.selected')]
                    .map(c => c.getAttribute('data-day'));

    try {
        const res = await fetch('/api/preferences/', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({
                fitness_goal:   goal,
                units:          units,
                dark_mode:      dark,
                notifications:  notif,
                preferred_days: days,
            }),
        });

        if (res.ok) {
            applyTheme(dark);
            localStorage.setItem('darkMode', dark);
            prefsLoaded = false;  // allow refresh next time

            // Re-check reminders after saving
            if (notif) checkWorkoutReminder();
            else dismissReminder();

            showSettingsToast('✓ Settings saved');
        } else {
            showSettingsToast('Something went wrong');
        }
    } catch (e) {
        console.error('Save prefs failed:', e);
        showSettingsToast('Could not save settings');
    }
}

function showSettingsToast(msg) {
    const t = document.getElementById('settings-toast');
    if (!t) return;
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2500);
}