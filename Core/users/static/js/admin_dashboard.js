document.addEventListener('DOMContentLoaded', () => {
  const dataElement = document.getElementById('admin-dashboard-data');

  if (!dataElement || typeof Chart === 'undefined') {
    return;
  }

  const dashboardData = JSON.parse(dataElement.textContent);

  Chart.defaults.color = '#64748b';
  Chart.defaults.borderColor = '#d7e3f4';
  Chart.defaults.font.family = "'DM Mono', monospace";
  Chart.defaults.font.size = 11;

  const BLUE = '#2563eb';
  const VIOLET = '#7c3aed';
  const ORANGE = '#f97316';
  const CYAN = '#06b6d4';
  const RED = '#e11d48';
  const GREEN = '#16a34a';
  const NEUTRAL = '#dbe7f5';
  const GRID = '#d7e3f4';
  const PALETTE = [BLUE, VIOLET, ORANGE, CYAN, RED, GREEN, '#0ea5e9', '#a78bfa', '#34d399', '#f59e0b'];

  function makeGradient(ctx, color) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, color + '40');
    gradient.addColorStop(1, color + '05');
    return gradient;
  }

  const regCtx = document.getElementById('regChart')?.getContext('2d');
  let regChart = null;

  if (regCtx) {
    regChart = new Chart(regCtx, {
      type: 'line',
      data: {
        labels: dashboardData.reg.daily.labels,
        datasets: [{
          label: 'New Users',
          data: dashboardData.reg.daily.data,
          borderColor: BLUE,
          backgroundColor: makeGradient(regCtx, BLUE),
          borderWidth: 2,
          pointBackgroundColor: BLUE,
          pointRadius: 3,
          tension: 0.4,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: GRID } },
          y: { grid: { color: GRID }, beginAtZero: true, ticks: { precision: 0 } },
        },
      },
    });
  }

  document.querySelectorAll('[data-reg-period]').forEach((button) => {
    button.addEventListener('click', () => {
      if (!regChart) {
        return;
      }

      const period = button.dataset.regPeriod;
      const selectedPeriod = dashboardData.reg[period];

      if (!selectedPeriod) {
        return;
      }

      document.querySelectorAll('[data-reg-period]').forEach((tab) => tab.classList.remove('active'));
      button.classList.add('active');
      regChart.data.labels = selectedPeriod.labels;
      regChart.data.datasets[0].data = selectedPeriod.data;
      regChart.update();
    });
  });

  const activeChartElement = document.getElementById('activeChart');
  if (activeChartElement) {
    new Chart(activeChartElement, {
      type: 'doughnut',
      data: {
        labels: ['Active', 'Inactive'],
        datasets: [{
          data: dashboardData.activeData,
          backgroundColor: [GREEN, NEUTRAL],
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom', labels: { padding: 16 } },
          tooltip: { callbacks: { label: (context) => ` ${context.parsed} users` } },
        },
        cutout: '70%',
      },
    });
  }

  const retentionChartElement = document.getElementById('retentionChart');
  if (retentionChartElement) {
    new Chart(retentionChartElement, {
      type: 'doughnut',
      data: {
        labels: ['Retained', 'Churned'],
        datasets: [{
          data: dashboardData.retentionData,
          backgroundColor: [CYAN, RED],
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom', labels: { padding: 16 } } },
        cutout: '70%',
      },
    });
  }

  const completionChartElement = document.getElementById('completionChart');
  if (completionChartElement) {
    new Chart(completionChartElement, {
      type: 'doughnut',
      data: {
        labels: ['Completed', 'Incomplete'],
        datasets: [{
          data: dashboardData.completionData,
          backgroundColor: [GREEN, NEUTRAL],
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        cutout: '72%',
      },
    });
  }

  const popularExChartElement = document.getElementById('popularExChart');
  if (popularExChartElement) {
    new Chart(popularExChartElement, {
      type: 'bar',
      data: {
        labels: dashboardData.popularEx.labels,
        datasets: [{
          label: 'Logs',
          data: dashboardData.popularEx.data,
          backgroundColor: PALETTE.map((color) => color + 'cc'),
          borderRadius: 6,
          borderSkipped: false,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: GRID }, beginAtZero: true, ticks: { precision: 0 } },
          y: { grid: { display: false } },
        },
      },
    });
  }

  const categoryChartElement = document.getElementById('categoryChart');
  if (categoryChartElement) {
    new Chart(categoryChartElement, {
      type: 'bar',
      data: {
        labels: dashboardData.category.labels,
        datasets: [{
          label: 'Logs',
          data: dashboardData.category.data,
          backgroundColor: VIOLET + 'bb',
          borderRadius: 6,
          borderSkipped: false,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: { grid: { color: GRID }, beginAtZero: true, ticks: { precision: 0 } },
        },
      },
    });
  }

  const foodChartElement = document.getElementById('foodChart');
  if (foodChartElement) {
    new Chart(foodChartElement, {
      type: 'bar',
      data: {
        labels: dashboardData.food.labels,
        datasets: [{
          label: 'Logs',
          data: dashboardData.food.data,
          backgroundColor: ORANGE + 'bb',
          borderRadius: 6,
          borderSkipped: false,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: GRID }, beginAtZero: true, ticks: { precision: 0 } },
          y: { grid: { display: false } },
        },
      },
    });
  }

  const foodSourceChartElement = document.getElementById('foodSourceChart');
  if (foodSourceChartElement) {
    new Chart(foodSourceChartElement, {
      type: 'pie',
      data: {
        labels: dashboardData.foodSource.labels,
        datasets: [{
          data: dashboardData.foodSource.data,
          backgroundColor: [BLUE, CYAN],
          borderWidth: 0,
          hoverOffset: 8,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom', labels: { padding: 16 } } },
      },
    });
  }

  const calorieCtx = document.getElementById('calorieChart')?.getContext('2d');
  if (calorieCtx) {
    new Chart(calorieCtx, {
      type: 'line',
      data: {
        labels: dashboardData.calories.labels,
        datasets: [{
          label: 'Total Calories',
          data: dashboardData.calories.data,
          borderColor: ORANGE,
          backgroundColor: makeGradient(calorieCtx, ORANGE),
          borderWidth: 2,
          pointRadius: 2,
          tension: 0.4,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: GRID } },
          y: { grid: { color: GRID }, beginAtZero: true },
        },
      },
    });
  }

  const goalChartElement = document.getElementById('goalChart');
  if (goalChartElement) {
    new Chart(goalChartElement, {
      type: 'pie',
      data: {
        labels: dashboardData.goal.labels,
        datasets: [{
          data: dashboardData.goal.data,
          backgroundColor: PALETTE,
          borderWidth: 0,
          hoverOffset: 8,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom', labels: { padding: 12 } } },
      },
    });
  }

  const fitnessChartElement = document.getElementById('fitnessChart');
  if (fitnessChartElement) {
    new Chart(fitnessChartElement, {
      type: 'doughnut',
      data: {
        labels: dashboardData.fitness.labels,
        datasets: [{
          data: dashboardData.fitness.data,
          backgroundColor: [GREEN, CYAN, VIOLET],
          borderWidth: 0,
          hoverOffset: 6,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom', labels: { padding: 14 } } },
        cutout: '60%',
      },
    });
  }

  const sections = document.querySelectorAll('section[id]');
  const navItems = document.querySelectorAll('.nav-item[href^="#"]');

  window.addEventListener('scroll', () => {
    let current = '';

    sections.forEach((section) => {
      if (window.scrollY >= section.offsetTop - 120) {
        current = section.id;
      }
    });

    navItems.forEach((item) => {
      item.classList.toggle('active', item.getAttribute('href') === `#${current}`);
    });
  }, { passive: true });
});
