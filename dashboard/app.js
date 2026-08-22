// Förder-Radar – Dashboard (Alpine.js + Chart.js)
// Pure client-side, no build step, no server.
// Data: fetch('data/catalog.json'), fetch('data/sources.json')

function dashboard() {
  return {
    // --- State ---
    catalog: [],
    sources: {},
    loading: true,
    error: null,
    stand: '',

    // Filters
    search: '',
    kategorie: '',
    status: '',
    karriere: '',

    // Sorting
    sortKey: 'name',
    sortDir: 1,
    srcSortKey: 'name',
    srcSortDir: 1,

    // Charts
    _catChart: null,
    _statusChart: null,
    _deadlineChart: null,

    // --- Init ---
    async init() {
      try {
        const [catRes, srcRes] = await Promise.all([
          fetch('data/catalog.json').then(r => { if (!r.ok) throw new Error('catalog.json: ' + r.status); return r.json(); }),
          fetch('data/sources.json').then(r => { if (!r.ok) throw new Error('sources.json: ' + r.status); return r.json(); }),
        ]);
        this.catalog = catRes.programme || [];
        this.stand = catRes.stand || '';
        this.sources = srcRes || {};
        this.loading = false;
        this.$nextTick(() => this.renderCharts());
      } catch (e) {
        this.error = 'Daten konnten nicht geladen werden: ' + e.message;
        this.loading = false;
      }
    },

    // --- Computed ---
    get categories() {
      return [...new Set(this.catalog.map(p => p.kategorie))].sort();
    },

    get filtered() {
      let result = this.catalog.filter(p => {
        if (this.search) {
          const q = this.search.toLowerCase();
          const inName = (p.name || '').toLowerCase().includes(q);
          const inThemen = (p.themen || []).some(t => t.toLowerCase().includes(q));
          if (!inName && !inThemen) return false;
        }
        if (this.kategorie && p.kategorie !== this.kategorie) return false;
        if (this.status && p.status !== this.status) return false;
        if (this.karriere && !(p.karriere || []).includes(this.karriere)) return false;
        return true;
      });
      // Sort
      result = result.sort((a, b) => {
        let va = a[this.sortKey], vb = b[this.sortKey];
        if (this.sortKey === 'frist') {
          va = va || '9999';
          vb = vb || '9999';
        }
        if (this.sortKey === 'budget_max') {
          va = va || 0;
          vb = vb || 0;
        }
        if (typeof va === 'string') va = va.toLowerCase();
        if (typeof vb === 'string') vb = vb.toLowerCase();
        if (va < vb) return -1 * this.sortDir;
        if (va > vb) return 1 * this.sortDir;
        return 0;
      });
      return result;
    },

    get upcomingDeadlines() {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const in90 = new Date(today.getTime() + 90 * 24 * 60 * 60 * 1000);
      return this.catalog
        .filter(p => {
          if (!p.frist) return false;
          const d = new Date(p.frist);
          return d >= today && d <= in90;
        })
        .sort((a, b) => new Date(a.frist) - new Date(b.frist));
    },

    get sortedSources() {
      const entries = Object.entries(this.sources).map(([key, v]) => ({
        key,
        name: v.name || key,
        url: v.url || '',
        type: v.type || 'manual',
        update_frequency: v.update_frequency || '',
        last_check: v.last_check || '',
        calls: v.calls || [],
        programs: v.programs || [],
      }));
      return entries.sort((a, b) => {
        const va = a[this.srcSortKey] || '';
        const vb = b[this.srcSortKey] || '';
        if (typeof va === 'string') va = va.toLowerCase();
        if (typeof vb === 'string') vb = vb.toLowerCase();
        if (va < vb) return -1 * this.srcSortDir;
        if (va > vb) return 1 * this.srcSortDir;
        return 0;
      });
    },

    // --- Sorting ---
    toggleSort(key) {
      if (this.sortKey === key) {
        this.sortDir *= -1;
      } else {
        this.sortKey = key;
        this.sortDir = 1;
      }
    },

    toggleSortSrc(key) {
      if (this.srcSortKey === key) {
        this.srcSortDir *= -1;
      } else {
        this.srcSortKey = key;
        this.sortDir = 1;
      }
    },

    // --- Charts ---
    cssVar(name, fallback) {
      const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
      return v || fallback;
    },

    renderCharts() {
      const text = this.cssVar('--text', '#222');
      const textMuted = this.cssVar('--text-muted', '#5f5f5f');
      const bg = this.cssVar('--bg', '#fff');
      const cardBg = this.cssVar('--card-bg', '#fafafa');
      const gridColor = this.cssVar('--chart-grid', 'rgba(136,136,136,0.25)');
      const borderColor = this.cssVar('--chart-border', 'rgba(136,136,136,0.5)');
      const tooltipBg = this.cssVar('--card-bg', '#fafafa');
      const tooltipText = this.cssVar('--text', '#222');
      const catColors = [
        this.cssVar('--c1', '#007a3d'), this.cssVar('--c2', '#1a5fb4'),
        this.cssVar('--c3', '#c0392b'), this.cssVar('--c4', '#8a6500'),
        this.cssVar('--c5', '#6f42c1'), this.cssVar('--c6', '#e83e8c'),
        this.cssVar('--c7', '#20c997'), this.cssVar('--c8', '#fd7e14'),
        this.cssVar('--c9', '#495057'),
      ];
      const statusColors = {
        verifiziert: this.cssVar('--green-bg', '#007a3d'),
        laufend: this.cssVar('--blue-bg', '#1a5fb4'),
        'zu-pruefen': this.cssVar('--amber-bg', '#8a6500'),
      };
      const statusLabels = {
        verifiziert: 'Verifiziert',
        laufend: 'Laufend',
        'zu-pruefen': 'Zu prüfen',
      };
      const tooltipOpts = {
        backgroundColor: tooltipBg,
        titleColor: tooltipText,
        bodyColor: tooltipText,
        borderColor: gridColor,
        borderWidth: 1,
        padding: 10,
        cornerRadius: 6,
        displayColors: true,
      };
      const scaleOpts = {
        grid: { color: gridColor },
        ticks: { color: textMuted },
        border: { color: borderColor },
      };

      // Category doughnut
      const cats = {};
      this.catalog.forEach(p => { cats[p.kategorie] = (cats[p.kategorie] || 0) + 1; });
      if (this._catChart) this._catChart.destroy();
      this._catChart = new Chart(document.getElementById('catChart'), {
        type: 'doughnut',
        data: {
          labels: Object.keys(cats),
          datasets: [{
            data: Object.values(cats),
            backgroundColor: catColors.slice(0, Object.keys(cats).length),
            borderColor: bg,
            borderWidth: 2,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: { color: text, usePointStyle: true, padding: 12, font: { size: 11 } },
            },
            tooltip: { ...tooltipOpts, callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} Programme` } },
          },
        },
      });

      // Status bar (horizontal for readability)
      const stats = {};
      this.catalog.forEach(p => { stats[p.status] = (stats[p.status] || 0) + 1; });
      const statLabels = Object.keys(stats).map(k => statusLabels[k] || k);
      if (this._statusChart) this._statusChart.destroy();
      this._statusChart = new Chart(document.getElementById('statusChart'), {
        type: 'bar',
        data: {
          labels: statLabels,
          datasets: [{
            label: 'Programme',
            data: Object.values(stats),
            backgroundColor: Object.keys(stats).map(k => statusColors[k] || '#999'),
            borderRadius: 4,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { ...tooltipOpts, callbacks: { label: ctx => ` ${ctx.parsed.x ?? ctx.parsed.y} Programme` } },
          },
          scales: {
            x: { ...scaleOpts, beginAtZero: true, title: { display: true, text: 'Programme', color: textMuted } },
            y: { ...scaleOpts },
          },
        },
      });

      // Deadline timeline (next 90 days, top 10)
      const upcoming = this.upcomingDeadlines.slice(0, 10);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (this._deadlineChart) this._deadlineChart.destroy();
      this._deadlineChart = new Chart(document.getElementById('deadlineChart'), {
        type: 'bar',
        data: {
          labels: upcoming.map(p => p.name.length > 45 ? p.name.slice(0, 42) + '…' : p.name),
          datasets: [{
            label: 'Tage bis Frist',
            data: upcoming.map(p => Math.ceil((new Date(p.frist) - today) / (24 * 60 * 60 * 1000))),
            backgroundColor: upcoming.map(p => {
              const days = Math.ceil((new Date(p.frist) - today) / (24 * 60 * 60 * 1000));
              if (days <= 14) return this.cssVar('--red-bg', '#c0392b');
              if (days <= 30) return this.cssVar('--orange', '#b85d00');
              return this.cssVar('--green-bg', '#007a3d');
            }),
            borderRadius: 4,
          }],
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              ...tooltipOpts,
              callbacks: {
                title: ctx => upcoming[ctx[0].dataIndex].name,
                label: ctx => ` ${ctx.parsed.x} Tage bis Frist (${upcoming[ctx[0].dataIndex].frist})`,
              },
            },
          },
          scales: {
            x: { ...scaleOpts, beginAtZero: true, title: { display: true, text: 'Tage bis Frist', color: textMuted } },
            y: { ...scaleOpts, ticks: { ...scaleOpts.ticks, font: { size: 11 } } },
          },
        },
      });
    },

    // --- Formatting helpers ---
    formatFrist(p) {
      if (p.rolling) return 'Rolling';
      if (!p.frist) return '—';
      const d = new Date(p.frist);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const days = Math.ceil((d - today) / (24 * 60 * 60 * 1000));
      if (days < 0) return `${p.frist} (abgelaufen)`;
      if (days <= 30) return `${p.frist} (${days}d)`;
      return p.frist;
    },

    formatBudget(p) {
      if (p.budget_max === null || p.budget_max === undefined) return '—';
      if (p.budget_max >= 1_000_000) return `${(p.budget_max / 1_000_000).toFixed(1)} Mio. €`;
      if (p.budget_max >= 1_000) return `${Math.round(p.budget_max / 1000)}k €`;
      return `${p.budget_max} €`;
    },

    formatSource(url) {
      if (!url) return '—';
      try {
        const u = new URL(url);
        return u.hostname;
      } catch {
        return url.slice(0, 30);
      }
    },
  };
}
