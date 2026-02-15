// Filter chips selection
const chips = document.querySelectorAll('.chip');

chips.forEach(chip => {
    chip.addEventListener('click', () => {
        // Remove selected class from all
        chips.forEach(c => c.classList.remove('selected'));
        // Add selected to clicked chip
        chip.classList.add('selected');

        const level = chip.getAttribute('data-level');
        filterCards(level);
    });
});

// Filter workout cards by data-level
function filterCards(level) {
    const cards = document.querySelectorAll('.category_card');
    cards.forEach(card => {
        if (card.getAttribute('data-level') === level) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

const searchInput = document.getElementById('search-workout');
const cardContainer = document.querySelector('.card-container');

let debounceTimer;

searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);

    debounceTimer = setTimeout(() => {
        const query = searchInput.value.trim();

        fetch(`/dashboard/search/?q=${query}`)
            .then(res => res.json())
            .then(data => {
                cardContainer.innerHTML = '';

                if (data.results.length === 0) {
                    cardContainer.innerHTML = '<p>No workouts found.</p>';
                    return;
                }

                data.results.forEach(cat => {
                    const div = document.createElement('div');
                    div.classList.add('category_card');
                    div.classList.add(cat.name.toLowerCase());

                    div.onclick = () => {
                        window.location.href = `/exercises/category${cat.id}/`;
                    };

                    div.innerHTML = `
    <div class="card-left">
        <h3>${cat.name}</h3>
        <p>${cat.total_programs} Workout Programs</p>
    </div>
    <div class="card-right">
        <img src="${cat.image}" alt="${cat.name}">
    </div>
`;


                    cardContainer.appendChild(div);
                });
            });
    }, 300); // debounce for smooth typing
});

// PROFILE AVATAR & PANEL
const avatarBtn = document.getElementById('avatarBtn');
const profilePanel = document.getElementById('profilePanel');

if (avatarBtn && profilePanel) {
    avatarBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        profilePanel.style.display =
            profilePanel.style.display === 'block' ? 'none' : 'block';
    });

    document.addEventListener('click', (e) => {
        if (!profilePanel.contains(e.target) && !avatarBtn.contains(e.target)) {
            profilePanel.style.display = 'none';
        }
    });
}

// PROFILE IMAGE UPLOAD
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
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const avatarImg = avatarBtn.querySelector('img');
                if (avatarImg) {
                    avatarImg.src = data.image_url;
                } else {
                    avatarBtn.innerHTML = `<img src="${data.image_url}" alt="Avatar">`;
                }
            }
        });
    });
}

//BACKUP REMINDER TOGGLE
const backupToggle = document.getElementById('backupToggle');

if (backupToggle) {
    backupToggle.addEventListener('change', () => {
        fetch('/toggle-backup/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
    });
}

// LOGOUT
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        fetch('/logout/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        }).then(() => {
            window.location.href = '/login/';
        });
    });
}

//DELETE ACCOUNT
const deleteBtn = document.getElementById('deleteBtn');

if (deleteBtn) {
    deleteBtn.addEventListener('click', () => {
        if (!confirm('This will permanently delete your account. Continue?')) return;

        fetch('/profile/delete/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        }).then(() => {
            window.location.href = '/';
        });
    });
}

//CSRF HELPER
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        document.cookie.split(';').forEach(cookie => {
            const c = cookie.trim();
            if (c.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(c.slice(name.length + 1));
            }
        });
    }
    return cookieValue;
}
