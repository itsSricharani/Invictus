/* ============================================================
   landing.js — Aeir Landing Page Logic
   ============================================================ */

/* ---- Scroll reveal (IntersectionObserver) ---- */
function initReveal() {
  const targets = document.querySelectorAll('.reveal');
  const observer = new IntersectionObserver(
    (entries) => entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add('is-visible');
        observer.unobserve(e.target);
      }
    }),
    { threshold: 0.12 }
  );
  targets.forEach((t) => observer.observe(t));
}

/* ---- Populate "Index at a glance" from API ---- */
async function loadGlanceData() {
  try {
    const data = await fetch('/index').then(r => { if (!r.ok) throw new Error(); return r.json(); });

    const indexEl  = document.getElementById('glance-index');
    const changeEl = document.getElementById('glance-change');

    if (indexEl)  indexEl.textContent  = data.national_index?.toFixed(2) ?? '--';

    const change = (data.national_index ?? 100) - 100;
    const sign   = change >= 0 ? '+' : '';
    if (changeEl) {
      changeEl.textContent = `${sign}${change.toFixed(2)} pts from base period`;
      changeEl.style.color = change >= 0 ? 'var(--positive)' : 'var(--negative)';
    }
  } catch (_) {
    const indexEl = document.getElementById('glance-index');
    if (indexEl) indexEl.textContent = '--';
  }
}

/* ---- Populate last collection time ---- */
async function loadStatusData() {
  try {
    const status = await fetch('/system-status').then(r => { if (!r.ok) throw new Error(); return r.json(); });
    const timeEl = document.getElementById('glance-time');
    if (timeEl) {
      const d = new Date(status.last_checked ?? status.latest_data_date);
      const today = new Date();
      const isToday = d.toDateString() === today.toDateString();
      const timeStr = d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
      timeEl.textContent = isToday
        ? `Today, ${timeStr}`
        : d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) + `, ${timeStr}`;
    }
  } catch (_) {}
}

/* ---- Init ---- */
document.addEventListener('DOMContentLoaded', () => {
  initReveal();
  loadGlanceData();
  loadStatusData();
});