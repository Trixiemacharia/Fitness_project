// ═══════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════
const API_BASE = '/api';
let allCategories = [];
let currentCategory = null;
let userLogs = {};         // { exercise_id: { sets_completed, total_sets, status } }

let activeLevel  = document.body.getAttribute('data-fitness-level') || 'beginner';
let activeType   = 'all';
let activeMuscle = 'all';

// ═══════════════════════════════════════════════════
// DOM REFS
// ═══════════════════════════════════════════════════
const dashboardSection  = document.getElementById('dashboard');
const exercisesSection  = document.getElementById('exercises-section');
const detailSection     = document.getElementById('exercise-detail-section');
const exercisesList     = document.getElementById('exercises-list');
const categoryTitle     = document.getElementById('category-title');
const cardContainer     = document.querySelector('.card-container');

// ═══════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([loadCategories(), loadLogs()]);
    initChips();
    updateMuscleChips();
    renderCategoryCards();
});

async function loadCategories() {
    try {
        const res = await fetch(`${API_BASE}/categories/`);
        allCategories = await res.json();
    } catch (e) {
        console.error('Failed to load categories:', e);
        allCategories = [];
    }
}

async function loadLogs() {
    try {
        const res = await fetch(`${API_BASE}/logs/`);
        const data = await res.json();
        userLogs = {};
        data.forEach(log => {
            userLogs[log.exercise_id] = {
                sets_completed: log.sets_completed,
                total_sets: log.total_sets,
                status: log.status,
            };
        });
    } catch (e) {
        console.error('Failed to load logs:', e);
    }
}

// ═══════════════════════════════════════════════════
// CHIPS
// ═══════════════════════════════════════════════════
function initChips() {
    // Level chips
    document.querySelectorAll('.chip[data-level]').forEach(chip => {
        if (chip.getAttribute('data-level') === activeLevel) chip.classList.add('selected');
        chip.addEventListener('click', () => {
            document.querySelectorAll('.chip[data-level]').forEach(c => c.classList.remove('selected'));
            chip.classList.add('selected');
            activeLevel = chip.getAttribute('data-level');
            updateLevelTag();
            if (currentCategory && exercisesSection.style.display !== 'none') {
                renderExercises(currentCategory.exercises);
            }
        });
    });

    // Training type chips
    document.querySelectorAll('.chip[data-type]').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.chip[data-type]').forEach(c => c.classList.remove('selected'));
            chip.classList.add('selected');
            activeType = chip.getAttribute('data-type');
            updateMuscleChips();
            renderCategoryCards();
        });
    });
}

function updateMuscleChips() {
    const row = document.getElementById('muscle-chip-row');
    if (!row) return;

    let relevantMuscles = new Set();
    allCategories.forEach(cat => {
        if (activeType === 'all' || cat.training_type === activeType) {
            (cat.muscle_groups || []).forEach(mg => {
                relevantMuscles.add(mg.name + '|' + mg.display_name);
            });
        }
    });

    row.innerHTML = '';

    const allChip = makeChip('All', 'all', 'muscle');
    if (activeMuscle === 'all') allChip.classList.add('selected');
    row.appendChild(allChip);

    relevantMuscles.forEach(entry => {
        const [name, label] = entry.split('|');
        const chip = makeChip(label, name, 'muscle');
        if (activeMuscle === name) chip.classList.add('selected');
        row.appendChild(chip);
    });

    if (activeMuscle !== 'all' && ![...relevantMuscles].some(e => e.startsWith(activeMuscle + '|'))) {
        activeMuscle = 'all';
        row.querySelector('.chip')?.classList.add('selected');
    }
}

function makeChip(label, value, type) {
    const chip = document.createElement('button');
    chip.className = 'chip';
    chip.textContent = label;
    chip.setAttribute(`data-${type}`, value);
    chip.addEventListener('click', () => {
        document.querySelectorAll(`[data-${type}]`).forEach(c => c.classList.remove('selected'));
        chip.classList.add('selected');
        if (type === 'muscle') {
            activeMuscle = value;
            renderCategoryCards();
        }
    });
    return chip;
}

// ═══════════════════════════════════════════════════
// CATEGORY CARDS
// ═══════════════════════════════════════════════════
function renderCategoryCards() {
    cardContainer.innerHTML = '';

    const filtered = allCategories.filter(cat => {
        const typeMatch   = activeType   === 'all' || cat.training_type === activeType;
        const muscleMatch = activeMuscle === 'all' || (cat.muscle_groups || []).some(mg => mg.name === activeMuscle);
        return typeMatch && muscleMatch;
    });

    if (filtered.length === 0) {
        cardContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <p class="empty-msg">No categories match</p>
                <p class="empty-sub">Try a different filter</p>
            </div>`;
        return;
    }

    filtered.forEach((cat, index) => {
        cardContainer.appendChild(buildCategoryCard(cat, index));
    });
}

function buildCategoryCard(cat, index) {
    const div = document.createElement('div');
    div.className = `category-card ${cat.training_type || 'strength'}`;
    div.setAttribute('data-id', cat.id);
    div.style.opacity = '0';
    div.style.animation = `fadeUp 0.4s ease-out ${index * 0.07}s forwards`;

    div.innerHTML = `
        <div class="card-left">
            <span class="card-type-tag">${(cat.training_type || '').toUpperCase()}</span>
            <h3>${cat.name}</h3>
            <p class="program-count">${cat.exercises ? cat.exercises.length : 0} Exercises</p>
        </div>
        ${cat.image ? `<div class="card-right"><img src="${cat.image}" alt="${cat.name}"></div>` : ''}
        <span class="card-number">${String(index + 1).padStart(2, '0')}</span>
    `;

    div.addEventListener('click', () => showExercises(cat));
    return div;
}

// ═══════════════════════════════════════════════════
// EXERCISES LIST
// ═══════════════════════════════════════════════════
function showExercises(category) {
    currentCategory = category;
    categoryTitle.textContent = category.name;
    updateLevelTag();
    renderExercises(category.exercises);

    dashboardSection.style.display  = 'none';
    exercisesSection.style.display  = 'block';
    if (detailSection) detailSection.style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateLevelTag() {
    const tag = document.getElementById('level-tag');
    if (tag) tag.textContent = activeLevel.charAt(0).toUpperCase() + activeLevel.slice(1);
}

function renderExercises(exercises) {
    exercisesList.innerHTML = '';

    const filtered = (exercises || []).filter(ex => ex.level === activeLevel);

    if (filtered.length === 0) {
        exercisesList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">💪</div>
                <p class="empty-msg">No ${activeLevel} exercises yet</p>
                <p class="empty-sub">Switch level or check back soon</p>
            </div>`;
        return;
    }

    filtered.forEach((ex, index) => {
        exercisesList.appendChild(buildExerciseCard(ex, index));
    });
}

function buildExerciseCard(ex, index) {
    const div = document.createElement('div');
    div.className = 'exercise-card';
    div.setAttribute('data-exercise-id', ex.id);
    div.style.opacity = '0';
    div.style.animation = `fadeIn 0.35s ease-out ${index * 0.06}s forwards`;

    // Media
    let mediaSide = '';
    if (ex.image) {
        mediaSide = `<div class="exercise-img-side"><img src="${ex.image}" alt="${ex.name}" loading="lazy"></div>`;
    } else if (ex.demo_video) {
        mediaSide = `<div class="exercise-video-side"><video muted loop playsinline><source src="${ex.demo_video}" type="video/mp4"></video></div>`;
    } else {
        mediaSide = `<div class="exercise-no-media">${getCategoryIcon(ex.exercise_type)}</div>`;
    }

    // Stats
    const stats = (ex.stats || []).map(s => `
        <div class="stat-item">
            <span class="stat-label">${s.label}</span>
            <span class="stat-value">${s.value}</span>
        </div>`).join('');

    // Completion status bar
    const log    = userLogs[ex.id];
    const status = log ? log.status : 'not_started';
    const statusBar = buildStatusBar(log, ex);

    div.innerHTML = `
        <div class="exercise-card-inner">
            ${mediaSide}
            <div class="exercise-body">
                <span class="level-badge ${ex.level}">${ex.level.charAt(0).toUpperCase() + ex.level.slice(1)}</span>
                <h3 class="exercise-name">${ex.name}</h3>
                <div class="exercise-stats">${stats}</div>
                ${ex.description ? `<p class="exercise-desc">${ex.description}</p>` : ''}
            </div>
        </div>
        ${statusBar}
    `;

    div.addEventListener('click', () => showExerciseDetail(ex));
    return div;
}

function buildStatusBar(log, ex) {
    if (!log || log.status === 'not_started') return '';

    const done  = log.sets_completed;
    const total = log.total_sets || ex.computed_sets || 3;
    const pct   = Math.min(100, Math.round((done / total) * 100));

    if (log.status === 'completed') {
        return `<div class="completion-bar completed">✓ Completed — ${done}/${total} sets</div>`;
    }
    return `
        <div class="completion-bar in-progress">
            <div class="completion-bar-fill" style="width:${pct}%"></div>
            <span class="completion-label">${done}/${total} sets</span>
        </div>`;
}

// ═══════════════════════════════════════════════════
// EXERCISE DETAIL
// ═══════════════════════════════════════════════════
function showExerciseDetail(ex) {
    if (!detailSection) return;

    const log        = userLogs[ex.id] || { sets_completed: 0, total_sets: ex.computed_sets || ex.get_sets, status: 'not_started' };
    const totalSets  = ex.computed_sets || 3;
    const doneSets   = log.sets_completed || 0;

    // Hero background — gradient per type if no image
    const heroStyle = ex.image
        ? `background: url('${ex.image}') center/cover no-repeat;`
        : `background: ${getTypeGradient(ex.exercise_type)};`;

    // Stats chips for detail view
    const statsChips = (ex.stats || []).map(s => `
        <div class="detail-stat">
            <span class="detail-stat-label">${s.label}</span>
            <span class="detail-stat-value">${s.value}</span>
        </div>`).join('');

    // Instructions
    const instructions = (ex.instructions_list || []).map((step, i) => `
        <li class="instruction-step">
            <span class="step-num">${i + 1}</span>
            <span>${step.replace(/^\d+\.\s*/, '')}</span>
        </li>`).join('');

    // Sets tracker circles
    const setCircles = Array.from({ length: totalSets }, (_, i) => `
        <button class="set-circle ${i < doneSets ? 'done' : ''}"
                data-set-index="${i}"
                onclick="toggleSet(${ex.id}, ${i}, ${totalSets})">
            ${i < doneSets ? '✓' : i + 1}
        </button>`).join('');

    detailSection.innerHTML = `
        <!-- Hero -->
        <div class="detail-hero" style="${heroStyle}">
            <div class="detail-hero-overlay"></div>
            <button class="back-btn detail-back" onclick="closeDetail()" aria-label="Go back"></button>
            <div class="detail-hero-content">
                <span class="level-badge ${ex.level}">${ex.level.charAt(0).toUpperCase() + ex.level.slice(1)}</span>
                <h1 class="detail-title">${ex.name}</h1>
                ${ex.muscle_group_name ? `<p class="detail-muscle">${ex.muscle_group_name}</p>` : ''}
            </div>
        </div>

        <!-- Body -->
        <div class="detail-body">

            <!-- Quick stats row -->
            <div class="detail-stats-row">
                ${statsChips}
                <div class="detail-stat">
                    <span class="detail-stat-label">Equipment</span>
                    <span class="detail-stat-value">${ex.equipment_display || 'Bodyweight'}</span>
                </div>
            </div>

            <!-- Description -->
            ${ex.description ? `
            <div class="detail-section">
                <h3 class="detail-section-title">About</h3>
                <p class="detail-description">${ex.description}</p>
            </div>` : ''}

            <!-- Instructions -->
            ${instructions ? `
            <div class="detail-section">
                <h3 class="detail-section-title">How To</h3>
                <ol class="instructions-list">${instructions}</ol>
            </div>` : ''}

            <!-- Demo Video -->
            ${ex.demo_video ? `
            <div class="detail-section">
                <h3 class="detail-section-title">Form Demo</h3>
                <div class="detail-video-wrap">
                    <video controls>
                        <source src="${ex.demo_video}" type="video/mp4">
                    </video>
                </div>
            </div>` : ''}

            <!-- Sets Tracker -->
            <div class="detail-section">
                <h3 class="detail-section-title">Sets Tracker</h3>
                <p class="sets-sub">Tap each circle as you complete the set</p>
                <div class="sets-tracker" id="sets-tracker-${ex.id}">
                    ${setCircles}
                </div>
                ${doneSets > 0 ? `
                <button class="reset-btn" onclick="resetLog(${ex.id})">↺ Reset Progress</button>` : ''}
            </div>

        </div>
    `;

    exercisesSection.style.display = 'none';
    detailSection.style.display    = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ═══════════════════════════════════════════════════
// SETS TRACKER
// ═══════════════════════════════════════════════════
async function toggleSet(exerciseId, setIndex, totalSets) {
    const log          = userLogs[exerciseId] || { sets_completed: 0 };
    let setsCompleted  = log.sets_completed;

    // Tap completed set → undo it. Tap next empty set → complete it.
    if (setIndex < setsCompleted) {
        setsCompleted = setIndex;       // undo back to this point
    } else if (setIndex === setsCompleted) {
        setsCompleted = setIndex + 1;   // complete this set
    }
    // Tapping a future set (skipping) does nothing

    setsCompleted = Math.max(0, Math.min(setsCompleted, totalSets));

    try {
        const res = await fetch(`${API_BASE}/logs/update/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ exercise_id: exerciseId, sets_completed: setsCompleted }),
        });
        const data = await res.json();

        // Update local state
        userLogs[exerciseId] = {
            sets_completed: data.sets_completed,
            total_sets: data.total_sets,
            status: data.status,
        };

        // Update circles in detail view
        updateSetCircles(exerciseId, setsCompleted, totalSets);

        // Update card in exercise list if visible
        updateExerciseCard(exerciseId);

        // Show completion animation
        if (data.status === 'completed') showCompletionToast();

    } catch (e) {
        console.error('Failed to update log:', e);
    }
}

function updateSetCircles(exerciseId, doneSets, totalSets) {
    const tracker = document.getElementById(`sets-tracker-${exerciseId}`);
    if (!tracker) return;

    tracker.querySelectorAll('.set-circle').forEach((circle, i) => {
        if (i < doneSets) {
            circle.classList.add('done');
            circle.textContent = '✓';
        } else {
            circle.classList.remove('done');
            circle.textContent = i + 1;
        }
    });

    // Show/hide reset button
    const existingReset = tracker.parentElement.querySelector('.reset-btn');
    if (doneSets > 0 && !existingReset) {
        const btn = document.createElement('button');
        btn.className = 'reset-btn';
        btn.textContent = '↺ Reset Progress';
        btn.onclick = () => resetLog(exerciseId);
        tracker.parentElement.appendChild(btn);
    } else if (doneSets === 0 && existingReset) {
        existingReset.remove();
    }
}

function updateExerciseCard(exerciseId) {
    const card = document.querySelector(`.exercise-card[data-exercise-id="${exerciseId}"]`);
    if (!card) return;

    const log = userLogs[exerciseId];
    const ex  = currentCategory?.exercises?.find(e => e.id === exerciseId);
    if (!log || !ex) return;

    // Remove old status bar
    card.querySelector('.completion-bar')?.remove();

    // Add updated status bar
    const bar = document.createElement('div');
    bar.innerHTML = buildStatusBar(log, ex);
    if (bar.firstElementChild) card.appendChild(bar.firstElementChild);
}

async function resetLog(exerciseId) {
    if (!confirm('Reset your progress for this exercise?')) return;

    try {
        const res = await fetch(`${API_BASE}/logs/${exerciseId}/reset/`, {
            method: 'DELETE',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
        });
        const data = await res.json();

        const totalSets = userLogs[exerciseId]?.total_sets || 3;
        userLogs[exerciseId] = { sets_completed: 0, total_sets: totalSets, status: 'not_started' };

        updateSetCircles(exerciseId, 0, totalSets);
        updateExerciseCard(exerciseId);
    } catch (e) {
        console.error('Failed to reset log:', e);
    }
}

function showCompletionToast() {
    const toast = document.createElement('div');
    toast.className = 'completion-toast';
    toast.innerHTML = '🎉 Exercise Complete!';
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 50);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 2500);
}

// ═══════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════
function closeExercises() {
    exercisesSection.style.display = 'none';
    dashboardSection.style.display = 'flex';
    currentCategory = null;
}

function closeDetail() {
    detailSection.style.display    = 'none';
    exercisesSection.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ═══════════════════════════════════════════════════
// SEARCH
// ═══════════════════════════════════════════════════
const searchInput = document.getElementById('search-workout');
let debounceTimer;

if (searchInput) {
    searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            const q = searchInput.value.trim();
            if (!q) { renderCategoryCards(); return; }

            fetch(`/dashboard/search/?q=${encodeURIComponent(q)}`)
                .then(r => r.json())
                .then(data => {
                    cardContainer.innerHTML = '';
                    if (!data.results || data.results.length === 0) {
                        cardContainer.innerHTML = `<div class="empty-state"><p class="empty-msg">No results for "${q}"</p></div>`;
                        return;
                    }
                    data.results.forEach((cat, i) => {
                        const full = allCategories.find(c => c.id === cat.id) || cat;
                        cardContainer.appendChild(buildCategoryCard(full, i));
                    });
                });
        }, 300);
    });
}

// ═══════════════════════════════════════════════════
// PROFILE PANEL
// ═══════════════════════════════════════════════════
const avatarBtn    = document.getElementById('avatarBtn');
const profilePanel = document.getElementById('profilePanel');

if (avatarBtn && profilePanel) {
    avatarBtn.addEventListener('click', e => {
        e.stopPropagation();
        profilePanel.style.display = profilePanel.style.display === 'block' ? 'none' : 'block';
    });
    document.addEventListener('click', e => {
        if (!profilePanel.contains(e.target) && e.target !== avatarBtn) {
            profilePanel.style.display = 'none';
        }
    });
}

const uploadBtn = document.getElementById('uploadPhotoBtn');
const fileInput = document.getElementById('profileImageInput');
if (uploadBtn && fileInput) {
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
        if (!fileInput.files.length) return;
        const fd = new FormData();
        fd.append('profile_image', fileInput.files[0]);
        fetch('/upload-profile-image/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: fd,
        }).then(r => r.json()).then(data => {
            if (data.success) {
                const img = avatarBtn.querySelector('img');
                if (img) img.src = data.image_url;
                else avatarBtn.innerHTML = `<img src="${data.image_url}" alt="Avatar">`;
            }
        });
    });
}

const backupToggle = document.getElementById('backupToggle');
if (backupToggle) {
    backupToggle.addEventListener('change', () => {
        fetch('/toggle-backup/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } });
    });
}

const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        fetch('/logout/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
            .then(() => window.location.href = '/login/');
    });
}

const deleteBtn = document.getElementById('deleteBtn');
if (deleteBtn) {
    deleteBtn.addEventListener('click', () => {
        if (!confirm('Permanently delete your account?')) return;
        fetch('/profile/delete/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
            .then(() => window.location.href = '/');
    });
}

// ═══════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════
function getCookie(name) {
    let v = null;
    document.cookie.split(';').forEach(c => {
        const t = c.trim();
        if (t.startsWith(name + '=')) v = decodeURIComponent(t.slice(name.length + 1));
    });
    return v;
}

function getTypeGradient(type) {
    const gradients = {
        strength: 'linear-gradient(135deg, #1a1a2e, #0f3460)',
        hiit:     'linear-gradient(135deg, #2d0a0a, #7b1919)',
        cardio:   'linear-gradient(135deg, #0a1a0a, #1a4a2e)',
        mobility: 'linear-gradient(135deg, #1a0f2e, #4a2d7a)',
    };
    return gradients[type] || gradients.strength;
}

function getCategoryIcon(type) {
    const icons = {
        strength: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M6.5 6.5h11M12 3v18M4 12h16"/></svg>`,
        hiit:     `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>`,
        cardio:   `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`,
        mobility: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><circle cx="12" cy="5" r="2"/><path d="m3 12 4-4 4 4 4-4 4 4M3 19l4-4 4 4 4-4 4 4"/></svg>`,
    };
    return icons[type] || icons.strength;
}