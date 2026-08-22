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
    renderCharts() {
      // Category doughnut (colorblind-friendly palette)
      const cats = {};
      this.catalog.forEach(p => { cats[p.kategorie] = (cats[p.kategorie] || 0) + 1; });
      const catColors = [
        getComputedStyle(document.documentElement).getPropertyValue('--c1').trim() || '#007a3d',
        getComputedStyle(document.documentElement).getPropertyValue('--c2').trim() || '#1a5fb4',
        getComputedStyle(document.documentElement).getPropertyValue('--c3').trim() || '#c0392b',
        getComputedStyle(document.documentElement).getPropertyValue('--c4').trim() || '#8a6500',
        getComputedStyle(document.documentElement).getPropertyValue('--c5').trim() || '#6f42c1',
        getComputedStyle(document.documentElement).getPropertyValue('--c6').trim() || '#e83e8c',
        getComputedStyle(document.documentElement).getPropertyValue('--c7').trim() || '#20c997',
        getComputedStyle(document.documentElement).getPropertyValue('--c8').trim() || '#fd7e14',
        getComputedStyle(document.documentElement).getPropertyValue('--c9').trim() || '#495057',
      ];

      if (this._catChart) this._catChart.destroy();
      this._catChart = new Chart(document.getElementById('catChart'), {
        type: 'doughnut',
        data: {
          labels: Object.keys(cats),
          datasets: [{ data: Object.values(cats), backgroundColor: catColors, borderColor: getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#fff' }],
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: 'right', labels: { color: getComputedStyle(document.documentElement).getPropertyValue('--text').trim() || '#222' } },
          },
        },
      });

      // Status bar
      const stats = {};
      this.catalog.forEach(p => { stats[p.status] = (stats[p.status] || 0) + 1; });
      const statusColors = {
        verifiziert: getComputedStyle(document.documentElement).getPropertyValue('--green-bg').trim() || '#007a3d',
        laufend: getComputedStyle(document.documentElement).getPropertyValue('--blue-bg').trim() || '#1a5fb4',
        'zu-pruefen': getComputedStyle(document.documentElement).getPropertyValue('--amber-bg').trim() || '#8a6500',
      };
      if (this._statusChart) this._statusChart.destroy();
      this._statusChart = new Chart(document.getElementById('statusChart'), {
        type: 'bar',
        data: {
          labels: Object.keys(stats),
          datasets: [{ label: 'Programme', data: Object.values(stats), backgroundColor: Object.keys(stats).map(k => statusColors[k] || '#999') }],
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#5f5f5f' } },
            x: { ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#5f5f5f' } },
          },
        },
      });

      // Deadline timeline (next 90 days, top 15)
      const upcoming = this.upcomingDeadlines.slice(0, 15);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (this._deadlineChart) this._deadlineChart.destroy();
      this._deadlineChart = new Chart(document.getElementById('deadlineChart'), {
        type: 'bar',
        data: {
          labels: upcoming.map(p => p.name.length > 40 ? p.name.slice(0, 37) + '…' : p.name),
          datasets: [{
            label: 'Tage bis Frist',
            data: upcoming.map(p => Math.ceil((new Date(p.frist) - today) / (24 * 60 * 60 * 1000))),
            backgroundColor: upcoming.map(p => {
              const days = Math.ceil((new Date(p.frist) - today) / (24 * 60 * 60 * 1000));
              if (days <= 14) return getComputedStyle(document.documentElement).getPropertyValue('--red-bg').trim() || '#c0392b';
              if (days <= 30) return getComputedStyle(document.documentElement).getPropertyValue('--orange').trim() || '#b85d00';
              return getComputedStyle(document.documentElement).getPropertyValue('--green-bg').trim() || '#007a3d';
            }),
          }],
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            x: { beginAtZero: true, title: { display: true, text: 'Tage bis Frist', color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#5f5f5f' }, ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#5f5f5f' } },
            y: { ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim() || '#5f5f5f' } },
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
