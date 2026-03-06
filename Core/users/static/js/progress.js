// ═══════════════════════════════════════════════════
// PROGRESS SCREEN
// ═══════════════════════════════════════════════════

let weightChart       = null;
let measurementChart  = null;
let strengthChart     = null;
let progressLoaded    = false;

async function loadProgressScreen() {
    if (progressLoaded) return;   // don't re-fetch if already loaded
    progressLoaded = false;       // always refresh on visit

    await Promise.all([
        loadConsistency(),
        loadWeightChart(),
        loadMeasurementChart(),
        loadStrengthChart(),
        loadProgressPhotos(),
    ]);
}

// ── CONSISTENCY HEATMAP ──────────────────────────

async function loadConsistency() {
    try {
        const res  = await fetch('/api/progress/consistency/');
        const data = await res.json();

        // Update stat cards
        document.getElementById('stat-streak').textContent      = data.current_streak || 0;
        document.getElementById('stat-longest').textContent     = data.longest_streak || 0;
        document.getElementById('stat-total').textContent       = data.total_workouts || 0;
        document.getElementById('stat-this-week').textContent   = data.active_this_week || 0;

        // Build heatmap
        const grid = document.getElementById('heatmap-grid');
        if (!grid) return;
        grid.innerHTML = '';

        const today = new Date().toISOString().split('T')[0];

        data.weeks.forEach(week => {
            const col = document.createElement('div');
            col.className = 'heatmap-week';
            week.forEach(day => {
                const cell = document.createElement('div');
                cell.className = `heatmap-day${day.active ? ' active' : ''}${day.date === today ? ' today' : ''}`;
                cell.title = `${day.date}${day.count ? ` — ${day.count} exercises` : ''}`;
                col.appendChild(cell);
            });
            grid.appendChild(col);
        });

    } catch (e) {
        console.error('Consistency load failed:', e);
    }
}

// ── WEIGHT CHART ──────────────────────────────────

async function loadWeightChart() {
    try {
        const res  = await fetch('/api/progress/weight/');
        const data = await res.json();

        const canvas = document.getElementById('weight-chart');
        if (!canvas) return;

        // Destroy existing
        if (weightChart) { weightChart.destroy(); weightChart = null; }

        if (!data.length) {
            canvas.parentElement.innerHTML += '<p class="chart-empty">No weight entries yet. Log your first entry above.</p>';
            return;
        }

        const labels = data.map(d => formatChartDate(d.date));
        const values = data.map(d => parseFloat(d.weight));
        const unit   = data[0]?.unit || 'kg';

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

// ── MEASUREMENTS CHART ────────────────────────────

async function loadMeasurementChart() {
    try {
        const res  = await fetch('/api/progress/measurements/');
        const data = await res.json();

        const canvas = document.getElementById('measurement-chart');
        if (!canvas) return;

        if (measurementChart) { measurementChart.destroy(); measurementChart = null; }

        if (!data.length) {
            canvas.parentElement.innerHTML += '<p class="chart-empty">No measurements yet. Log your first entry above.</p>';
            return;
        }

        const labels  = data.map(d => formatChartDate(d.date));
        const unit    = data[0]?.unit || 'cm';
        const fields  = ['waist', 'hips', 'chest', 'arms', 'thighs'];
        const colors  = ['#c8f135', '#f97316', '#3b82f6', '#a855f7', '#ff3b3b'];

        const datasets = fields.map((field, i) => ({
            label: field.charAt(0).toUpperCase() + field.slice(1),
            data:  data.map(d => d[field] ? parseFloat(d[field]) : null),
            borderColor: colors[i],
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 3,
            tension: 0.3,
            spanGaps: true,
        }));

        measurementChart = new Chart(canvas, {
            type: 'line',
            data: { labels, datasets },
            options: chartOptions(`Measurements (${unit})`),
        });

    } catch (e) {
        console.error('Measurement chart failed:', e);
    }
}

// ── STRENGTH CHART ────────────────────────────────

async function loadStrengthChart() {
    try {
        const res  = await fetch('/api/progress/strength/summary/');
        const data = await res.json();

        const canvas = document.getElementById('strength-chart');
        if (!canvas) return;

        if (strengthChart) { strengthChart.destroy(); strengthChart = null; }

        if (!data.length) {
            canvas.parentElement.innerHTML += '<p class="chart-empty">No strength logs yet. Complete exercises to auto-log, or add manually above.</p>';
            return;
        }

        const colors = ['#c8f135', '#f97316', '#3b82f6', '#a855f7', '#ff3b3b'];

        const allDates = [...new Set(data.flatMap(ex => ex.data.map(d => d.date)))].sort();
        const labels   = allDates.map(d => formatChartDate(d));

        const datasets = data.map((ex, i) => ({
            label: ex.exercise,
            data:  allDates.map(date => {
                const entry = ex.data.find(d => d.date === date);
                return entry ? entry.weight : null;
            }),
            borderColor: colors[i % colors.length],
            backgroundColor: 'transparent',
            borderWidth: 2,
            pointRadius: 3,
            tension: 0.3,
            spanGaps: true,
        }));

        strengthChart = new Chart(canvas, {
            type: 'line',
            data: { labels, datasets },
            options: {
                ...chartOptions('Weight Lifted (kg)'),
                plugins: {
                    ...chartOptions('').plugins,
                    legend: {
                        display: true,
                        labels: {
                            color: '#a0a0a0',
                            font: { family: 'Barlow', size: 11 },
                            boxWidth: 12,
                        }
                    }
                }
            },
        });

    } catch (e) {
        console.error('Strength chart failed:', e);
    }
}

// ── PROGRESS PHOTOS ───────────────────────────────

async function loadProgressPhotos() {
    try {
        const res    = await fetch('/api/progress/photos/');
        const photos = await res.json();
        const grid   = document.getElementById('photos-grid');
        if (!grid) return;

        // Keep the add button, remove old photo cards
        grid.querySelectorAll('.photo-card').forEach(c => c.remove());

        photos.forEach(photo => {
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

// ═══════════════════════════════════════════════════
// LOG MODALS
// ═══════════════════════════════════════════════════

function openLogModal(type) {
    const modal = document.getElementById(`${type}-modal`);
    if (modal) modal.classList.add('show');
}

function closeLogModal(type) {
    const modal = document.getElementById(`${type}-modal`);
    if (modal) modal.classList.remove('show');
}

// Weight log submit
async function submitWeightLog(e) {
    e.preventDefault();
    const form   = e.target;
    const weight = form.querySelector('[name=weight]').value;
    const unit   = form.querySelector('[name=unit]').value;
    const note   = form.querySelector('[name=note]')?.value || '';
    const date   = form.querySelector('[name=date]').value || new Date().toISOString().split('T')[0];

    try {
        await fetch('/api/progress/weight/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ weight, unit, note, date }),
        });
        closeLogModal('weight');
        progressLoaded = false;
        loadWeightChart();
        showToast('Weight logged!');
    } catch (e) {
        console.error(e);
    }
}

// Measurement log submit
async function submitMeasurementLog(e) {
    e.preventDefault();
    const form = e.target;
    const data = {
        unit:   form.querySelector('[name=unit]').value,
        waist:  form.querySelector('[name=waist]').value || null,
        hips:   form.querySelector('[name=hips]').value || null,
        chest:  form.querySelector('[name=chest]').value || null,
        arms:   form.querySelector('[name=arms]').value || null,
        thighs: form.querySelector('[name=thighs]').value || null,
        date:   form.querySelector('[name=date]').value || new Date().toISOString().split('T')[0],
    };

    try {
        await fetch('/api/progress/measurements/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify(data),
        });
        closeLogModal('measurement');
        progressLoaded = false;
        loadMeasurementChart();
        showToast('Measurements logged!');
    } catch (e) {
        console.error(e);
    }
}

// Strength log submit
async function submitStrengthLog(e) {
    e.preventDefault();
    const form = e.target;
    const data = {
        exercise:      form.querySelector('[name=exercise]').value,
        weight_lifted: form.querySelector('[name=weight_lifted]').value,
        weight_unit:   form.querySelector('[name=weight_unit]').value,
        reps:          form.querySelector('[name=reps]').value,
        note:          form.querySelector('[name=note]')?.value || '',
        date:          form.querySelector('[name=date]').value || new Date().toISOString().split('T')[0],
    };

    try {
        await fetch('/api/progress/strength/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify(data),
        });
        closeLogModal('strength');
        progressLoaded = false;
        loadStrengthChart();
        showToast('Strength logged!');
    } catch (e) {
        console.error(e);
    }
}

// Photo upload
async function submitPhotoUpload(e) {
    e.preventDefault();
    const form  = e.target;
    const file  = form.querySelector('[name=image]').files[0];
    if (!file) return;

    const fd = new FormData();
    fd.append('image', file);
    fd.append('label', form.querySelector('[name=label]').value);
    fd.append('note',  form.querySelector('[name=note]')?.value || '');
    fd.append('date',  form.querySelector('[name=date]').value || new Date().toISOString().split('T')[0]);

    try {
        await fetch('/api/progress/photos/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') },
            body: fd,
        });
        closeLogModal('photo');
        loadProgressPhotos();
        showToast('Photo uploaded!');
    } catch (e) {
        console.error(e);
    }
}

// ═══════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════

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
                bodyFont:  { family: 'Barlow', size: 12 },
                padding: 10,
            },
        },
        scales: {
            x: {
                grid:  { color: 'rgba(255,255,255,0.04)' },
                ticks: { color: '#a0a0a0', font: { family: 'Barlow', size: 11 } },
            },
            y: {
                grid:  { color: 'rgba(255,255,255,0.04)' },
                ticks: { color: '#a0a0a0', font: { family: 'Barlow', size: 11 } },
                title: { display: !!yLabel, text: yLabel, color: '#a0a0a0', font: { family: 'Barlow', size: 11 } },
            },
        },
    };
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
    setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 400); }, 2500);
}

// Populate strength exercise select
async function populateStrengthSelect() {
    const select = document.getElementById('strength-exercise-select');
    if (!select || select.children.length > 1) return;

    try {
        const res  = await fetch('/api/exercises/');
        const data = await res.json();
        data.results?.forEach(ex => {
            const opt = document.createElement('option');
            opt.value = ex.id;
            opt.textContent = `${ex.name} (${ex.level})`;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error('Exercise select populate failed:', e);
    }
}