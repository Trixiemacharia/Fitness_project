// ===== FILTER CHIPS =====
const chips = document.querySelectorAll('.chip');
let activeLevel = document.body.getAttribute('data-fitness-level') || 'beginner';

chips.forEach(chip => {
    chip.addEventListener('click', () => {
        chips.forEach(c => c.classList.remove('selected'));
        chip.classList.add('selected');
        activeLevel = chip.getAttribute('data-level');

        // If exercises section is open, re-render with new level instantly
        if (exercisesSection && exercisesSection.style.display === 'block' && currentCategory) {
            renderExercises(currentCategory.exercises, activeLevel);
        }
    });
});

// ===== SEARCH =====
const searchInput = document.getElementById('search-workout');
const cardContainer = document.querySelector('.card-container');
let debounceTimer;

searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        const query = searchInput.value.trim();
        if (!query) { hydrateCategories(); return; }

        fetch(`/dashboard/search/?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                cardContainer.innerHTML = '';
                if (data.results.length === 0) {
                    cardContainer.innerHTML = '<p>No workouts found.</p>';
                    return;
                }
                data.results.forEach(cat => {
                    const div = document.createElement('div');
                    div.className = `category-card ${cat.name.toLowerCase()}`;
                    div.innerHTML = `
                        <div class="card-left">
                            <h3>${cat.name}</h3>
                            <p class="program-count">${cat.exercises ? cat.exercises.length : 0} Workout Programs</p>
                            ${cat.description ? `<p class="card-desc">${cat.description}</p>` : ''}
                        </div>
                        <div class="card-right">
                            ${cat.image ? `<img src="${cat.image}" alt="${cat.name}">` : ''}
                        </div>
                    `;
                    const fullCategory = allCategories.find(c => c.id === cat.id);
                    div.addEventListener('click', () => { if (fullCategory) showExercises(fullCategory); });
                    cardContainer.appendChild(div);
                });
            });
    }, 300);
});

// ===== PROFILE AVATAR & PANEL =====
const avatarBtn = document.getElementById('avatarBtn');
const profilePanel = document.getElementById('profilePanel');

if (avatarBtn && profilePanel) {
    avatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        profilePanel.style.display = profilePanel.style.display === 'block' ? 'none' : 'block';
    });
    document.addEventListener('click', (e) => {
        if (!profilePanel.contains(e.target) && !avatarBtn.contains(e.target)) {
            profilePanel.style.display = 'none';
        }
    });
}

// ===== PROFILE IMAGE UPLOAD =====
const uploadBtn = document.getElementById('uploadPhotoBtn');
const fileInput = document.getElementById('profileImageInput');

if (uploadBtn && fileInput) {
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
        if (!fileInput.files.length) return;
        const formData = new FormData();
        formData.append('profile_image', fileInput.files[0]);
        fetch('/upload-profile-image/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const avatarImg = avatarBtn.querySelector('img');
                if (avatarImg) avatarImg.src = data.image_url;
                else avatarBtn.innerHTML = `<img src="${data.image_url}" alt="Avatar">`;
            }
        });
    });
}

// ===== BACKUP TOGGLE =====
const backupToggle = document.getElementById('backupToggle');
if (backupToggle) {
    backupToggle.addEventListener('change', () => {
        fetch('/toggle-backup/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } });
    });
}

// ===== LOGOUT =====
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        fetch('/logout/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
            .then(() => { window.location.href = '/login/'; });
    });
}

// ===== DELETE ACCOUNT =====
const deleteBtn = document.getElementById('deleteBtn');
if (deleteBtn) {
    deleteBtn.addEventListener('click', () => {
        if (!confirm('This will permanently delete your account. Continue?')) return;
        fetch('/profile/delete/', { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } })
            .then(() => { window.location.href = '/'; });
    });
}

// ===== CSRF HELPER =====
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        document.cookie.split(';').forEach(cookie => {
            const c = cookie.trim();
            if (c.startsWith(name + '=')) cookieValue = decodeURIComponent(c.slice(name.length + 1));
        });
    }
    return cookieValue;
}

// ===== SPA CORE =====
const API_BASE = 'http://127.0.0.1:8000/api';
const dashboardSection = document.getElementById('dashboard');
const exercisesSection = document.getElementById('exercises-section');
const exercisesList = document.getElementById('exercises-list');
const categoryTitle = document.getElementById('category-title');

let allCategories = [];
let currentCategory = null;

async function hydrateCategories() {
    try {
        const res = await fetch(`${API_BASE}/categories/`);
        allCategories = await res.json();

        const cards = document.querySelectorAll('.category-card');
        cards.forEach((card, index) => {
            const id = parseInt(card.getAttribute('data-id'));
            const category = allCategories.find(c => c.id === id);
            if (!category) return;

            const p = card.querySelector('.program-count');
            if (p) p.textContent = `${category.exercises.length} Workout Programs`;

            const freshCard = card.cloneNode(true);
            card.parentNode.replaceChild(freshCard, card);
            freshCard.style.opacity = '0';
            freshCard.style.animation = `fadeIn 0.4s ease-out ${index * 0.08}s forwards`;

            freshCard.addEventListener('touchstart', function () { this.style.transform = 'translateY(-2px)'; });
            freshCard.addEventListener('touchend', function () { this.style.transform = ''; });
            freshCard.addEventListener('click', () => showExercises(category));
        });

    } catch (error) {
        console.error("Hydration failed:", error);
    }
}

// ===== SHOW EXERCISES — no level tabs, uses activeLevel from top chip =====
function showExercises(category) {
    currentCategory = category;
    categoryTitle.textContent = category.name;
    renderExercises(category.exercises, activeLevel);

    dashboardSection.style.display = 'none';
    exercisesSection.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderExercises(exercises, level) {
    exercisesList.innerHTML = '';

    const filtered = exercises.filter(ex => ex.level === level);

    if (filtered.length === 0) {
        exercisesList.innerHTML = `
            <div class="empty-state">
                <p class="empty-msg">No ${level} exercises in this category yet.</p>
            </div>`;
        return;
    }

    filtered.forEach((ex, index) => {
        const exCard = document.createElement('div');
        exCard.className = 'exercise-card';
        exCard.style.opacity = '0';
        exCard.style.animation = `fadeIn 0.4s ease-out ${index * 0.08}s forwards`;

        // Left side: video if available, else image
        let leftSide = '';
        if (ex.demo_video) {
            leftSide = `
                <div class="exercise-video-side">
                    <video controls>
                        <source src="${ex.demo_video}" type="video/mp4">
                    </video>
                </div>`;
        } else if (ex.image) {
            leftSide = `
                <div class="exercise-img-side">
                    <img src="${ex.image}" alt="${ex.name}">
                </div>`;
        }

        exCard.innerHTML = `
            <div class="exercise-card-inner">
                ${leftSide}
                <div class="exercise-body">
                    <span class="level-badge ${ex.level}">${ex.level.charAt(0).toUpperCase() + ex.level.slice(1)}</span>
                    <h3 class="exercise-name">${ex.name}</h3>
                    <div class="exercise-stats">
                        <div class="stat-item">
                            <span class="stat-label">Sets</span>
                            <span class="stat-value">${ex.sets}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Reps</span>
                            <span class="stat-value">${ex.reps}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Weight</span>
                            <span class="stat-value">${ex.weight || 'Bodyweight'}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Rest</span>
                            <span class="stat-value">${ex.rest_time_display}</span>
                        </div>
                    </div>
                    <p class="exercise-desc">${ex.description || ''}</p>
                </div>
            </div>
        `;

        exercisesList.appendChild(exCard);
    });
}

function closeExercises() {
    exercisesSection.style.display = 'none';
    dashboardSection.style.display = 'flex';
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', async () => {
    await hydrateCategories();

    // Highlight chip matching user's fitness level
    const matchingChip = document.querySelector(`.chip[data-level="${activeLevel}"]`);
    if (matchingChip) {
        chips.forEach(c => c.classList.remove('selected'));
        matchingChip.classList.add('selected');
    }
});

window.addEventListener('popstate', () => {
    exercisesSection.style.display = 'none';
    dashboardSection.style.display = 'flex';
});