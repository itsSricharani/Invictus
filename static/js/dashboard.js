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

  if (window._dataMode === 'demo') {
    alert('Export unavailable in demo mode. Only real scraped data can be exported.');
    return;
  }

  btn.classList.add('loading');
  btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation:spin 1s linear infinite"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Preparing…`;
  try {
    const resp = await fetch('/export/excel');
    if (!resp.ok) {
      let errMsg = `Server returned ${resp.status}`;
      try {
        const errJson = await resp.json();
        if (errJson.detail) errMsg = errJson.detail;
      } catch (_) {}
      throw new Error(errMsg);
    }
    const blob = await resp.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    // Use filename from Content-Disposition if available
    const cd   = resp.headers.get('Content-Disposition') || '';
    const match = cd.match(/filename=([^;]+)/);
    a.download  = match ? match[1].trim() : `apix_fare_data_${Date.now()}.xlsx`;
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
  if (!dateString) return '--';
  try {
    const d = new Date(dateString + (dateString.includes('T') ? '' : 'T00:00:00'));
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch (_) {
    return dateString;
  }
}

function formatTime(isoString) {
  if (!isoString) return '--';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    const today = new Date();
    const isToday = d.toDateString() === today.toDateString();
    const timeStr = d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
    return isToday ? `Today, ${timeStr}` : `${d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}, ${timeStr}`;
  } catch (_) {
    return isoString;
  }
}

/* ---- Count-up animation ---- */
function animateCountUp(element, target, duration = 1000) {
  if (!element || target == null || isNaN(target)) return;
  const start = performance.now();
  const from = 0;
  function step(now) {
    const p = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - p, 3); // ease-out cubic
    element.textContent = (from + (target - from) * eased).toFixed(2);
    if (p < 1) requestAnimationFrame(step);
    else element.textContent = Number(target).toFixed(2);
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
    { threshold: 0.01, rootMargin: '0px 0px 200px 0px' }
  );
  targets.forEach(t => observer.observe(t));

  // Safety fallback: force visibility on all reveal elements so nothing stays hidden
  setTimeout(() => {
    document.querySelectorAll('.reveal').forEach(t => t.classList.add('is-visible'));
  }, 200);
}


/* ---- Index section ---- */
function loadIndex(data) {
  if (!data) return;
  window._dataMode = data.data_mode;
  const indexEl = document.getElementById('national-index');

  if (indexEl && data.national_index != null) animateCountUp(indexEl, data.national_index);

  const baseDateEl = document.getElementById('base-date');
  if (baseDateEl && data.base_date) baseDateEl.textContent = formatDate(data.base_date);

  const currentPeriodEl = document.getElementById('current-period');
  if (currentPeriodEl && data.current_date) currentPeriodEl.textContent = formatDate(data.current_date);

  const currentDateEl = document.getElementById('current-date');
  if (currentDateEl && data.current_date) currentDateEl.textContent = formatDate(data.current_date);

  if (data.national_index != null) {
    const change = data.national_index - 100;
    const sign   = change >= 0 ? '+' : '';
    const changeEl = document.getElementById('index-change');
    if (changeEl) {
      changeEl.textContent = `${sign}${change.toFixed(2)} pts from base period`;
      if (change < 0) changeEl.classList.add('negative');
    }
  }
}

/* ---- Route cards ---- */
function loadRoutes(data) {
  const grid = document.getElementById('route-grid');
  if (!grid) return;
  grid.innerHTML = '';

  const entries = data && data.route_indices ? Object.entries(data.route_indices) : [];
  if (entries.length === 0) {
    grid.innerHTML = '<p class="error-state">No route data available.</p>';
    return;
  }

  entries.forEach(([route, value]) => {
    const change = value - 100;
    const sign   = change >= 0 ? '+' : '';
    const changeClass = change >= 0 ? 'positive' : 'negative';
    const formatted = route.replace('-', ' → ');

    const card = document.createElement('div');
    card.className = 'route-card';
    card.innerHTML = `
      <div class="route-name">${formatted}</div>
      <div class="route-value">${Number(value).toFixed(2)}</div>
      <div class="route-status ${changeClass}">${sign}${change.toFixed(2)} pts</div>
    `;
    grid.appendChild(card);
  });

  const routeCountEl = document.getElementById('route-count');
  if (routeCountEl) routeCountEl.textContent = entries.length;
}

/* ---- Lead-time cards ---- */
function loadLeadTimes(data) {
  const container = document.getElementById('lead-time-grid');
  if (!container) return;
  container.innerHTML = '';

  const entries = data && data.lead_time_indices ? Object.entries(data.lead_time_indices) : [];
  if (entries.length === 0) {
    container.innerHTML = '<p class="error-state">No lead-time data available.</p>';
    return;
  }

  entries.forEach(([label, value]) => {
    const card = document.createElement('div');
    card.className = 'lead-card';
    card.innerHTML = `
      <div class="lead-label">${label} Booking</div>
      <div class="lead-value">${Number(value).toFixed(2)}</div>
    `;
    container.appendChild(card);
  });
}

/* ---- History chart ---- */
let _historyChartInstance = null;

function loadHistoryChart(data) {
  const loadingEl = document.getElementById('chart-loading');
  if (loadingEl) loadingEl.remove();

  const container = document.getElementById('history-chart-container');
  if (!container) return;

  if (!data.history || data.history.length === 0) {
    container.innerHTML = '<div class="loading-placeholder">No historical data available yet.</div>';
    return;
  }

  let canvas = document.getElementById('history-chart');
  if (!canvas) {
    container.innerHTML = '<canvas id="history-chart"></canvas>';
    canvas = document.getElementById('history-chart');
  }

  if (_historyChartInstance) {
    _historyChartInstance.destroy();
    _historyChartInstance = null;
  }

  const labels = data.history.map(d => formatDate(d.date));
  const values = data.history.map(d => d.index);

  const ctx = canvas.getContext('2d');

  // Gradient fill
  const gradient = ctx.createLinearGradient(0, 0, 0, 280);
  gradient.addColorStop(0, 'rgba(56, 189, 248, 0.18)');
  gradient.addColorStop(1, 'rgba(56, 189, 248, 0)');

  _historyChartInstance = new Chart(ctx, {
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

  // Load Sector Heatmap and Backtest chart dynamically
  loadHeatmap();
  loadBacktestChart();

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

/* ============================================================
   Chart View Toggle
   ============================================================ */
let _ltChartInstance  = null;   // Track Chart.js instance so we can destroy & redraw
let _ltChartLastRoute = null;   // Prevent redundant fetches when route unchanged

function switchChartView(view) {
  const trendBtn    = document.getElementById('btn-trend');
  const leadBtn     = document.getElementById('btn-leadtime');
  const trendView   = document.getElementById('view-trend');
  const leadView    = document.getElementById('view-leadtime');
  const titleEl     = document.getElementById('chart-section-title');

  if (view === 'trend') {
    trendBtn.classList.add('active');
    leadBtn.classList.remove('active');
    trendView.style.display = '';
    leadView.style.display  = 'none';
    if (titleEl) titleEl.textContent = 'Aeir Index Trend';
  } else {
    leadBtn.classList.add('active');
    trendBtn.classList.remove('active');
    trendView.style.display = 'none';
    leadView.style.display  = '';
    if (titleEl) titleEl.textContent = 'Fare by Booking Window';
    setTimeout(() => {
      loadLeadTimeChart();
    }, 50);
  }
}

/* ============================================================
   Keepa-style Lead-Time Chart
   ============================================================ */

// Lines to render (T+1 gets gradient fill; others plain strokes)
// Architectured so T+30 / T+45 can be uncommented later
const LT_WINDOWS = [
  { key: 'T+1',  label: 'Book 1 day before',  color: '#F5F7FA' },  // white/top line
  { key: 'T+7',  label: 'Book 7 days before', color: '#7DD3FC' },  // blue-mid
  { key: 'T+15', label: 'Book 15 days before',color: '#38BDF8',  dash: [3, 3] },  // blue-dotted
  // { key: 'T+30', label: 'Book 30 days before', color: '#34D399', dash: [4, 4] },
  // { key: 'T+45', label: 'Book 45 days before', color: '#FBBF24', dash: [4, 4] },
];

function formatRupee(v) {
  if (v == null) return '—';
  return '\u20B9' + v.toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

async function loadLeadTimeChart() {
  const select    = document.getElementById('lt-route-select');
  const route     = select ? select.value : 'DEL-BOM';
  const container = document.getElementById('lt-chart-container');
  const legendEl  = document.getElementById('lt-legend');
  let loadingEl   = document.getElementById('lt-chart-loading');

  if (!container) return;

  // Show skeleton while fetching
  if (loadingEl) loadingEl.style.display = '';

  let data;
  try {
    data = await fetchData(`/lead-time-history?route=${encodeURIComponent(route)}`);
  } catch (err) {
    console.error('[Aeir] Lead-time history fetch failed:', err);
    container.innerHTML = `<div class="error-state">Unable to load lead-time data.<br><button class="retry-btn" onclick="loadLeadTimeChart()">Retry</button></div>`;
    return;
  }

  if (loadingEl) loadingEl.style.display = 'none';

  const dates  = data.dates  || [];
  const series = data.series || {};

  let canvas = document.getElementById('lt-chart');
  if (!canvas) {
    container.innerHTML = '<canvas id="lt-chart"></canvas><div class="loading-placeholder" id="lt-chart-loading" style="display:none;"></div>';
    canvas = document.getElementById('lt-chart');
  }

  if (dates.length === 0) {
    container.innerHTML = '<div class="loading-placeholder" style="height:100%">No real data for this route yet.</div>';
    return;
  }

  // Destroy previous Chart.js instance
  if (_ltChartInstance) {
    _ltChartInstance.destroy();
    _ltChartInstance = null;
  }


  const ctx = canvas.getContext('2d');


  // Build gradient for the topmost line (T+1) only
  const topColor = LT_WINDOWS[0].color;
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  // Parse hex → rgba helper
  function hexAlpha(hex, a) {
    const r = parseInt(hex.slice(1,3),16);
    const g = parseInt(hex.slice(3,5),16);
    const b = parseInt(hex.slice(5,7),16);
    return `rgba(${r},${g},${b},${a})`;
  }
  gradient.addColorStop(0, hexAlpha(topColor, 0.18));
  gradient.addColorStop(1, hexAlpha(topColor, 0));

  // Build chart datasets
  const datasets = LT_WINDOWS.map((w, idx) => {
    const vals = series[w.key] || Array(dates.length).fill(null);
    return {
      label:           w.label,
      data:            vals,
      borderColor:     w.color,
      borderWidth:     idx === 0 ? 2 : 1.5,
      borderDash:      w.dash || [],
      stepped:         true,               // ← Keepa flat-step style
      fill:            idx === 0,          // only topmost line gets fill
      backgroundColor: idx === 0 ? gradient : 'transparent',
      pointRadius:     0,                  // no dots at data points (Keepa style)
      pointHoverRadius:5,
      pointHoverBackgroundColor: w.color,
      spanGaps:        true,               // don't break line at null gaps
      tension:         0,                  // must be 0 for stepped
    };
  });

  const labels = dates.map(d => {
    const dt = new Date(d + 'T00:00:00');
    return dt.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
  });

  // Custom external tooltip (floating card near cursor)
  const tooltipEl = document.getElementById('lt-tooltip');

  function customTooltipHandler(context) {
    const { chart, tooltip } = context;
    if (!tooltipEl) return;

    if (tooltip.opacity === 0) {
      tooltipEl.style.display = 'none';
      return;
    }

    const dateLabel = tooltip.title?.[0] ?? '';

    let html = `<div class="lt-tooltip-date">${dateLabel}</div>`;
    tooltip.dataPoints.forEach(pt => {
      const dsIdx  = pt.datasetIndex;
      const w      = LT_WINDOWS[dsIdx];
      if (!w) return;
      const val = pt.raw;
      if (val == null) return;
      html += `
        <div class="lt-tooltip-row">
          <div class="lt-tooltip-row-left">
            <span class="lt-tooltip-dot" style="background:${w.color}"></span>
            <span>${w.key}</span>
          </div>
          <span class="lt-tooltip-value">${formatRupee(val)}</span>
        </div>`;
    });
    tooltipEl.innerHTML = html;

    // Position the tooltip near the cursor but keep inside the viewport
    const { left, top } = chart.canvas.getBoundingClientRect();
    const ttW = tooltipEl.offsetWidth  || 200;
    const ttH = tooltipEl.offsetHeight || 100;
    const x   = tooltip.caretX + left;
    const y   = tooltip.caretY + top;

    const clampedX = Math.min(x + 14, window.innerWidth  - ttW - 12);
    const clampedY = Math.min(y - 20,  window.innerHeight - ttH - 12);

    tooltipEl.style.left    = `${Math.max(8, clampedX)}px`;
    tooltipEl.style.top     = `${Math.max(8, clampedY)}px`;
    tooltipEl.style.display = 'block';
  }

  // Build chart
  _ltChartInstance = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      animation:           { duration: 600, easing: 'easeOutQuart' },
      interaction:         { intersect: false, mode: 'index' },
      plugins: {
        legend:  { display: false },    // we render our own legend pills
        tooltip: {
          enabled: false,              // disable built-in tooltip
          external: customTooltipHandler,
        },
      },
      scales: {
        x: {
          grid:   { color: 'rgba(255,255,255,0.04)' },
          ticks:  { color: PALETTE.muted, font: { size: 11 }, maxRotation: 0, maxTicksLimit: 8 },
          border: { color: 'rgba(255,255,255,0.06)' },
        },
        y: {
          grid:          { color: 'rgba(255,255,255,0.04)' },
          ticks:         {
            color: PALETTE.muted,
            font:  { size: 11 },
            callback: v => '\u20B9' + v.toLocaleString('en-IN'),
          },
          border:        { color: 'rgba(255,255,255,0.06)' },
          beginAtZero:   false,
        },
      },
    },
  });

  // Hide tooltip when mouse leaves chart area
  canvas.addEventListener('mouseleave', () => {
    if (tooltipEl) tooltipEl.style.display = 'none';
  });

  // Render legend pills
  if (legendEl) {
    legendEl.innerHTML = '';
    LT_WINDOWS.forEach(w => {
      const vals = (series[w.key] || []).filter(v => v != null);
      const latest = vals.length ? vals[vals.length - 1] : null;
      const pill = document.createElement('div');
      pill.className = 'lt-legend-pill';
      pill.innerHTML = `
        <span class="lt-legend-dot" style="background:${w.color}"></span>
        <span>${w.key}</span>
        <strong>${latest != null ? formatRupee(latest) : '—'}</strong>
      `;
      legendEl.appendChild(pill);
    });
  }

  _ltChartLastRoute = route;
}

/* ============================================================
   Sector-Wise Heatmap Implementation
   ============================================================ */
async function loadHeatmap() {
  const container = document.getElementById('heatmap-grid');
  if (!container) return;

  try {
    const data = await fetchData('/sector-heatmap');
    const days = data.days || ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const routes = data.routes || [];
    const heatmap = data.heatmap || {};

    if (routes.length === 0) {
      container.innerHTML = '<div class="error-state" style="grid-column: 1 / -1;">No route heatmap data available.</div>';
      return;
    }

    // Collect values to calculate intensity scale
    const allVals = [];
    routes.forEach(r => {
      days.forEach(d => {
        const v = heatmap[r]?.[d];
        if (v != null) allVals.push(v);
      });
    });

    const minVal = allVals.length ? Math.min(...allVals) : 100;
    const maxVal = allVals.length ? Math.max(...allVals) : 120;

    let html = '<div class="heatmap-header-cell"></div>';
    days.forEach(day => {
      html += `<div class="heatmap-header-cell">${day}</div>`;
    });

    routes.forEach(route => {
      html += `<div class="heatmap-route-label">${route}</div>`;
      days.forEach(day => {
        const val = heatmap[route]?.[day];
        if (val == null) {
          html += `<div class="heatmap-cell empty">--</div>`;
        } else {
          // Normalize 0..1 range for intensity classes 1..4
          let intensityClass = 'heatmap-cell-intensity-2';
          if (maxVal > minVal) {
            const ratio = (val - minVal) / (maxVal - minVal);
            if (ratio < 0.25) intensityClass = 'heatmap-cell-intensity-1';
            else if (ratio < 0.55) intensityClass = 'heatmap-cell-intensity-2';
            else if (ratio < 0.85) intensityClass = 'heatmap-cell-intensity-3';
            else intensityClass = 'heatmap-cell-intensity-4';
          }
          html += `<div class="heatmap-cell ${intensityClass}" title="${route} (${day}): Index ${val}">${val}</div>`;
        }
      });
    });

    container.innerHTML = html;

  } catch (err) {
    console.error('[Aeir] Heatmap loading failed:', err);
    container.innerHTML = `<div class="error-state" style="grid-column: 1 / -1;">Unable to load heatmap.</div>`;
  }
}

/* ============================================================
   Back-Test: APIx vs DGCA Implementation
   ============================================================ */
let _backtestChartInstance = null;

async function loadBacktestChart() {
  const container = document.getElementById('backtest-chart-container');
  if (!container) return;

  const loadingEl = document.getElementById('backtest-loading');

  try {
    const data = await fetchData('/backtest-index');
    if (loadingEl) loadingEl.remove();

    if (!data.apix || data.apix.length === 0) {
      container.innerHTML = '<div class="loading-placeholder">No back-test comparison data available yet.</div>';
      return;
    }

    let canvas = document.getElementById('backtest-chart');
    if (!canvas) {
      container.innerHTML = '<canvas id="backtest-chart"></canvas>';
      canvas = document.getElementById('backtest-chart');
    }

    if (_backtestChartInstance) {
      _backtestChartInstance.destroy();
      _backtestChartInstance = null;
    }

    const ctx = canvas.getContext('2d');

    _backtestChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: data.labels,
        datasets: [
          {
            label: 'APIx (Daily High-Freq)',
            data: data.apix,
            borderColor: PALETTE.accent,
            borderWidth: 2,
            tension: 0.35,
            pointRadius: 3,
            pointBackgroundColor: PALETTE.accent,
            fill: false,
          },
          {
            label: 'DGCA Benchmark (Monthly)',
            data: data.dgca,
            borderColor: '#FB923C', // Warm orange
            borderWidth: 2,
            borderDash: [5, 5],
            stepped: 'before',
            pointRadius: 0,
            fill: false,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 800, easing: 'easeOutQuart' },
        interaction: { intersect: false, mode: 'index' },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            align: 'end',
            labels: {
              color: PALETTE.textSec,
              font: { size: 11, family: 'Inter' },
              boxWidth: 14,
              usePointStyle: true,
            }
          },
          tooltip: {
            backgroundColor: '#14243A',
            borderColor: PALETTE.border,
            borderWidth: 1,
            titleColor: PALETTE.textSec,
            bodyColor: PALETTE.textPrim,
            padding: 10,
            callbacks: {
              title: ctx => `Period: ${data.dates[ctx[0].dataIndex]} (${ctx[0].label})`,
              label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}`
            }
          }
        },
        scales: {
          x: {
            grid: { color: 'rgba(255,255,255,0.04)' },
            ticks: { color: PALETTE.muted, font: { size: 11 }, maxTicksLimit: 8 },
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

  } catch (err) {
    console.error('[Aeir] Back-test chart loading failed:', err);
    if (loadingEl) loadingEl.remove();
    container.innerHTML = '<div class="error-state">Unable to load back-test benchmark chart.</div>';
  }
}

