document.addEventListener('DOMContentLoaded', () => {
  const dataElement = document.getElementById('admin-dashboard-data');

  if (!dataElement || typeof Chart === 'undefined') {
    return;
  }

  const dashboardData = JSON.parse(dataElement.textContent);

  Chart.defaults.color = '#6b6b80';
  Chart.defaults.borderColor = '#23232e';
  Chart.defaults.font.family = "'DM Mono', monospace";
  Chart.defaults.font.size = 11;

  const LIME = '#c8f135';
  const VIOLET = '#7c6af7';
  const ORANGE = '#f97316';
  const CYAN = '#22d3ee';
  const RED = '#f43f5e';
  const GREEN = '#4ade80';
  const PALETTE = [LIME, VIOLET, ORANGE, CYAN, RED, GREEN, '#fb923c', '#a78bfa', '#34d399', '#f472b6'];

  function makeGradient(ctx, color) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, color + '55');
    gradient.addColorStop(1, color + '00');
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
          borderColor: LIME,
          backgroundColor: makeGradient(regCtx, LIME),
          borderWidth: 2,
          pointBackgroundColor: LIME,
          pointRadius: 3,
          tension: 0.4,
          fill: true,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: '#23232e' } },
          y: { grid: { color: '#23232e' }, beginAtZero: true, ticks: { precision: 0 } },
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

  new Chart(document.getElementById('activeChart'), {
    type: 'doughnut',
    data: {
      labels: ['Active', 'Inactive'],
      datasets: [{
        data: dashboardData.activeData,
        backgroundColor: [GREEN, '#23232e'],
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

  new Chart(document.getElementById('retentionChart'), {
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

  new Chart(document.getElementById('completionChart'), {
    type: 'doughnut',
    data: {
      labels: ['Completed', 'Incomplete'],
      datasets: [{
        data: dashboardData.completionData,
        backgroundColor: [GREEN, '#23232e'],
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

  new Chart(document.getElementById('popularExChart'), {
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
        x: { grid: { color: '#23232e' }, beginAtZero: true, ticks: { precision: 0 } },
        y: { grid: { display: false } },
      },
    },
  });

  new Chart(document.getElementById('categoryChart'), {
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
        y: { grid: { color: '#23232e' }, beginAtZero: true, ticks: { precision: 0 } },
      },
    },
  });

  new Chart(document.getElementById('foodChart'), {
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
        x: { grid: { color: '#23232e' }, beginAtZero: true, ticks: { precision: 0 } },
        y: { grid: { display: false } },
      },
    },
  });

  new Chart(document.getElementById('foodSourceChart'), {
    type: 'pie',
    data: {
      labels: dashboardData.foodSource.labels,
      datasets: [{
        data: dashboardData.foodSource.data,
        backgroundColor: [LIME, CYAN],
        borderWidth: 0,
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom', labels: { padding: 16 } } },
    },
  });

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
          x: { grid: { color: '#23232e' } },
          y: { grid: { color: '#23232e' }, beginAtZero: true },
        },
      },
    });
  }

  new Chart(document.getElementById('goalChart'), {
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

  new Chart(document.getElementById('fitnessChart'), {
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
