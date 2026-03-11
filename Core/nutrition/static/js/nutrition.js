const Nutrition = (() => {

    // ─── State ────────────────────────────────────
    let currentDate  = todayStr();
    let selectedFood = null;
    let selectedMT   = 'breakfast';
    let waterCount   = 0;
    const WATER_MAX  = 8;
    const GOALS      = { calories: 2200, protein: 150, carbs: 250, fats: 70 };

    let searchTimer  = null;
    let ringChart    = null;   // Chart.js doughnut
    let barChart     = null;   // Chart.js bar
    let bound        = false;  // prevent duplicate event listeners

    // ─── Shorthand ────────────────────────────────
    const el = id => document.getElementById(id);

    // ─── CSRF helper ──────────────────────────────
    // Reads csrftoken from cookie — required for Django POST/DELETE
    function csrf() {
        const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return m ? m[1] : '';
    }

    // ─── Date helpers ─────────────────────────────
    function todayStr() {
        // Returns YYYY-MM-DD in local time (not UTC)
        const d = new Date();
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        return `${y}-${m}-${day}`;
    }

    function setDate(dateStr) {
        currentDate = dateStr;
        // Sync all date inputs
        if (el('nutr-date-picker'))  el('nutr-date-picker').value  = dateStr;
        if (el('nutr-entry-date'))   el('nutr-entry-date').value   = dateStr;
        // Update the label text
        const lbl = el('nutr-date-label');
        if (!lbl) return;
        if (dateStr === todayStr()) {
            lbl.textContent = 'Today';
        } else {
            const d = new Date(dateStr + 'T00:00:00');
            lbl.textContent = d.toLocaleDateString('en-KE', {
                weekday: 'short', month: 'short', day: 'numeric'
            });
        }
    }

    function shiftDate(days) {
        const d = new Date(currentDate + 'T00:00:00');
        d.setDate(d.getDate() + days);
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const dy = String(d.getDate()).padStart(2, '0');
        setDate(`${y}-${m}-${dy}`);
        refreshAll();
    }

    function cap(s) {
        return s ? s[0].toUpperCase() + s.slice(1) : '';
    }

    function init() {
        setDate(currentDate);           // sync label + inputs
        buildGlasses();                 // render water glasses

        if (!bound) {
            bindAll();
            bound = true;
        }

        refreshAll();                   // load data from API
    }

    // ─── Bind all events ONCE ────────────────────
    function bindAll() {

        // ← prev day
        el('nutr-prev-day')?.addEventListener('click', () => shiftDate(-1));
        // → next day
        el('nutr-next-day')?.addEventListener('click', () => shiftDate(+1));

        // Calendar picker (hidden date input behind the label)
        el('nutr-date-picker')?.addEventListener('change', e => {
            if (e.target.value) {
                setDate(e.target.value);
                refreshAll();
            }
        });

        // Entry date field (inside the form) — also navigates view
        el('nutr-entry-date')?.addEventListener('change', e => {
            if (e.target.value) {
                setDate(e.target.value);
                refreshAll();
            }
        });

        // Food search input (debounced)
        el('nutr-food-input')?.addEventListener('input', () => {
            clearTimeout(searchTimer);
            const q = el('nutr-food-input').value.trim();
            if (q.length < 2) { closeDropdown(); return; }
            showSpinner(true);
            searchTimer = setTimeout(() => searchFood(q), 320);
        });

        // Hide dropdown on outside click
        document.addEventListener('click', e => {
            if (!e.target.closest('#nutr-food-input') &&
                !e.target.closest('#nutr-dropdown')) {
                closeDropdown();
            }
        });

        // Clear selected food
        el('nutr-chip-clear')?.addEventListener('click', clearFood);

        // Meal type selector
        document.querySelectorAll('.nutr-mt').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.nutr-mt').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedMT = btn.dataset.mt;
            });
        });

        // Portion input → re-validate
        el('nutr-portion')?.addEventListener('input', validateForm);

        // Log meal button
        el('nutr-submit')?.addEventListener('click', logMeal);
    }

    // ─── Refresh all data ─────────────────────────
    function refreshAll() {
        fetchSummary();
        fetchLogs();
        fetchWeekly();
    }

    // ─── Food search ──────────────────────────────
    function searchFood(q) {
        fetch(`/api/nutrition/foods/?q=${encodeURIComponent(q)}`, {
            method: 'GET',
            credentials: 'same-origin',           // sends session cookie
            headers: { 'X-CSRFToken': csrf() }
        })
        .then(r => {
            showSpinner(false);
            if (!r.ok) throw new Error(r.status);
            return r.json();
        })
        .then(items => renderDropdown(items))
        .catch(err => {
            showSpinner(false);
            console.error('Food search failed:', err);
        });
    }

    function renderDropdown(items) {
        const box = el('nutr-dropdown');
        if (!box) return;

        if (!items.length) {
            box.innerHTML = `<div class="nutr-dd-empty">No results — try "ugali", "sukuma" or "tilapia"</div>`;
        } else {
            box.innerHTML = items.map((f, i) => `
                <div class="nutr-dd-item" data-i="${i}">
                    <div>
                        <div class="nutr-dd-name">${f.name}</div>
                        <div class="nutr-dd-meta">${cap(f.category)} · ${f.default_serving_size}${f.serving_unit}</div>
                    </div>
                    <div class="nutr-dd-cal">${f.calories_per_100g} kcal
                        <br><small style="color:var(--grey-2);font-size:9px">per 100g</small>
                    </div>
                </div>`).join('');

            box.querySelectorAll('.nutr-dd-item').forEach(row => {
                row.addEventListener('click', () => {
                    pickFood(items[+row.dataset.i]);
                });
            });
        }
        box.style.display = 'block';
    }

    function closeDropdown() {
        const box = el('nutr-dropdown');
        if (box) box.style.display = 'none';
    }

    function showSpinner(on) {
        const s = el('nutr-spinner');
        if (s) s.style.display = on ? 'block' : 'none';
    }

    function pickFood(food) {
        selectedFood = food;
        closeDropdown();

        if (el('nutr-food-input')) el('nutr-food-input').value = food.name;

        // Populate chip
        if (el('nutr-chip-name')) el('nutr-chip-name').textContent = food.name;
        if (el('nc-cal'))  el('nc-cal').textContent  = `${food.calories_per_100g} kcal`;
        if (el('nc-prot')) el('nc-prot').textContent = `${food.protein_per_100g}g P`;
        if (el('nc-carb')) el('nc-carb').textContent = `${food.carbs_per_100g}g C`;
        if (el('nc-fat'))  el('nc-fat').textContent  = `${food.fats_per_100g}g F`;

        const chip = el('nutr-food-chip');
        if (chip) chip.style.display = 'block';

        if (el('nutr-portion')) el('nutr-portion').value = food.default_serving_size;
        validateForm();
    }

    function clearFood() {
        selectedFood = null;
        if (el('nutr-food-input')) el('nutr-food-input').value = '';
        const chip = el('nutr-food-chip');
        if (chip) chip.style.display = 'none';
        validateForm();
    }

    function validateForm() {
        const portion = parseFloat(el('nutr-portion')?.value);
        const ok = selectedFood && portion > 0 && el('nutr-entry-date')?.value;
        const btn = el('nutr-submit');
        if (btn) btn.disabled = !ok;
    }

    //LOG MEAL
    function logMeal() {
        if (!selectedFood) return;

        const portion = parseFloat(el('nutr-portion').value);
        const date    = el('nutr-entry-date').value;
        if (!portion || portion <= 0 || !date) return;

        const btn = el('nutr-submit');
        if (btn) { btn.disabled = true; btn.textContent = 'Saving…'; }

        const body = JSON.stringify({
            food_item:    selectedFood.id,
            date:         date,
            meal_type:    selectedMT,
            portion_size: portion,
            notes:        ''
        });

        fetch('/api/nutrition/logs/', {
            method: 'POST',
            credentials: 'same-origin',           // ← sends Django session cookie
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf()              // ← required by Django CSRF middleware
            },
            body
        })
        .then(r => {
            if (!r.ok) {
                // Surface the error details for debugging
                return r.json().then(detail => {
                    console.error('Server rejected log:', detail);
                    throw new Error(JSON.stringify(detail));
                });
            }
            return r.json();
        })
        .then(saved => {
            // ✅ Successfully saved — update UI
            toast('Meal logged successfully!!', false);

            // Reset form
            clearFood();
            if (el('nutr-portion')) el('nutr-portion').value = '';
            if (btn) { btn.disabled = true; btn.textContent = '+ Log Meal'; }

            // Pull fresh data from DB
            fetchSummary();
            fetchLogs();
            fetchWeekly();
        })
        .catch(err => {
            console.error('logMeal error:', err);
            toast('Could not save meal — check console', true);
            if (btn) { btn.disabled = false; btn.textContent = '+ Log Meal'; }
        });
    }

    // ─── DELETE LOG ENTRY ─────────────────────────
    function deleteEntry(id) {
        if (!confirm('Remove this meal entry?')) return;
        fetch(`/api/nutrition/logs/${id}/`, {
            method: 'DELETE',
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': csrf() }
        })
        .then(r => {
            if (r.ok || r.status === 204) {
                toast('Entry removed', false);
                fetchSummary();
                fetchLogs();
                fetchWeekly();
            } else {
                toast('Could not remove entry', true);
            }
        })
        .catch(() => toast('Delete failed', true));
    }

    // ─── FETCH DAILY SUMMARY → ring ───────────────
    function fetchSummary() {
        fetch(`/api/nutrition/summary/?date=${currentDate}`, {
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': csrf() }
        })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(d => {
            // Animate calorie counter
            animNum('nutr-cal-val', d.total_calories);

            // Update macro pills
            if (el('nutr-prot-val')) el('nutr-prot-val').textContent = d.total_protein.toFixed(1) + 'g';
            if (el('nutr-carb-val')) el('nutr-carb-val').textContent = d.total_carbs.toFixed(1)   + 'g';
            if (el('nutr-fat-val'))  el('nutr-fat-val').textContent  = d.total_fats.toFixed(1)    + 'g';

            // Update dynamic doughnut ring
            updateRing(d.total_protein, d.total_carbs, d.total_fats);
        })
        .catch(e => console.warn('fetchSummary error', e));
    }

    // ─── ANIMATED NUMBER ──────────────────────────
    function animNum(id, target) {
        const node = el(id);
        if (!node) return;
        const from = parseFloat(node.textContent) || 0;
        const dur = 500, t0 = performance.now();
        const tick = now => {
            const p = Math.min((now - t0) / dur, 1);
            node.textContent = Math.round(from + (target - from) * (1 - Math.pow(1 - p, 3)));
            if (p < 1) requestAnimationFrame(tick);
            else node.textContent = Math.round(target);
        };
        requestAnimationFrame(tick);
    }

    // ─── DOUGHNUT RING (dynamic) ──────────────────
    function updateRing(protein, carbs, fats) {
        const canvas = el('nutr-ring-canvas');
        if (!canvas || typeof Chart === 'undefined') return;

        const hasData = (protein + carbs + fats) > 0;
        const data    = hasData ? [protein, carbs, fats] : [1, 1, 1];
        const colors  = hasData
            ? ['#60a5fa', '#fbbf24', '#f87171']
            : ['#2a2a2a', '#2a2a2a', '#2a2a2a'];

        if (ringChart) {
            // Update in-place — no flicker
            ringChart.data.datasets[0].data             = data;
            ringChart.data.datasets[0].backgroundColor  = colors;
            ringChart.options.plugins.tooltip.enabled   = hasData;
            ringChart.update('active');
            return;
        }

        // First render
        ringChart = new Chart(canvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Protein', 'Carbs', 'Fats'],
                datasets: [{
                    data,
                    backgroundColor: colors,
                    borderColor: 'transparent',
                    borderWidth: 0,
                    hoverOffset: 5
                }]
            },
            options: {
                responsive: false,
                cutout: '72%',
                animation: { animateRotate: true, duration: 700 },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        enabled: hasData,
                        backgroundColor: '#181818',
                        borderColor: '#2a2a2a',
                        borderWidth: 1,
                        titleColor: '#fff',
                        bodyColor: '#a0a0a0',
                        callbacks: {
                            label: ctx => ` ${ctx.parsed.toFixed(1)}g`
                        }
                    }
                }
            }
        });
    }

    // ─── FETCH & RENDER LOGS ──────────────────────
    const MT_ORDER  = ['breakfast', 'lunch', 'dinner', 'snack'];
    const MT_COLOR  = { breakfast:'#fb923c', lunch:'#c8f135', dinner:'#818cf8', snack:'#f472b6' };
    const MT_ICON   = { breakfast:'☀️', lunch:'🌤', dinner:'🌙', snack:'🍌' };

    function fetchLogs() {
        fetch(`/api/nutrition/logs/?date=${currentDate}`, {
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': csrf() }
        })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(logs => renderLogs(logs))
        .catch(e => console.warn('fetchLogs error', e));
    }

    function renderLogs(logs) {
        const list  = el('nutr-log-list');
        const badge = el('nutr-entry-count');
        if (!list) return;

        if (badge) badge.textContent = `${logs.length} entr${logs.length === 1 ? 'y' : 'ies'}`;

        if (!logs.length) {
            list.innerHTML = `<div class="nutr-empty-state"><span>🥗</span><p>No meals logged yet</p></div>`;
            return;
        }

        let html = '';

        // Always render groups in fixed order
        MT_ORDER.forEach(type => {
            const group = logs.filter(l => l.meal_type === type);
            if (!group.length) return;

            const groupCal = group.reduce((s, l) => s + l.calories, 0).toFixed(0);
            const color    = MT_COLOR[type];

            html += `
                <div class="nutr-group" id="nutr-group-${type}">
                    <div class="nutr-group-header">
                        <span class="nutr-group-dot" style="background:${color}"></span>
                        <span class="nutr-group-name" style="color:${color}">${MT_ICON[type]} ${cap(type)}</span>
                        <span class="nutr-group-kcal">${groupCal} kcal</span>
                    </div>`;

            group.forEach(log => {
                html += `
                    <div class="nutr-entry" id="nutr-e-${log.id}">
                        <div class="nutr-entry-info">
                            <div class="nutr-entry-name">${log.food_name}</div>
                            <div class="nutr-entry-sub">${log.portion_size}${log.serving_unit}</div>
                        </div>
                        <div class="nutr-entry-chips">
                            <span class="nutr-chip-sm nc-cal">${log.calories} kcal</span>
                            <span class="nutr-chip-sm nc-prot">${log.protein}g P</span>
                        </div>
                        <button class="nutr-del" type="button"
                                onclick="Nutrition.del(${log.id})" title="Remove">✕</button>
                    </div>`;
            });

            html += `</div>`;
        });

        list.innerHTML = html;
    }

    // ─── WEEKLY BAR CHART ─────────────────────────
    function fetchWeekly() {
        fetch('/api/nutrition/weekly/', {
            credentials: 'same-origin',
            headers: { 'X-CSRFToken': csrf() }
        })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(days => renderBar(days))
        .catch(e => console.warn('fetchWeekly error', e));
    }

    function renderBar(days) {
        const canvas = el('nutr-bar-chart');
        if (!canvas || typeof Chart === 'undefined') return;

        const labels = days.map(d => d.day_label);
        const cals   = days.map(d => d.calories);
        const prots  = days.map(d => d.protein);

        if (barChart) {
            barChart.data.labels                   = labels;
            barChart.data.datasets[0].data         = cals;
            barChart.data.datasets[1].data         = prots;
            barChart.update('active');
            return;
        }

        barChart = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        label: 'Calories',
                        data: cals,
                        backgroundColor: 'rgba(200,241,53,.72)',
                        borderColor: '#c8f135',
                        borderWidth: 1,
                        borderRadius: 5,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Protein g',
                        data: prots,
                        backgroundColor: 'rgba(96,165,250,.65)',
                        borderColor: '#60a5fa',
                        borderWidth: 1,
                        borderRadius: 5,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        labels: {
                            color: '#a0a0a0',
                            font: { family: 'Barlow', size: 11 },
                            boxWidth: 10, padding: 14
                        }
                    },
                    tooltip: {
                        backgroundColor: '#181818',
                        borderColor: '#2a2a2a',
                        borderWidth: 1,
                        titleColor: '#fff',
                        bodyColor: '#a0a0a0'
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#a0a0a0', font: { family: 'Barlow', size: 11 } }
                    },
                    y: {
                        position: 'left',
                        beginAtZero: true,
                        grid: { color: 'rgba(255,255,255,.05)' },
                        ticks: { color: '#a0a0a0', font: { family: 'Barlow', size: 10 } }
                    },
                    y1: {
                        position: 'right',
                        beginAtZero: true,
                        grid: { display: false },
                        ticks: { color: '#60a5fa', font: { family: 'Barlow', size: 10 } }
                    }
                }
            }
        });
    }

    // WATER TRACKER
    function buildGlasses() {
        const wrap = el('nutr-glasses');
        if (!wrap) return;
        wrap.innerHTML = '';
        for (let i = 0; i < WATER_MAX; i++) {
            const btn = document.createElement('button');
            btn.className = 'nutr-glass';
            btn.type = 'button';
            btn.title = `Glass ${i + 1}`;
            btn.innerHTML = `<div class="nutr-glass-water"></div><span class="nutr-glass-drop">💧</span>`;
            btn.addEventListener('click', () => {
                waterCount = i < waterCount ? i : i + 1;
                waterCount = Math.max(0, Math.min(WATER_MAX, waterCount));
                updateGlasses();
            });
            wrap.appendChild(btn);
        }
        updateGlasses();
    }

    function updateGlasses() {
        document.querySelectorAll('.nutr-glass').forEach((g, i) => {
            g.classList.toggle('filled', i < waterCount);
        });
        const lbl = el('nutr-water-label');
        if (lbl) lbl.textContent = `${waterCount} / ${WATER_MAX}`;
        const fill = el('nutr-water-fill');
        if (fill) fill.style.width = (waterCount / WATER_MAX * 100) + '%';
    }

    // TOAST
    function toast(msg, isErr = false) {
        const t   = el('nutr-toast');
        const ico = el('nutr-toast-icon');
        const txt = el('nutr-toast-msg');
        if (!t) return;

        if (ico) ico.textContent = isErr ? '✗' : '✓';
        if (txt) txt.textContent = msg;
        t.style.borderColor = isErr
            ? 'rgba(248,113,113,.4)'
            : 'rgba(200,241,53,.4)';

        t.classList.add('show');
        clearTimeout(t._t);
        t._t = setTimeout(() => t.classList.remove('show'), 3200);
    }

    //  PUBLIC API
    return {
        init,
        del: deleteEntry   // called from onclick in the HTML
    };

})();


// Hook into navbar.js switchScreen
document.addEventListener('DOMContentLoaded', () => {
    const _orig = window.switchScreen;
    window.switchScreen = function (screenId) {
        if (typeof _orig === 'function') _orig(screenId);
        if (screenId === 'nutrition-screen') {
            // Tiny delay so the screen is display:block before we read canvas dimensions
            setTimeout(() => Nutrition.init(), 80);
        }
    };
});
