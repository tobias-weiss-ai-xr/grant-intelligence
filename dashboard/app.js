// Förder-Radar – Dashboard (Alpine.js + Chart.js)
// Pure client-side, no build step, no server.
// Data: fetch('data/catalog.json'), fetch('data/sources.json'), fetch('data/profiles.json')

function dashboard() {
  return {
    // --- State ---
    catalog: [],
    sources: {},
    profiles: [],
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

    // Profile matcher
    profilId: '',
    matchedProgrammes: [],

    // Charts
    _catChart: null,
    _statusChart: null,
    _deadlineChart: null,

    // --- Init ---
    async init() {
      try {
        const [catRes, srcRes, profRes] = await Promise.all([
          fetch('data/catalog.json').then(r => { if (!r.ok) throw new Error('catalog.json: ' + r.status); return r.json(); }),
          fetch('data/sources.json').then(r => { if (!r.ok) throw new Error('sources.json: ' + r.status); return r.json(); }),
          fetch('data/profiles.json').then(r => { if (!r.ok) throw new Error('profiles.json: ' + r.status); return r.json(); }),
        ]);
        this.catalog = catRes.programme || [];
        this.stand = catRes.stand || '';
        this.sources = srcRes || {};
        this.profiles = profRes.profile || profRes.profiles || [];
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
        this.srcSortDir = 1;
      }
    },

    // --- Profile Matcher ---
    selectProfile(id) {
      this.profilId = id;
      if (!id) {
        this.matchedProgrammes = [];
        return;
      }
      const profile = this.profiles.find(p => p.id === id);
      if (!profile) {
        this.matchedProgrammes = [];
        return;
      }
      const scored = this.catalog.map(p => {
        const score = this.scoreProgramme(profile, p);
        return {
          id: p.id,
          name: p.name,
          kategorie: p.kategorie,
          frist: p.frist || '',
          rolling: p.rolling || false,
          score: score.score,
          reason: score.reason,
        };
      }).filter(m => m.score > 0).sort((a, b) => b.score - a.score);
      this.matchedProgrammes = scored;
    },

    scoreProgramme(profile, programme) {
      let score = 0;
      const reasons = [];

      // Themen overlap (max 3 points)
      const profileThemen = profile.themen || [];
      const progThemen = programme.themen || [];
      const themenOverlap = progThemen.filter(t =>
        profileThemen.some(pt => pt.toLowerCase().includes(t.toLowerCase()) || t.toLowerCase().includes(pt.toLowerCase()))
      );
      if (themenOverlap.length > 0) {
        score += Math.min(themenOverlap.length, 3);
        reasons.push(`Themen: ${themenOverlap.slice(0, 3).join(', ')}`);
      }

      // Karriere match (1 point)
      if ((programme.karriere || []).includes(profile.karriere)) {
        score += 1;
        reasons.push(`Karriere: ${profile.karriere}`);
      }

      // Rolle match (0.5 points)
      const progRolle = programme.rolle || [];
      if (progRolle.length === 0 || progRolle.includes('lead')) {
        score += 0.5;
        reasons.push('Rolle: offen/lead');
      }

      // Rolling bonus (0.5 points)
      if (programme.rolling) {
        score += 0.5;
        reasons.push('Rolling (keine Frist)');
      }

      // Status bonus
      if (programme.status === 'verifiziert') {
        score += 0.5;
        reasons.push('Verifiziert');
      } else if (programme.status === 'laufend') {
        score += 0.25;
        reasons.push('Laufend');
      }

      return {
        score: Math.min(Math.round(score * 10) / 10, 5),
        reason: reasons.join('; '),
      };
    },

    // --- Charts ---
    renderCharts() {
      // Category doughnut
      const cats = {};
      this.catalog.forEach(p => { cats[p.kategorie] = (cats[p.kategorie] || 0) + 1; });
      const catColors = ['#0b5', '#36a2eb', '#ff6384', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40', '#e7e7e7', '#c9cbcf'];

      if (this._catChart) this._catChart.destroy();
      this._catChart = new Chart(document.getElementById('catChart'), {
        type: 'doughnut',
        data: {
          labels: Object.keys(cats),
          datasets: [{ data: Object.values(cats), backgroundColor: catColors }],
        },
        options: { responsive: true, plugins: { legend: { position: 'right' } } },
      });

      // Status bar
      const stats = {};
      this.catalog.forEach(p => { stats[p.status] = (stats[p.status] || 0) + 1; });
      if (this._statusChart) this._statusChart.destroy();
      this._statusChart = new Chart(document.getElementById('statusChart'), {
        type: 'bar',
        data: {
          labels: Object.keys(stats),
          datasets: [{ label: 'Programme', data: Object.values(stats), backgroundColor: ['#0b5', '#36a2eb', '#ffce56'] }],
        },
        options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } },
      });

      // Deadline timeline (next 90 days)
      const upcoming = this.upcomingDeadlines.slice(0, 15);
      const today = new Date();
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
              return days <= 14 ? '#d33' : days <= 30 ? '#ff9f40' : '#0b5';
            }),
          }],
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          plugins: { legend: { display: false } },
          scales: { x: { beginAtZero: true, title: { display: true, text: 'Tage bis Frist' } } },
        },
      });
    },

    // --- Formatting helpers ---
    formatFrist(p) {
      if (p.rolling) return 'Rolling';
      if (!p.frist) return '—';
      const d = new Date(p.frist);
      const today = new Date();
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
