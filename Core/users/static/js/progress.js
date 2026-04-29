let weightChart = null;
let measurementChart = null;
let weeklyWorkoutsChart = null;
let consistencyChart = null;
let progressLoaded = false;

async function loadProgressScreen() {
    if (progressLoaded) return;
    progressLoaded = true;

    await Promise.all([
        loadConsistency(),
        loadWeightChart(),
        loadMeasurementChart(),
        loadProgressPhotos(),
    ]);
}

async function loadConsistency() {
    try {
        const res = await fetch('/api/progress/consistency/');
        const data = await res.json();

        document.getElementById('stat-streak').textContent = data.current_streak || 0;
        document.getElementById('stat-longest').textContent = data.longest_streak || 0;
        document.getElementById('stat-total').textContent = data.total_workouts || 0;
        document.getElementById('stat-this-week').textContent = data.active_this_week || 0;

        const weeklyAverage = document.getElementById('stat-weekly-average');
        if (weeklyAverage) {
            weeklyAverage.textContent = data.avg_weekly_workouts || 0;
        }

        renderConsistencyChart(data.weekly_workouts || []);

        renderWeeklyWorkoutsChart(data.weekly_workouts || []);
    } catch (e) {
        console.error('Consistency load failed:', e);
    }
}

function renderConsistencyChart(weeklyData) {
    const canvas = document.getElementById('consistency-chart');
    if (!canvas) return;

    clearChartEmpty(canvas);
    if (consistencyChart) {
        consistencyChart.destroy();
        consistencyChart = null;
    }

    if (!weeklyData.length) {
        showChartEmpty(canvas, 'No consistency data yet. Complete workouts to reveal your trend.');
        return;
    }

    consistencyChart = new Chart(canvas, {
        type: 'line',
        data: {
            labels: weeklyData.map((item) => formatChartDate(item.label)),
            datasets: [{
                label: 'Consistency',
                data: weeklyData.map((item) => item.count),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59,130,246,0.12)',
                fill: true,
                tension: 0.35,
                pointRadius: 4,
                pointBackgroundColor: '#3b82f6',
            }]
        },
        options: chartOptions('Sessions'),
    });
}

function renderWeeklyWorkoutsChart(weeklyData) {
    const canvas = document.getElementById('weekly-workouts-chart');
    if (!canvas) return;

    clearChartEmpty(canvas);
    if (weeklyWorkoutsChart) {
        weeklyWorkoutsChart.destroy();
        weeklyWorkoutsChart = null;
    }

    if (!weeklyData.length) {
        showChartEmpty(canvas, 'No workout activity yet. Complete workouts to see your weekly trend.');
        return;
    }

    weeklyWorkoutsChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: weeklyData.map((item) => formatChartDate(item.label)),
            datasets: [{
                label: 'Workouts',
                data: weeklyData.map((item) => item.count),
                backgroundColor: 'rgba(200,241,53,0.75)',
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: chartOptions('Workouts'),
    });
}

async function loadWeightChart() {
    try {
        const res = await fetch('/api/progress/weight/');
        const data = await res.json();
        const canvas = document.getElementById('weight-chart');
        if (!canvas) return;

        clearChartEmpty(canvas);
        if (weightChart) {
            weightChart.destroy();
            weightChart = null;
        }

        if (!data.length) {
            showChartEmpty(canvas, 'No weight entries yet. Log your first entry above.');
            return;
        }

        const labels = data.map((entry) => formatChartDate(entry.date));
        const values = data.map((entry) => parseFloat(entry.weight));
        const unit = data[0]?.unit || 'kg';

        weightChart = new Chart(canvas, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: `Weight (${unit})`,
                    data: values,
                    borderColor: '#c8f135',
                    backgroundColor: 'rgba(200,241,53,0.08)',
                    borderWidth: 2,
                    pointBackgroundColor: '#c8f135',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: true,
                    tension: 0.3,
                }]
            },
            options: chartOptions(`Weight (${unit})`),
        });
    } catch (e) {
        console.error('Weight chart failed:', e);
    }
}

async function loadMeasurementChart() {
    try {
        const res = await fetch('/api/progress/measurements/');
        const data = await res.json();
        const canvas = document.getElementById('measurement-chart');
        if (!canvas) return;

        clearChartEmpty(canvas);
        if (measurementChart) {
            measurementChart.destroy();
            measurementChart = null;
        }

        if (!data.length) {
            showChartEmpty(canvas, 'No measurements yet. Log your first entry above.');
            return;
        }

        const unit = data[0]?.unit || 'cm';
        const fields = ['waist', 'hips', 'chest', 'arms', 'thighs'];
        const latest = data[data.length - 1];
        measurementChart = new Chart(canvas, {
            type: 'radar',
            data: {
                labels: fields.map((field) => field.charAt(0).toUpperCase() + field.slice(1)),
                datasets: [{
                    label: `Latest (${unit})`,
                    data: fields.map((field) => latest[field] ? parseFloat(latest[field]) : 0),
                    borderColor: '#0f766e',
                    backgroundColor: 'rgba(15,118,110,0.18)',
                    pointBackgroundColor: '#0f766e',
                    borderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { display: false } },
                scales: {
                    r: {
                        angleLines: { color: 'rgba(255,255,255,0.08)' },
                        grid: { color: 'rgba(255,255,255,0.08)' },
                        pointLabels: { color: '#a0a0a0', font: { family: 'Barlow', size: 11 } },
                        ticks: { color: '#a0a0a0', backdropColor: 'transparent' },
                    },
                },
            },
        });
    } catch (e) {
        console.error('Measurement chart failed:', e);
    }
}

async function loadProgressPhotos() {
    try {
        const res = await fetch('/api/progress/photos/');
        const photos = await res.json();
        const grid = document.getElementById('photos-grid');
        if (!grid) return;

        renderBeforeAfterComparison(photos);
        grid.querySelectorAll('.photo-card').forEach((card) => card.remove());

        photos.forEach((photo) => {
            const card = document.createElement('div');
            card.className = 'photo-card';
            card.innerHTML = `
                <img src="${photo.image_url}" alt="${photo.label}">
                <span class="photo-card-label ${photo.label}">${photo.label}</span>
            `;
            card.addEventListener('click', () => showPhotoFullscreen(photo));
            grid.insertBefore(card, grid.querySelector('.add-photo-btn'));
        });
    } catch (e) {
        console.error('Photos load failed:', e);
    }
}

function renderBeforeAfterComparison(photos) {
    const beforeCard = document.getElementById('before-photo-card');
    const afterCard = document.getElementById('after-photo-card');
    if (!beforeCard || !afterCard) return;

    const beforePhoto = photos.find((photo) => photo.label === 'before');
    const afterPhoto = photos.find((photo) => photo.label === 'after');

    fillComparisonCard(beforeCard, 'Before', beforePhoto, 'Upload your starting photo.');
    fillComparisonCard(afterCard, 'After', afterPhoto, 'Upload your latest photo.');
}

function fillComparisonCard(card, title, photo, emptyText) {
    if (!photo) {
        card.innerHTML = `
            <div class="comparison-label">${title}</div>
            <div class="comparison-photo-empty">${emptyText}</div>
        `;
        card.onclick = null;
        return;
    }

    card.innerHTML = `
        <div class="comparison-label">${title}</div>
        <img class="comparison-photo" src="${photo.image_url}" alt="${title}">
        <div class="comparison-meta">
            <span>${formatChartDate(photo.date)}</span>
            ${photo.note ? `<span>${photo.note}</span>` : ''}
        </div>
    `;
    card.onclick = () => showPhotoFullscreen(photo);
}

function openLogModal(type) {
    const modal = document.getElementById(`${type}-modal`);
    if (modal) modal.classList.add('show');
}

function closeLogModal(type) {
    const modal = document.getElementById(`${type}-modal`);
    if (modal) modal.classList.remove('show');
}

async function submitWeightLog(e) {
    e.preventDefault();
    const form = e.target;
    const payload = {
        weight: form.querySelector('[name=weight]').value,
        unit: form.querySelector('[name=unit]').value,
        note: form.querySelector('[name=note]')?.value || '',
        date: form.querySelector('[name=date]').value || new Date().toISOString().split('T')[0],
    };

    try {
        await fetch('/api/progress/weight/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify(payload),
        });
        closeLogModal('weight');
        progressLoaded = false;
        loadProgressScreen();
        showToast('Weight logged!');
    } catch (e) {
        console.error(e);
    }
}

async function submitMeasurementLog(e) {
    e.preventDefault();
    const form = e.target;
    const payload = {
        unit: form.querySelector('[name=unit]').value,
        waist: form.querySelector('[name=waist]').value || null,
        hips: form.querySelector('[name=hips]').value || null,
        chest: form.querySelector('[name=chest]').value || null,
        arms: form.querySelector('[name=arms]').value || null,
        thighs: form.querySelector('[name=thighs]').value || null,
        date: form.querySelector('[name=date]').value || new Date().toISOString().split('T')[0],
    };

    try {
        await fetch('/api/progress/measurements/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify(payload),
        });
        closeLogModal('measurement');
        progressLoaded = false;
        loadProgressScreen();
        showToast('Measurements logged!');
    } catch (e) {
        console.error(e);
    }
}

async function submitStrengthLog(e) {
    e.preventDefault();
    const form = e.target;
    const payload = {
        exercise: form.querySelector('[name=exercise]').value,
        weight_lifted: form.querySelector('[name=weight_lifted]').value,
        weight_unit: form.querySelector('[name=weight_unit]').value,
        reps: form.querySelector('[name=reps]').value,
        note: form.querySelector('[name=note]')?.value || '',
        date: form.querySelector('[name=date]').value || new Date().toISOString().split('T')[0],
    };

    try {
        await fetch('/api/progress/strength/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify(payload),
        });
        closeLogModal('strength');
        progressLoaded = false;
        loadProgressScreen();
        showToast('Strength logged!');
    } catch (e) {
        console.error(e);
    }
}

async function submitPhotoUpload(e) {
    e.preventDefault();
    const form = e.target;
    const file = form.querySelector('[name=image]').files[0];
    if (!file) return;

    const fd = new FormData();
    fd.append('image', file);
    fd.append('label', form.querySelector('[name=label]').value);
    fd.append('note', form.querySelector('[name=note]')?.value || '');
    fd.append('date', form.querySelector('[name=date]').value || new Date().toISOString().split('T')[0]);

    try {
        await fetch('/api/progress/photos/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: fd,
        });
        closeLogModal('photo');
        progressLoaded = false;
        loadProgressScreen();
        showToast('Photo uploaded!');
    } catch (e) {
        console.error(e);
    }
}

function formatChartDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
}

function chartOptions(yLabel) {
    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: '#181818',
                borderColor: '#2a2a2a',
                borderWidth: 1,
                titleColor: '#ffffff',
                bodyColor: '#a0a0a0',
                titleFont: { family: 'Barlow Condensed', size: 14, weight: 700 },
                bodyFont: { family: 'Barlow', size: 12 },
                padding: 10,
            },
        },
        scales: {
            x: {
                grid: { color: 'rgba(255,255,255,0.04)' },
                ticks: { color: '#a0a0a0', font: { family: 'Barlow', size: 11 } },
            },
            y: {
                grid: { color: 'rgba(255,255,255,0.04)' },
                ticks: { color: '#a0a0a0', font: { family: 'Barlow', size: 11 } },
                title: { display: !!yLabel, text: yLabel, color: '#a0a0a0', font: { family: 'Barlow', size: 11 } },
                beginAtZero: true,
            },
        },
    };
}

function clearChartEmpty(canvas) {
    canvas.parentElement.querySelectorAll('.chart-empty').forEach((node) => node.remove());
}

function showChartEmpty(canvas, message) {
    clearChartEmpty(canvas);
    const empty = document.createElement('p');
    empty.className = 'chart-empty';
    empty.textContent = message;
    canvas.parentElement.appendChild(empty);
}

function showPhotoFullscreen(photo) {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position:fixed;inset:0;background:rgba(0,0,0,0.92);
        display:flex;align-items:center;justify-content:center;
        z-index:500;cursor:pointer;padding:20px;
    `;
    overlay.innerHTML = `<img src="${photo.image_url}" style="max-width:100%;max-height:90vh;border-radius:12px;object-fit:contain;">`;
    overlay.addEventListener('click', () => overlay.remove());
    document.body.appendChild(overlay);
}

function showToast(msg) {
    const t = document.createElement('div');
    t.className = 'completion-toast';
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.classList.add('show'), 50);
    setTimeout(() => {
        t.classList.remove('show');
        setTimeout(() => t.remove(), 400);
    }, 2500);
}

async function populateStrengthSelect() {
    const select = document.getElementById('strength-exercise-select');
    if (!select || select.children.length > 1) return;

    try {
        const res = await fetch('/api/exercises/');
        const data = await res.json();
        data.results?.forEach((exercise) => {
            const opt = document.createElement('option');
            opt.value = exercise.id;
            opt.textContent = `${exercise.name} (${exercise.level})`;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('Exercise select populate failed:', e);
    }
}
