const API_BASE = "/api";
const PLACEHOLDER_IMAGES = [
    "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1594737625785-a6cbdabd333c?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?auto=format&fit=crop&w=900&q=80",
];

let allCategories = [];
let currentCategory = null;
let userLogs = {};
let homeDashboardLoaded = false;
let homeDashboardCharts = {};
let dashboardState = {
    reminders: [],
    workoutVideos: [],
    suggestedWorkouts: [],
};

let activeLevel = document.body.getAttribute("data-fitness-level") || "beginner";
let activeType = "all";
let activeMuscle = "all";

const dashboardSection = document.getElementById("dashboard");
const exercisesSection = document.getElementById("exercises-section");
const detailSection = document.getElementById("exercise-detail-section");
const exercisesList = document.getElementById("exercises-list");
const categoryTitle = document.getElementById("category-title");
const cardContainer = document.querySelector(".card-container");

document.addEventListener("DOMContentLoaded", async () => {
    await Promise.all([loadCategories(), loadLogs()]);
    initChips();
    updateMuscleChips();
    renderCategoryCards();
    initDashboardEventHandlers();
    loadHomeDashboard();
});

async function loadHomeDashboard(force = false) {
    if (homeDashboardLoaded && !force) return;

    try {
        const response = await fetch("/dashboard/summary/");
        const summary = await response.json();

        dashboardState = {
            reminders: summary.reminders || [],
            workoutVideos: summary.workout_videos || [],
            suggestedWorkouts: summary.suggested_workouts || [],
        };

        renderActivitySnapshot(summary.today_activity);
        renderGoalProgress(summary.goal_progress, summary.weekly_stats);
        renderMealPlanPreview(summary.meal_plan_enabled, summary.meal_plan_preview);
        renderWeeklyCharts(summary.weekly_stats);
        renderWorkoutVideoGrid(summary.workout_videos || []);
        renderSuggestedWorkoutList(summary.suggested_workouts || []);
        renderReminders(summary.reminders || []);
        renderInsights(summary.insights || []);
        await loadFeedbackThread();

        homeDashboardLoaded = true;
    } catch (error) {
        console.error("Failed to load dashboard summary:", error);
    }
}

function initDashboardEventHandlers() {
    document.getElementById("markWorkoutCompleteBtn")?.addEventListener("click", markWorkoutVideoComplete);
    document.getElementById("dashboardFeedbackForm")?.addEventListener("submit", submitFeedbackEntry);
}

function renderActivitySnapshot(activity) {
    const stateNode = document.getElementById("todayActivityState");
    const caloriesNode = document.getElementById("activityCalories");
    const workoutNode = document.getElementById("activityWorkout");
    const stepsNode = document.getElementById("activitySteps");
    const waterNode = document.getElementById("activityWater");

    if (!activity?.has_record) {
        if (stateNode) {
            stateNode.textContent = activity?.message || "No activity recorded today";
            stateNode.classList.remove("is-active");
        }
        if (caloriesNode) caloriesNode.textContent = "0 kcal";
        if (workoutNode) workoutNode.textContent = "Rest day";
        if (stepsNode) stepsNode.textContent = "0";
        if (waterNode) waterNode.textContent = "0 cups";
        return;
    }

    if (stateNode) {
        stateNode.textContent = `Active today • ${activity.date}`;
        stateNode.classList.add("is-active");
    }
    if (caloriesNode) caloriesNode.textContent = `${activity.calories_burned || 0} kcal`;
    if (workoutNode) workoutNode.textContent = activity.workout_done ? "Workout logged" : "No workout yet";
    if (stepsNode) stepsNode.textContent = formatNumber(activity.steps || 0);
    if (waterNode) waterNode.textContent = `${activity.water_intake || 0} cups`;
}

function renderGoalProgress(goalProgress, weeklyStats) {
    const progressPercent = Number(weeklyStats?.progress_percent || 0);
    const completedWorkouts = Number(weeklyStats?.completed_workouts || 0);
    const weeklyGoal = Number(weeklyStats?.weekly_goal || 0);
    const circle = document.getElementById("goalProgressCircle");
    const percentNode = document.getElementById("goalProgressPercent");
    const completedNode = document.getElementById("completedWorkoutsCounter");
    const weeklyGoalNode = document.getElementById("weeklyGoalCounter");
    const subtextNode = document.getElementById("goalProgressSubtext");
    const caloriesBurnedNode = document.getElementById("caloriesBurnedMetric");
    const caloriesRemainingNode = document.getElementById("caloriesRemainingMetric");

    if (percentNode) percentNode.textContent = `${progressPercent}%`;
    if (completedNode) animateCounter(completedNode, completedWorkouts);
    if (weeklyGoalNode) weeklyGoalNode.textContent = weeklyGoal;
    if (subtextNode) {
        subtextNode.textContent = goalProgress
            ? `${completedWorkouts} of ${weeklyGoal} workouts completed this week`
            : "No activity recorded today";
    }
    if (caloriesBurnedNode) {
        caloriesBurnedNode.textContent = `${goalProgress?.calories_burned || 0} kcal`;
    }
    if (caloriesRemainingNode) {
        caloriesRemainingNode.textContent = `${goalProgress?.calories_remaining || weeklyStats?.weekly_calorie_target || 0} left`;
    }

    if (!circle) return;
    const radius = 48;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (progressPercent / 100) * circumference;
    circle.style.strokeDasharray = `${circumference}`;
    circle.style.strokeDashoffset = `${circumference}`;
    circle.style.stroke = getProgressColor(progressPercent);
    requestAnimationFrame(() => {
        circle.style.strokeDashoffset = `${offset}`;
    });
}

function renderMealPlanPreview(enabled, preview) {
    const toggle = document.getElementById("dashboardMealPlanToggle");
    const card = document.getElementById("mealPlanPreviewCard");
    if (toggle) toggle.checked = !!enabled;
    if (!card) return;

    if (!enabled) {
        card.className = "meal-plan-preview empty";
        card.innerHTML = "<p>Meal plan is currently turned off for this profile.</p>";
        return;
    }
    if (!preview) {
        card.className = "meal-plan-preview empty";
        card.innerHTML = "<p>No active meal plan was found for today.</p>";
        return;
    }
    if (!preview.meals?.length) {
        card.className = "meal-plan-preview";
        card.innerHTML = `
            <div class="meal-plan-title">${preview.name}</div>
            <div class="meal-plan-goal">${preview.goal} goal • ${Math.round(preview.target_calories || 0)} kcal target</div>
            <p>No meals are scheduled for today yet.</p>
        `;
        return;
    }

    card.className = "meal-plan-preview";
    card.innerHTML = `
        <div class="meal-plan-title">${preview.name}</div>
        <div class="meal-plan-goal">${preview.goal} goal • ${Math.round(preview.target_calories || 0)} kcal target</div>
        ${preview.meals.map((meal) => `
            <div class="meal-plan-meal">
                <div class="meal-plan-meal-type">${meal.meal_type}</div>
                ${meal.items.map((item) => `
                    <div class="meal-plan-item">
                        <span>${item.food} • ${trimNumber(item.quantity)} ${item.unit}</span>
                        <span>${trimNumber(item.calories)} kcal</span>
                    </div>
                `).join("")}
            </div>
        `).join("")}
    `;
}

function renderWeeklyCharts(weeklyStats) {
    const labels = (weeklyStats?.activity_series || []).map((item) => item.label);
    const workoutData = (weeklyStats?.activity_series || []).map((item) => item.workouts);
    const calorieBalance = weeklyStats?.calorie_balance || [];

    renderLineChart("dashboardConsistencyChart", labels, workoutData, "Workouts", "#0f766e");
    renderBarChart(
        "dashboardCalorieBalanceChart",
        labels,
        calorieBalance,
        "Calories vs Target",
        calorieBalance.map((value) => value >= 0 ? "rgba(15,118,110,0.74)" : "rgba(234,88,12,0.74)")
    );

    const streakNode = document.getElementById("dashboardStreakCount");
    if (streakNode) streakNode.textContent = weeklyStats?.progress_percent || 0;
}

function renderLineChart(canvasId, labels, data, label, borderColor) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    destroyChart(canvasId);
    if (!data?.length) return;

    homeDashboardCharts[canvasId] = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label,
                data,
                borderColor,
                backgroundColor: `${borderColor}22`,
                fill: true,
                tension: 0.35,
                pointRadius: 3,
                pointBackgroundColor: borderColor,
            }],
        },
        options: dashboardChartOptions(),
    });
}

function renderBarChart(canvasId, labels, data, label, backgroundColor) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    destroyChart(canvasId);
    if (!data?.length) return;

    homeDashboardCharts[canvasId] = new Chart(canvas, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label,
                data,
                backgroundColor,
                borderRadius: 10,
                borderSkipped: false,
            }],
        },
        options: dashboardChartOptions(),
    });
}

function dashboardChartOptions() {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            x: {
                grid: { display: false },
                ticks: { color: "#627488", font: { family: "Inter", size: 11 } },
            },
            y: {
                grid: { color: "rgba(99, 117, 138, 0.12)" },
                ticks: { color: "#627488", font: { family: "Inter", size: 11 } },
                beginAtZero: true,
            },
        },
    };
}

function destroyChart(canvasId) {
    if (homeDashboardCharts[canvasId]) {
        homeDashboardCharts[canvasId].destroy();
        delete homeDashboardCharts[canvasId];
    }
}

function renderWorkoutVideoGrid(videos) {
    const grid = document.getElementById("workoutVideoGrid");
    if (!grid) return;

    grid.innerHTML = videos.map((video, index) => `
        <article class="video-card">
            <div class="video-thumb" style="background-image:linear-gradient(180deg, rgba(5, 10, 23, 0.08), rgba(5, 10, 23, 0.3)),url('${video.thumbnail || PLACEHOLDER_IMAGES[index % PLACEHOLDER_IMAGES.length]}')"></div>
            <div class="video-card-body">
                <div class="video-meta">
                    <span>${video.duration || "12 min"}</span>
                    <span class="difficulty-badge">${video.difficulty || "Beginner"}</span>
                </div>
                <div class="video-title">${video.title}</div>
                <div class="suggested-workout-meta">
                    <span class="meta-chip">${video.target_muscle || "Full Body"}</span>
                </div>
                <button class="ghost-action" type="button" onclick="openWorkoutVideoModalById(${video.id})">Watch video</button>
            </div>
        </article>
    `).join("");
}

function renderSuggestedWorkoutList(workouts) {
    const list = document.getElementById("suggestedWorkoutList");
    if (!list) return;

    list.innerHTML = workouts.map((workout) => `
        <article class="suggested-workout-item">
            <div class="suggested-workout-header">
                <div class="suggested-workout-name">${workout.name}</div>
                <span class="difficulty-badge">${workout.difficulty}</span>
            </div>
            <div class="suggested-workout-meta">
                <span class="meta-chip">${workout.duration}</span>
                <span class="meta-chip">${workout.target_muscle}</span>
            </div>
            <div>${workout.description || "Recommended based on your current focus and fitness level."}</div>
            <button class="primary-cta" type="button" onclick="openSuggestedWorkout(${workout.id})">Start workout</button>
        </article>
    `).join("");
}

function openSuggestedWorkout(workoutId) {
    const workout = (dashboardState.suggestedWorkouts || []).find((item) => item.id === workoutId);
    if (workout) openWorkoutVideoModal({
        id: workout.id,
        title: workout.name,
        description: workout.description,
        video_url: workout.video_url,
        computed_sets: workout.computed_sets,
    });
}

function openWorkoutVideoModalById(videoId) {
    const item = (dashboardState.workoutVideos || []).find((video) => video.id === videoId)
        || (dashboardState.suggestedWorkouts || []).find((workout) => workout.id === videoId);
    if (!item) return;
    openWorkoutVideoModal({
        id: item.id,
        title: item.title || item.name,
        description: item.description,
        video_url: item.video_url,
        computed_sets: item.computed_sets,
    });
}

function openWorkoutVideoModal(item) {
    const modal = document.getElementById("workoutVideoModal");
    const title = document.getElementById("videoModalTitle");
    const description = document.getElementById("videoModalDescription");
    const player = document.getElementById("videoModalPlayer");
    const completeBtn = document.getElementById("markWorkoutCompleteBtn");
    if (!modal || !title || !description || !player || !completeBtn) return;

    title.textContent = item.title || "Workout video";
    description.textContent = item.description || "Follow along with this workout demo.";
    player.innerHTML = item.video_url ? `<source src="${item.video_url}" type="video/mp4">` : "";
    completeBtn.dataset.exerciseId = item.id || "";
    completeBtn.dataset.totalSets = item.computed_sets || 3;
    modal.classList.add("show");
    player.load();
}

function closeWorkoutVideoModal() {
    const modal = document.getElementById("workoutVideoModal");
    const player = document.getElementById("videoModalPlayer");
    if (modal) modal.classList.remove("show");
    if (player) player.pause();
}

async function markWorkoutVideoComplete() {
    const button = document.getElementById("markWorkoutCompleteBtn");
    const exerciseId = Number(button?.dataset.exerciseId || 0);
    const totalSets = Number(button?.dataset.totalSets || 3);
    if (!exerciseId) {
        closeWorkoutVideoModal();
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/logs/update/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ exercise_id: exerciseId, sets_completed: totalSets }),
        });
        const data = await response.json();
        userLogs[exerciseId] = {
            sets_completed: data.sets_completed,
            total_sets: data.total_sets,
            status: data.status,
        };
        closeWorkoutVideoModal();
        showCompletionToast("Workout completed.");
        homeDashboardLoaded = false;
        loadHomeDashboard(true);
    } catch (error) {
        console.error("Failed to complete workout:", error);
    }
}

function renderReminders(reminders) {
    const container = document.getElementById("dashboardReminders");
    if (!container) return;

    const dismissed = JSON.parse(localStorage.getItem("dashboardDismissedReminders") || "[]");
    const visible = reminders.filter((reminder) => !dismissed.includes(reminder.id));
    container.innerHTML = visible.length
        ? visible.map((reminder) => `
            <div class="reminder-item" data-reminder-id="${reminder.id}">
                <div>${reminder.text}</div>
                <button class="dismiss-reminder-btn" type="button" onclick="dismissDashboardReminder('${reminder.id}')">Dismiss</button>
            </div>
        `).join("")
        : `<div class="reminder-item">No reminders right now.</div>`;
}

function dismissDashboardReminder(reminderId) {
    const dismissed = JSON.parse(localStorage.getItem("dashboardDismissedReminders") || "[]");
    if (!dismissed.includes(reminderId)) {
        dismissed.push(reminderId);
        localStorage.setItem("dashboardDismissedReminders", JSON.stringify(dismissed));
    }
    renderReminders(dashboardState.reminders || []);
}

function renderInsights(insights) {
    const container = document.getElementById("dashboardInsights");
    if (!container) return;
    container.innerHTML = insights.map((insight) => `<div class="insight-item">${insight}</div>`).join("");
}

async function loadFeedbackThread() {
    const container = document.getElementById("feedbackThreadList");
    if (!container) return;

    try {
        const response = await fetch("/dashboard/feedback/");
        const data = await response.json();
        const entries = data.results || [];
        if (!entries.length) {
            container.innerHTML = '<div class="feedback-thread-item"><div>No feedback sent yet.</div></div>';
            return;
        }

        container.innerHTML = entries.map((entry) => `
            <div class="feedback-thread-item">
                <div class="feedback-thread-meta">
                    <span>${entry.category}</span>
                    <span class="feedback-status">${entry.status}</span>
                    <span>${entry.created_at}</span>
                </div>
                <div>${entry.message}</div>
                ${entry.admin_response ? `
                    <div class="feedback-admin-response">
                        <div class="feedback-response-meta">
                            <strong>Admin reply</strong>
                            <span>${entry.responded_at}</span>
                        </div>
                        <div>${entry.admin_response}</div>
                    </div>
                ` : ""}
            </div>
        `).join("");
    } catch (error) {
        console.error("Failed to load feedback thread:", error);
    }
}

async function submitFeedbackEntry(event) {
    event.preventDefault();
    const category = document.getElementById("feedbackCategory")?.value;
    const messageField = document.getElementById("feedbackMessage");
    const message = messageField?.value.trim();
    if (!message) return;

    const formData = new FormData();
    formData.append("category", category);
    formData.append("message", message);

    try {
        const response = await fetch("/dashboard/feedback/", {
            method: "POST",
            headers: { "X-CSRFToken": getCookie("csrftoken") },
            body: formData,
        });
        if (!response.ok) return;
        messageField.value = "";
        showCompletionToast("Feedback sent.");
        loadFeedbackThread();
    } catch (error) {
        console.error("Failed to submit feedback:", error);
    }
}

async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories/`);
        allCategories = await response.json();
    } catch (error) {
        console.error("Failed to load categories:", error);
        allCategories = [];
    }
}

async function loadLogs() {
    try {
        const response = await fetch(`${API_BASE}/logs/`);
        const data = await response.json();
        userLogs = {};
        data.forEach((log) => {
            userLogs[log.exercise_id] = {
                sets_completed: log.sets_completed,
                total_sets: log.total_sets,
                status: log.status,
            };
        });
    } catch (error) {
        console.error("Failed to load logs:", error);
    }
}

function initChips() {
    document.querySelectorAll(".chip[data-level]").forEach((chip) => {
        if (chip.getAttribute("data-level") === activeLevel) chip.classList.add("selected");
        chip.addEventListener("click", () => {
            document.querySelectorAll(".chip[data-level]").forEach((node) => node.classList.remove("selected"));
            chip.classList.add("selected");
            activeLevel = chip.getAttribute("data-level");
            updateLevelTag();
            if (currentCategory && exercisesSection.style.display !== "none") {
                renderExercises(currentCategory.exercises);
            }
        });
    });

    document.querySelectorAll(".chip[data-type]").forEach((chip) => {
        chip.addEventListener("click", () => {
            document.querySelectorAll(".chip[data-type]").forEach((node) => node.classList.remove("selected"));
            chip.classList.add("selected");
            activeType = chip.getAttribute("data-type");
            updateMuscleChips();
            renderCategoryCards();
        });
    });
}

function updateMuscleChips() {
    const row = document.getElementById("muscle-chip-row");
    if (!row) return;

    const relevantMuscles = new Set();
    allCategories.forEach((category) => {
        if (activeType === "all" || category.training_type === activeType) {
            (category.muscle_groups || []).forEach((group) => {
                relevantMuscles.add(`${group.name}|${group.display_name}`);
            });
        }
    });

    row.innerHTML = "";
    const allChip = makeChip("All", "all", "muscle");
    if (activeMuscle === "all") allChip.classList.add("selected");
    row.appendChild(allChip);

    relevantMuscles.forEach((entry) => {
        const [name, label] = entry.split("|");
        const chip = makeChip(label, name, "muscle");
        if (activeMuscle === name) chip.classList.add("selected");
        row.appendChild(chip);
    });
}

function makeChip(label, value, type) {
    const chip = document.createElement("button");
    chip.className = "chip";
    chip.textContent = label;
    chip.setAttribute(`data-${type}`, value);
    chip.addEventListener("click", () => {
        document.querySelectorAll(`[data-${type}]`).forEach((node) => node.classList.remove("selected"));
        chip.classList.add("selected");
        if (type === "muscle") {
            activeMuscle = value;
            renderCategoryCards();
        }
    });
    return chip;
}

function renderCategoryCards() {
    if (!cardContainer) return;
    cardContainer.innerHTML = "";

    const filtered = allCategories.filter((category) => {
        const typeMatch = activeType === "all" || category.training_type === activeType;
        const muscleMatch = activeMuscle === "all" || (category.muscle_groups || []).some((group) => group.name === activeMuscle);
        return typeMatch && muscleMatch;
    });

    if (!filtered.length) {
        cardContainer.innerHTML = `
            <div class="empty-state">
                <p class="empty-msg">No categories match</p>
                <p class="empty-sub">Try a different filter.</p>
            </div>
        `;
        return;
    }

    filtered.forEach((category, index) => {
        cardContainer.appendChild(buildCategoryCard(category, index));
    });
}

function buildCategoryCard(category, index) {
    const div = document.createElement("div");
    div.className = `category-card ${category.training_type || "strength"}`;
    div.setAttribute("data-id", category.id);
    div.innerHTML = `
        <div class="card-left">
            <span class="card-type-tag">${(category.training_type || "").toUpperCase()}</span>
            <h3>${category.name}</h3>
            <p class="program-count">${category.exercises ? category.exercises.length : 0} Exercises</p>
        </div>
        ${category.image ? `<div class="card-right"><img src="${category.image}" alt="${category.name}"></div>` : ""}
        <span class="card-number">${String(index + 1).padStart(2, "0")}</span>
    `;
    div.addEventListener("click", () => showExercises(category));
    return div;
}

function showExercises(category) {
    currentCategory = category;
    if (categoryTitle) categoryTitle.textContent = category.name;
    updateLevelTag();
    renderExercises(category.exercises);
    dashboardSection.style.display = "none";
    exercisesSection.style.display = "block";
    if (detailSection) detailSection.style.display = "none";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateLevelTag() {
    const tag = document.getElementById("level-tag");
    if (tag) tag.textContent = capitalize(activeLevel);
}

function renderExercises(exercises) {
    if (!exercisesList) return;
    exercisesList.innerHTML = "";
    const filtered = (exercises || []).filter((exercise) => exercise.level === activeLevel);

    if (!filtered.length) {
        exercisesList.innerHTML = `
            <div class="empty-state">
                <p class="empty-msg">No ${activeLevel} exercises yet</p>
                <p class="empty-sub">Switch level or check back soon.</p>
            </div>
        `;
        return;
    }

    filtered.forEach((exercise) => {
        exercisesList.appendChild(buildExerciseCard(exercise));
    });
}

function buildExerciseCard(exercise) {
    const div = document.createElement("div");
    div.className = "exercise-card";
    div.setAttribute("data-exercise-id", exercise.id);

    let mediaSide = "";
    if (exercise.image) {
        mediaSide = `<div class="exercise-img-side"><img src="${exercise.image}" alt="${exercise.name}" loading="lazy"></div>`;
    } else if (exercise.demo_video) {
        mediaSide = `<div class="exercise-video-side"><video muted loop playsinline><source src="${exercise.demo_video}" type="video/mp4"></video></div>`;
    } else {
        mediaSide = `<div class="exercise-no-media">${getCategoryIcon(exercise.exercise_type)}</div>`;
    }

    const stats = (exercise.stats || []).map((stat) => `
        <div class="stat-item">
            <span class="stat-label">${stat.label}</span>
            <span class="stat-value">${stat.value}</span>
        </div>
    `).join("");

    div.innerHTML = `
        <div class="exercise-card-inner">
            ${mediaSide}
            <div class="exercise-body">
                <span class="level-badge ${exercise.level}">${capitalize(exercise.level)}</span>
                <h3 class="exercise-name">${exercise.name}</h3>
                <div class="exercise-stats">${stats}</div>
                ${exercise.description ? `<p class="exercise-desc">${exercise.description}</p>` : ""}
            </div>
        </div>
        ${buildStatusBar(userLogs[exercise.id], exercise)}
    `;

    div.addEventListener("click", () => showExerciseDetail(exercise));
    return div;
}

function buildStatusBar(log, exercise) {
    if (!log || log.status === "not_started") return "";
    const done = log.sets_completed;
    const total = log.total_sets || exercise.computed_sets || 3;
    const pct = Math.min(100, Math.round((done / total) * 100));
    if (log.status === "completed") {
        return `<div class="completion-bar completed">Completed - ${done}/${total} sets</div>`;
    }
    return `
        <div class="completion-bar in-progress">
            <div class="completion-bar-fill" style="width:${pct}%"></div>
            <span class="completion-label">${done}/${total} sets</span>
        </div>
    `;
}

function showExerciseDetail(exercise) {
    if (!detailSection) return;

    const log = userLogs[exercise.id] || { sets_completed: 0, total_sets: exercise.computed_sets || 3, status: "not_started" };
    const totalSets = exercise.computed_sets || 3;
    const heroStyle = exercise.image
        ? `background:url('${exercise.image}') center/cover no-repeat;`
        : `background:${getTypeGradient(exercise.exercise_type)};`;

    const statsChips = (exercise.stats || []).map((stat) => `
        <div class="detail-stat">
            <span class="detail-stat-label">${stat.label}</span>
            <span class="detail-stat-value">${stat.value}</span>
        </div>
    `).join("");

    const instructions = (exercise.instructions_list || []).map((step, index) => `
        <li class="instruction-step">
            <span class="step-num">${index + 1}</span>
            <span>${step.replace(/^\d+\.\s*/, "")}</span>
        </li>
    `).join("");

    const setCircles = Array.from({ length: totalSets }, (_, index) => `
        <button class="set-circle ${index < log.sets_completed ? "done" : ""}"
                data-set-index="${index}"
                onclick="toggleSet(${exercise.id}, ${index}, ${totalSets})">
            ${index < log.sets_completed ? "✓" : index + 1}
        </button>
    `).join("");

    detailSection.innerHTML = `
        <div class="detail-hero" style="${heroStyle}">
            <div class="detail-hero-overlay"></div>
            <button class="back-btn detail-back" onclick="closeDetail()" aria-label="Go back"></button>
            <div class="detail-hero-content">
                <span class="level-badge ${exercise.level}">${capitalize(exercise.level)}</span>
                <h1 class="detail-title">${exercise.name}</h1>
                ${exercise.muscle_group_name ? `<p class="detail-muscle">${exercise.muscle_group_name}</p>` : ""}
            </div>
        </div>
        <div class="detail-body">
            <div class="detail-stats-row">${statsChips}</div>
            ${exercise.description ? `<div class="detail-section"><h3 class="detail-section-title">About</h3><p class="detail-description">${exercise.description}</p></div>` : ""}
            ${instructions ? `<div class="detail-section"><h3 class="detail-section-title">How To</h3><ol class="instructions-list">${instructions}</ol></div>` : ""}
            ${exercise.demo_video ? `<div class="detail-section"><h3 class="detail-section-title">Form Demo</h3><div class="detail-video-wrap"><video controls><source src="${exercise.demo_video}" type="video/mp4"></video></div></div>` : ""}
            <div class="detail-section">
                <h3 class="detail-section-title">Sets Tracker</h3>
                <p class="sets-sub">Tap each circle as you complete the set.</p>
                <div class="sets-tracker" id="sets-tracker-${exercise.id}">${setCircles}</div>
                ${log.sets_completed > 0 ? `<button class="reset-btn" onclick="resetLog(${exercise.id})">Reset Progress</button>` : ""}
            </div>
        </div>
    `;

    exercisesSection.style.display = "none";
    detailSection.style.display = "block";
}

async function toggleSet(exerciseId, setIndex, totalSets) {
    const log = userLogs[exerciseId] || { sets_completed: 0 };
    let setsCompleted = log.sets_completed;
    if (setIndex < setsCompleted) setsCompleted = setIndex;
    else if (setIndex === setsCompleted) setsCompleted = setIndex + 1;

    try {
        const response = await fetch(`${API_BASE}/logs/update/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({ exercise_id: exerciseId, sets_completed: setsCompleted }),
        });
        const data = await response.json();
        userLogs[exerciseId] = {
            sets_completed: data.sets_completed,
            total_sets: data.total_sets,
            status: data.status,
        };
        updateSetCircles(exerciseId, data.sets_completed);
        updateExerciseCard(exerciseId);
        if (data.status === "completed") {
            showCompletionToast("Exercise complete!");
            homeDashboardLoaded = false;
            loadHomeDashboard(true);
        }
    } catch (error) {
        console.error("Failed to update log:", error);
    }
}

function updateSetCircles(exerciseId, doneSets) {
    const tracker = document.getElementById(`sets-tracker-${exerciseId}`);
    if (!tracker) return;
    tracker.querySelectorAll(".set-circle").forEach((circle, index) => {
        circle.classList.toggle("done", index < doneSets);
        circle.textContent = index < doneSets ? "✓" : index + 1;
    });
}

function updateExerciseCard(exerciseId) {
    const card = document.querySelector(`.exercise-card[data-exercise-id="${exerciseId}"]`);
    if (!card || !currentCategory) return;
    const exercise = currentCategory.exercises.find((item) => item.id === exerciseId);
    card.querySelector(".completion-bar")?.remove();
    card.insertAdjacentHTML("beforeend", buildStatusBar(userLogs[exerciseId], exercise));
}

async function resetLog(exerciseId) {
    if (!confirm("Reset your progress for this exercise?")) return;
    try {
        await fetch(`${API_BASE}/logs/${exerciseId}/reset/`, {
            method: "DELETE",
            headers: { "X-CSRFToken": getCookie("csrftoken") },
        });
        userLogs[exerciseId] = { sets_completed: 0, total_sets: 3, status: "not_started" };
        updateSetCircles(exerciseId, 0);
        updateExerciseCard(exerciseId);
        homeDashboardLoaded = false;
        loadHomeDashboard(true);
    } catch (error) {
        console.error("Failed to reset log:", error);
    }
}

function closeExercises() {
    exercisesSection.style.display = "none";
    dashboardSection.style.display = "block";
    currentCategory = null;
}

function closeDetail() {
    detailSection.style.display = "none";
    exercisesSection.style.display = "block";
}

const searchInput = document.getElementById("search-workout");
let debounceTimer;
searchInput?.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
        const query = searchInput.value.trim();
        if (!query) {
            renderCategoryCards();
            return;
        }

        fetch(`/dashboard/search/?q=${encodeURIComponent(query)}`)
            .then((response) => response.json())
            .then((data) => {
                if (!cardContainer) return;
                cardContainer.innerHTML = "";
                if (!data.results?.length) {
                    cardContainer.innerHTML = `<div class="empty-state"><p class="empty-msg">No results for "${query}"</p></div>`;
                    return;
                }
                data.results.forEach((category, index) => {
                    const full = allCategories.find((item) => item.id === category.id) || category;
                    cardContainer.appendChild(buildCategoryCard(full, index));
                });
            });
    }, 300);
});

const avatarBtn = document.getElementById("avatarBtn");
const profilePanel = document.getElementById("profilePanel");
avatarBtn?.addEventListener("click", (event) => {
    event.stopPropagation();
    profilePanel.style.display = profilePanel.style.display === "block" ? "none" : "block";
});

document.addEventListener("click", (event) => {
    if (profilePanel && !profilePanel.contains(event.target) && event.target !== avatarBtn) {
        profilePanel.style.display = "none";
    }
});

document.getElementById("uploadPhotoBtn")?.addEventListener("click", () => {
    document.getElementById("profileImageInput")?.click();
});

document.getElementById("profileImageInput")?.addEventListener("change", async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("profile_image", file);
    const response = await fetch("/upload-profile-image/", {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        body: formData,
    });
    const data = await response.json();
    if (data.success) {
        const img = avatarBtn.querySelector("img");
        if (img) img.src = data.image_url;
        else avatarBtn.innerHTML = `<img src="${data.image_url}" alt="Avatar">`;
    }
});

document.getElementById("backupToggle")?.addEventListener("change", () => {
    fetch("/toggle-backup/", { method: "POST", headers: { "X-CSRFToken": getCookie("csrftoken") } });
});

document.getElementById("logoutBtn")?.addEventListener("click", () => {
    fetch("/logout/", { method: "POST", headers: { "X-CSRFToken": getCookie("csrftoken") } })
        .then(() => { window.location.href = "/login/"; });
});

document.getElementById("deleteBtn")?.addEventListener("click", () => {
    if (!confirm("Permanently delete your account?")) return;
    fetch("/profile/delete/", { method: "POST", headers: { "X-CSRFToken": getCookie("csrftoken") } })
        .then(() => { window.location.href = "/"; });
});

function getCookie(name) {
    let value = null;
    document.cookie.split(";").forEach((chunk) => {
        const item = chunk.trim();
        if (item.startsWith(`${name}=`)) value = decodeURIComponent(item.slice(name.length + 1));
    });
    return value;
}

function getTypeGradient(type) {
    const gradients = {
        strength: "linear-gradient(135deg, #1a1a2e, #0f3460)",
        hiit: "linear-gradient(135deg, #2d0a0a, #7b1919)",
        cardio: "linear-gradient(135deg, #0a1a0a, #1a4a2e)",
        mobility: "linear-gradient(135deg, #1a0f2e, #4a2d7a)",
    };
    return gradients[type] || gradients.strength;
}

function getCategoryIcon(type) {
    const icons = {
        strength: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M6.5 6.5h11M12 3v18M4 12h16"/></svg>`,
        hiit: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>`,
        cardio: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>`,
        mobility: `<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><circle cx="12" cy="5" r="2"/><path d="m3 12 4-4 4 4 4-4 4 4M3 19l4-4 4 4 4-4 4 4"/></svg>`,
    };
    return icons[type] || icons.strength;
}

function animateCounter(node, target) {
    if (!node) return;
    const duration = 900;
    const startTime = performance.now();
    const initial = Number(node.textContent) || 0;

    function tick(now) {
        const progress = Math.min((now - startTime) / duration, 1);
        node.textContent = Math.round(initial + ((target - initial) * progress));
        if (progress < 1) requestAnimationFrame(tick);
    }

    requestAnimationFrame(tick);
}

function getProgressColor(percent) {
    if (percent >= 70) return "#16a34a";
    if (percent >= 40) return "#f59e0b";
    return "#dc2626";
}

function formatNumber(value) {
    return Number(value || 0).toLocaleString();
}

function trimNumber(value) {
    return Number(value || 0).toFixed(1).replace(".0", "");
}

function capitalize(value) {
    return value ? value.charAt(0).toUpperCase() + value.slice(1) : "";
}

function showCompletionToast(message) {
    const toast = document.createElement("div");
    toast.className = "completion-toast";
    toast.textContent = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => toast.classList.add("show"));
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 250);
    }, 2400);
}
