/* ============================================================
   dashboard.js — Aeir Dashboard Data & Charts
   ============================================================ */

const PALETTE = {
  accent:    '#38BDF8',
  accent2:   '#7DD3FC',
  positive:  '#34D399',
  negative:  '#FB7185',
  muted:     '#64748B',
  border:    'rgba(255,255,255,0.08)',
  surface:   '#101D30',
  textPrim:  '#F5F7FA',
  textSec:   '#9AA8BA',
};

/* ---- Excel Export ---- */
async function triggerExport() {
  const btn = document.getElementById('export-btn');
  if (!btn) return;
  btn.classList.add('loading');
  btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation:spin 1s linear infinite"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Preparing…`;
  try {
    const resp = await fetch('/export');
    if (!resp.ok) throw new Error(`Server returned ${resp.status}`);
    const blob = await resp.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    // Use filename from Content-Disposition if available
    const cd   = resp.headers.get('Content-Disposition') || '';
    const match = cd.match(/filename=([^;]+)/);
    a.download  = match ? match[1].trim() : `aeir_export_${Date.now()}.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert('Export failed: ' + err.message);
  } finally {
    btn.classList.remove('loading');
    btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg> Download Data`;
  }
}

/* ---- Fetch helpers ---- */
async function fetchData(endpoint) {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error(`HTTP ${response.status} from ${endpoint}`);
  return response.json();
}

function formatDate(dateString) {
  const d = new Date(dateString + 'T00:00:00');
  return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatTime(isoString) {
  if (!isoString) return '--';
  const d = new Date(isoString);
  const today = new Date();
  const isToday = d.toDateString() === today.toDateString();
  const timeStr = d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
  return isToday ? `Today, ${timeStr}` : `${d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}, ${timeStr}`;
}

/* ---- Count-up animation ---- */
function animateCountUp(element, target, duration = 1000) {
  const start = performance.now();
  const from = 0;
  function step(now) {
    const p = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - p, 3); // ease-out cubic
    element.textContent = (from + (target - from) * eased).toFixed(2);
    if (p < 1) requestAnimationFrame(step);
    else element.textContent = target.toFixed(2);
  }
  requestAnimationFrame(step);
}

/* ---- Scroll reveal ---- */
function initScrollReveal() {
  const targets = document.querySelectorAll('.reveal');
  const observer = new IntersectionObserver(
    entries => entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('is-visible'); observer.unobserve(e.target); }
    }),
    { threshold: 0.12 }
  );
  targets.forEach(t => observer.observe(t));
}

/* ---- Index section ---- */
function loadIndex(data) {
  // Animate the big number
  const indexEl = document.getElementById('national-index');
  animateCountUp(indexEl, data.national_index);

  document.getElementById('base-date').textContent     = formatDate(data.base_date);
  document.getElementById('current-period').textContent = formatDate(data.current_date);
  document.getElementById('current-date').textContent   = formatDate(data.current_date);

  const change = data.national_index - 100;
  const sign   = change >= 0 ? '+' : '';
  const changeEl = document.getElementById('index-change');
  changeEl.textContent = `${sign}${change.toFixed(2)} pts from base period`;
  if (change < 0) changeEl.classList.add('negative');
}

/* ---- Route cards ---- */
function loadRoutes(data) {
  const grid = document.getElementById('route-grid');
  grid.innerHTML = '';

  const entries = Object.entries(data.route_indices);
  if (entries.length === 0) {
    grid.innerHTML = '<p class="error-state">No route data available.</p>';
    return;
  }

  entries.forEach(([route, value]) => {
    const change = value - 100;
    const sign   = change >= 0 ? '+' : '';
    const changeClass = change >= 0 ? 'positive' : 'negative';
    // Format "DEL-BOM" → "DEL → BOM"
    const formatted = route.replace('-', ' → ');

    const card = document.createElement('div');
    card.className = 'route-card';
    card.innerHTML = `
      <div class="route-name">${formatted}</div>
      <div class="route-value">${value.toFixed(2)}</div>
      <div class="route-status ${changeClass}">${sign}${change.toFixed(2)} pts</div>
    `;
    grid.appendChild(card);
  });

  // Update route count from index data
  const routeCountEl = document.getElementById('route-count');
  if (routeCountEl) routeCountEl.textContent = entries.length;
}

/* ---- Lead-time cards ---- */
function loadLeadTimes(data) {
  const container = document.getElementById('lead-time-grid');
  container.innerHTML = '';

  const entries = Object.entries(data.lead_time_indices);
  if (entries.length === 0) {
    container.innerHTML = '<p class="error-state">No lead-time data available.</p>';
    return;
  }

  entries.forEach(([label, value]) => {
    const card = document.createElement('div');
    card.className = 'lead-card';
    card.innerHTML = `
      <div class="lead-label">${label} Booking</div>
      <div class="lead-value">${value.toFixed(2)}</div>
    `;
    container.appendChild(card);
  });
}

/* ---- History chart ---- */
function loadHistoryChart(data) {
  const loadingEl = document.getElementById('chart-loading');
  if (loadingEl) loadingEl.remove();

  if (!data.history || data.history.length === 0) {
    document.getElementById('history-chart-container').innerHTML =
      '<div class="loading-placeholder">No historical data available yet.</div>';
    return;
  }

  const labels = data.history.map(d => formatDate(d.date));
  const values = data.history.map(d => d.index);

  const ctx = document.getElementById('history-chart').getContext('2d');

  // Gradient fill
  const gradient = ctx.createLinearGradient(0, 0, 0, 280);
  gradient.addColorStop(0, 'rgba(56, 189, 248, 0.18)');
  gradient.addColorStop(1, 'rgba(56, 189, 248, 0)');

  new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'National APIx',
        data: values,
        borderColor: PALETTE.accent,
        borderWidth: 2,
        backgroundColor: gradient,
        fill: true,
        tension: 0.35,
        pointRadius: values.length <= 15 ? 4 : 2,
        pointBackgroundColor: PALETTE.accent,
        pointBorderColor: PALETTE.surface,
        pointBorderWidth: 2,
        pointHoverRadius: 6,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 800, easing: 'easeOutQuart' },
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#14243A',
          borderColor: PALETTE.border,
          borderWidth: 1,
          titleColor: PALETTE.textSec,
          bodyColor: PALETTE.textPrim,
          padding: 12,
          displayColors: false,
          callbacks: {
            label: ctx => `APIx: ${ctx.parsed.y.toFixed(2)}`,
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: PALETTE.muted, font: { size: 11 }, maxRotation: 0, maxTicksLimit: 8 },
          border: { color: 'rgba(255,255,255,0.06)' },
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.04)' },
          ticks: { color: PALETTE.muted, font: { size: 11 } },
          border: { color: 'rgba(255,255,255,0.06)' },
          beginAtZero: false,
        }
      }
    }
  });
}

/* ---- System status strip ---- */
async function loadSystemStatus() {
  try {
    const data = await fetchData('/system-status');
    const recordsEl  = document.getElementById('status-records');
    const routesEl   = document.getElementById('status-routes');
    const nextRunEl  = document.getElementById('status-next-run');
    const statusLabel = document.getElementById('data-status-label');

    if (recordsEl)  recordsEl.textContent  = data.total_records ?? '--';
    if (routesEl)   routesEl.textContent   = data.routes_monitored ?? '--';
    if (nextRunEl)  nextRunEl.textContent  = data.next_collection ? formatTime(data.next_collection) : 'N/A';
    if (statusLabel) statusLabel.textContent = data.scheduler_status === 'LIVE' ? 'LIVE' : 'OFFLINE';
  } catch (err) {
    console.warn('[Aeir] System status unavailable:', err.message);
  }
}

/* ---- Main loader ---- */
async function loadDashboard() {
  const [indexResult, historyResult, leadTimeResult] = await Promise.allSettled([
    fetchData('/index'),
    fetchData('/index/history'),
    fetchData('/lead-times'),
  ]);

  if (indexResult.status === 'fulfilled') {
    loadIndex(indexResult.value);
    loadRoutes(indexResult.value);
  } else {
    console.error('[Aeir] Index endpoint failed:', indexResult.reason);
    const indexEl = document.getElementById('national-index');
    if (indexEl) indexEl.textContent = 'N/A';
    const changeEl = document.getElementById('index-change');
    if (changeEl) { changeEl.textContent = 'Unable to retrieve the latest index.'; changeEl.style.color = 'var(--text-muted)'; }
    document.getElementById('route-grid').innerHTML =
      `<div class="error-state">Unable to load route data.<br><button class="retry-btn" onclick="loadDashboard()">Retry</button></div>`;
  }

  if (historyResult.status === 'fulfilled') {
    loadHistoryChart(historyResult.value);
  } else {
    const chartContainer = document.getElementById('history-chart-container');
    if (chartContainer) {
      chartContainer.innerHTML =
        `<div class="error-state">Unable to retrieve chart data.<br><button class="retry-btn" onclick="loadDashboard()">Retry</button></div>`;
    }
  }

  if (leadTimeResult.status === 'fulfilled') {
    loadLeadTimes(leadTimeResult.value);
  } else {
    const ltGrid = document.getElementById('lead-time-grid');
    if (ltGrid) ltGrid.innerHTML = '<div class="error-state">Lead-time data unavailable.</div>';
  }

  // Also populate source count from /summary if available
  try {
    const summary = await fetchData('/summary');
    const srcEl = document.getElementById('source-count');
    if (srcEl && summary.data_quality) srcEl.textContent = summary.data_quality.sources ?? '--';
  } catch (_) {}
}

document.addEventListener('DOMContentLoaded', () => {
  initScrollReveal();
  loadSystemStatus();
  loadDashboard();
});