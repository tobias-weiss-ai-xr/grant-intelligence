'use strict';

// =============================================================================
// Foerder-Radar – JavaScript-Port der Matching-Logik + Node.js-Unit-Tests
// =============================================================================
//
// Diese Datei enthält einen 1:1-Port der Matching-Funktionen aus `mcp/match.py`
// (_fits, _theme_score, _score, _punkte_teile, _frist_text, _begruendung,
// match_profile) sowie Node.js-Unit-Tests (assert) für diese Ports.
//
// WICHTIG: Die JS-Ergebnisse müssen MIT DEN PYTHON-Ergebnissen IDENTISCH sein.
// Die Tests kodieren Erwartungswerte, die gegen die echte Python-Implementierung
// (mcp/match.py) verifiziert wurden.
//
// Ausführen:  node test_match.js        (aus dashboard/ oder per --filename)

const assert = require('assert');

// ---------------------------------------------------------------------------
// Referenz-Implementierung (Port von mcp/match.py, Stand: 2026-09-02)
// ---------------------------------------------------------------------------

// def _fits(theme_defs: list[str], field: str) -> bool
// 'alle'/'frei'/'thematisch-offen' matchen alles (Wildcards); sonst
// case-insensitive Substring-Match in beide Richtungen.
function _fits(themeDefs, field) {
  const wildcards = ['alle', 'frei', 'thematisch-offen'];
  if (field === null || field === undefined) return false;
  const f = String(field).toLowerCase().trim();
  if (!f) return false;
  const defs = themeDefs || []; // None/undefined wie leere Liste behandeln (leere Eingabe -> false)
  return defs.some((t) => {
    const tl = String(t).toLowerCase(); // Python: t.lower() (Themen NICHT gestrippt)
    return wildcards.includes(tl) || tl.includes(f) || f.includes(tl);
  });
}

// def _theme_score(prog, fields) -> (min(len(hits), 3), hits)
// Wie in Python: Score ist auf 3 gedeckelt, hits = passende Felder.
function _themeScore(prog, fields) {
  const hits = (fields || []).filter((f) => _fits((prog && prog.themen) || [], f));
  return { score: Math.min(hits.length, 3), felder: hits };
}

// def _score(prog, fields, karriere) -> {"gesamt", "thema", "karriere", "felder"}
function _score(prog, fields, karriere) {
  const hits = (fields || []).filter((f) => _fits((prog && prog.themen) || [], f));
  const thema = Math.min(hits.length, 3);
  const karrierePunkte = karriere && (prog.karriere || []).includes(karriere) ? 1 : 0;
  return { gesamt: thema + karrierePunkte, thema, karriere: karrierePunkte, felder: hits };
}

// def _punkte_teile(parts) -> List[{"name","punkte","max","detail"}]
function _punkteTeile(parts) {
  const detail = parts.felder.length ? parts.felder.join(', ') : null;
  return [
    { name: 'Thema', punkte: parts.thema, max: 3, detail },
    {
      name: 'Karriere',
      punkte: parts.karriere,
      max: 1,
      detail: parts.karriere ? 'Karrierestufe im Programm gelistet' : null,
    },
  ];
}

// def parse_frist(frist) -> date | None  (nur YYYY-MM-DD wie im Katalog)
function _parseFrist(s) {
  if (!s) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
  if (!m) return null;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return Number.isNaN(d.getTime()) ? null : d;
}

// def _frist_text(frist, rolling) -> str
function _fristText(frist, rolling) {
  if (rolling) return 'Rolling – jederzeit einreichbar, keine feste Frist';
  if (!frist) return 'Frist noch offen – vor Nutzung gegen Portal prüfen';
  const d = _parseFrist(frist);
  if (!d) return `Frist ${frist} (Format unklar, prüfen)`;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  target.setHours(0, 0, 0, 0);
  const delta = Math.round((target - today) / 86_400_000);
  const formatted = `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()}`;
  if (delta < 0) return `Frist ${formatted} – bereits abgelaufen (${-delta} Tage)`;
  return `Frist ${formatted} – noch ${delta} Tage`;
}

// def budget_beschreibung(budget_max) -> str
function _budgetBeschreibung(budgetMax) {
  if (!budgetMax) return '';
  if (budgetMax >= 1_000_000) return `bis ca. ${(budgetMax / 1_000_000).toFixed(1)} Mio. Euro`;
  return `bis ca. ${Math.round(budgetMax / 1_000)} Tausend Euro`;
}

// def _begruendung(prog, parts) -> str
function _begruendung(prog, parts) {
  const bits = [];
  if (parts.felder.length) bits.push('Themen-Ueberlappung: ' + parts.felder.join(', '));

  // Python prüft hier CASE-SENSITIV (bewusst anders als _fits!):
  //   prog.get("themen") in (["frei"], ["alle"]) or "frei" in prog.get("themen")
  const themen = prog.themen || [];
  const nurWildcard = themen.length === 1 && (themen[0] === 'frei' || themen[0] === 'alle');
  if (nurWildcard || themen.includes('frei')) {
    bits.push('offen fuer alle Fachrichtungen');
  }

  if (parts.karriere) {
    bits.push('Karrierestufe passt zum Programm');
  } else if (!(prog.karriere || []).length) {
    bits.push('Karrierestufe nicht gelistet – Eignung im Einzelfall prüfen');
  }

  bits.push(_fristText(prog.frist, prog.rolling));
  const budget = prog.budget_max;
  if (budget) bits.push(prog.budget_text || _budgetBeschreibung(budget));
  if (prog.status === 'zu-pruefen') bits.push('Achtung: Details/Frist vor Antrag gegen Portal prüfen');
  return bits.join('; ');
}

// def match_profile(programme, fields, karriere, rolle, top) -> list[MatchResult]
// Sortiert nach Score (absteigend), dann Frist (aufsteigend, None zuletzt).
function matchProfile(programmes, fields, karriere, options) {
  const rolle = options && options.rolle;
  const top = options && options.top !== undefined && options.top !== null ? options.top : 3;

  // Leere / nur Whitespace-Felder -> keine Treffer (wie Python)
  if (!fields || !fields.some((f) => String(f).trim())) return [];
  if (top <= 0) return [];

  const scored = [];
  for (const p of programmes) {
    // Harte Karriere-Filter: Programm ohne Eintrag wird NICHT gefiltert
    const progKarriere = p.karriere || [];
    if (karriere && progKarriere.length && !progKarriere.includes(karriere)) continue;

    const parts = _score(p, fields, karriere);
    if (parts.gesamt <= 0 || parts.thema <= 0) continue;

    if (rolle && !(p.rolle || []).includes(rolle)) continue;

    scored.push({
      id: p.id || '',
      name: p.name || '',
      kategorie: p.kategorie || '',
      score: parts.gesamt,
      frist: p.frist !== undefined ? p.frist : null,
      rolling: !!p.rolling,
      status: p.status || '',
      quelle: p.quelle || '',
      stand_datum: p.standDatum || '',
      begruendung: _begruendung(p, parts),
      punkte: _punkteTeile(parts),
    });
  }

  scored.sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score;
    const fa = a.frist || '9999-99-99';
    const fb = b.frist || '9999-99-99';
    return fa < fb ? -1 : fa > fb ? 1 : 0;
  });
  return scored.slice(0, top);
}

module.exports = { _fits, _themeScore, _score, _punkteTeile, _fristText, _begruendung, matchProfile };

// =============================================================================
// Tests
// =============================================================================

const path = require('path');
// Pfad-unabhängig laden: funktioniert egal, ob `node test_match.js` aus
// dashboard/ oder aus einem anderen Verzeichnis ausgeführt wird.
const catalog = require(path.join(__dirname, 'data', 'catalog.json'));
const PROGS = catalog.programme || [];

let passed = 0;
let failed = 0;
let failures = [];

function check(label, fn) {
  try {
    fn();
    passed += 1;
  } catch (e) {
    failed += 1;
    failures.push(`${label}: ${e.message}`);
  }
}

function section(title) {
  console.log(`\n== ${title} ==`);
}

// ---------------------------------------------------------------------------
// 2.1  _fits(): JavaScript-Unit-Tests  (Parität zu Python mcp/match.py)
// ---------------------------------------------------------------------------
section('2.1  _fits() – JavaScript-Port');

// 2.1.1 Exakter Match
check('exact match', () => {
  assert.strictEqual(_fits(['Mathematik'], 'Mathematik'), true);
  assert.strictEqual(_fits(['Biologie'], 'Biologie'), true);
});

// 2.1.2 Substring (bidirektional)
check('theme is substring of field', () => {
  assert.strictEqual(_fits(['Bio'], 'Biologie'), true);
  assert.strictEqual(_fits(['maschinelles'], 'MASCHINELLES LERNEN'), true);
});
check('field is substring of theme', () => {
  assert.strictEqual(_fits(['Biologie'], 'Bio'), true);
  assert.strictEqual(_fits(['Maschinelles Lernen'], 'Maschinelles'), true);
});

// 2.1.3 Case-Insensitivity
check('case insensitive (theme lower, field upper)', () => {
  assert.strictEqual(_fits(['mathematik'], 'MATHEMATIK'), true);
});
check('case insensitive (theme upper, field lower)', () => {
  assert.strictEqual(_fits(['MATHEMATIK'], 'mathematik'), true);
  assert.strictEqual(_fits(['Bio'], 'BIOLOGIE'), true);
});
check('case insensitive (Umlaute/Unicode)', () => {
  assert.strictEqual(_fits(['ÖKOLOGIE'], 'ökologie'), true);
  assert.strictEqual(_fits(['ökologie'], 'Ökologie'), true);
});

// 2.1.4 Wildcards: frei / alle / thematisch-offen
check('wildcard matches any field (frei)', () => {
  assert.strictEqual(_fits(['frei'], 'Astrophysik'), true);
  assert.strictEqual(_fits(['frei'], 'Sehr langes Forschungsfeld XYZ'), true);
});
check('wildcard matches any field (alle)', () => {
  assert.strictEqual(_fits(['alle'], 'Astrophysik'), true);
});
check('wildcard matches any field (thematisch-offen)', () => {
  assert.strictEqual(_fits(['thematisch-offen'], 'Chemie'), true);
});
check('wildcards are case insensitive', () => {
  assert.strictEqual(_fits(['FREI'], 'Astrophysik'), true);
  assert.strictEqual(_fits(['Alle'], 'Astrophysik'), true);
  assert.strictEqual(_fits(['Thematisch-Offen'], 'Astrophysik'), true);
});
check('wildcard works among other themes', () => {
  assert.strictEqual(_fits(['Physik', 'frei'], 'Chemie'), true);
  assert.strictEqual(_fits(['frei', 'Chemie'], 'Biologie'), true);
});
check('wildcard-only programme matches unrelated field', () => {
  assert.strictEqual(_fits(['frei'], ''), false); // leeres Feld trotz Wildcard -> false
});

// 2.1.5 Leere / Whitespace-Eingaben -> false
check('empty themes returns false', () => {
  assert.strictEqual(_fits([], 'Biologie'), false);
});
check('empty field returns false', () => {
  assert.strictEqual(_fits(['Biologie'], ''), false);
});
check('whitespace-only field returns false', () => {
  assert.strictEqual(_fits(['Biologie'], '   '), false);
  assert.strictEqual(_fits(['Biologie'], '\t\n '), false);
});
check('empty field + empty themes returns false', () => {
  assert.strictEqual(_fits([], ''), false);
});
check('null/undefined field returns false', () => {
  assert.strictEqual(_fits(['Biologie'], null), false);
  assert.strictEqual(_fits(['Biologie'], undefined), false);
});
check('null/undefined themes returns false (empty input)', () => {
  // Python wirft beim ``None``-Fall einen TypeError; wir behandeln None/undefined
  // defensiv wie eine leere Liste -> false (Konsistenz mit 'empty inputs return False').
  assert.strictEqual(_fits(null, 'Biologie'), false);
  assert.strictEqual(_fits(undefined, 'Biologie'), false);
});

// 2.1.6 Kein Match
check('no match returns false', () => {
  assert.strictEqual(_fits(['Astronomie'], 'Biologie'), false);
  assert.strictEqual(_fits(['Chemie', 'Physik'], 'Biologie'), false);
});

// 2.1.7 Randfälle
check('field is trimmed before matching', () => {
  assert.strictEqual(_fits(['Biologie'], '  Biologie  '), true);
  assert.strictEqual(_fits(['Biologie'], '\tBiologie\n'), true);
});
check('theme with surrounding whitespace still matches (Python: field in theme.lower())', () => {
  assert.strictEqual(_fits([' Biologie '], 'Biologie'), true);
});
check('multiple matches via any()', () => {
  assert.strictEqual(_fits(['Chemie', 'Biologie'], 'Biologie'), true);
  // 'Ökologie' teilt keinen Substring mit 'Chemie'/'Biologie' -> false (mit Python verifiziert)
  assert.strictEqual(_fits(['Chemie', 'Biologie'], 'Ökologie'), false);
});
check('partial word does not match', () => {
  assert.strictEqual(_fits(['Bio'], 'Astro'), false);
  assert.strictEqual(_fits(['Mathematik'], 'Info'), false);
});
check('field longer than any theme is no implicit match', () => {
  assert.strictEqual(_fits(['AI'], 'Künstliche Intelligenz'), false);
});
check('real catalog: wildcard programmes match arbitrary fields', () => {
  const allOpen = PROGS.filter((p) => (p.themen || []).includes('frei'));
  assert.ok(allOpen.length > 0, 'catalog must contain frei-programmes');
  assert.ok(allOpen.every((p) => _fits(p.themen, 'Astroteilchenphysik')));
});

// ---------------------------------------------------------------------------
// _themeScore(): Deckelung bei 3  (Port-Parität, TEST-JS-2 baut darauf auf)
// ---------------------------------------------------------------------------
section('_themeScore() – Port-Parität');

check('score capped at 3 even with 4+ matches', () => {
  const prog = { themen: ['Bio', 'Biologie', 'Chemie', 'Physik', 'Mathematik'] };
  const { score, felder } = _themeScore(prog, ['Bio', 'Biologie', 'Chemie', 'Physik']);
  assert.strictEqual(score, 3);
  assert.strictEqual(felder.length, 4);
});
check('empty fields returns 0', () => {
  assert.deepStrictEqual(_themeScore({ themen: ['Bio'] }, []), { score: 0, felder: [] });
});
check('no matches returns 0', () => {
  assert.strictEqual(_themeScore({ themen: ['Astronomie'] }, ['Biologie']).score, 0);
});
check('partial matches 1-3', () => {
  assert.strictEqual(_themeScore({ themen: ['Bio'] }, ['Biologie']).score, 1);
  assert.strictEqual(_themeScore({ themen: ['Bio', 'Chemie'] }, ['Biologie', 'Chemie']).score, 2);
});

// ---------------------------------------------------------------------------
// 2.2  matchProfile(): Parität zu Python match_profile()  (Test-Fixtures)
// ---------------------------------------------------------------------------
section('2.2  matchProfile() – Fixture-Parität (Erwartungswerte aus Python)');

// Fixtures ohne frist => begruendung ist datumsunabhängig und vollständig prüfbar
const FIX = [
  { id: 'p1', name: 'Prog One', themen: ['Bio'], karriere: ['postdoc'], frist: null, rolling: false,
    kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: 100000, rolle: [] },
  { id: 'p2', name: 'Prog Two', themen: ['frei'], karriere: ['prof'], frist: null, rolling: true,
    kategorie: 'K', status: 'laufend', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: [] },
  { id: 'p3', name: 'Prog Three', themen: ['Biologie', 'Chemie', 'Physik', 'Mathematik'], karriere: ['postdoc', 'prof'],
    frist: null, rolling: false, kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01',
    budget_max: 2000000, rolle: [] },
  { id: 'p4', name: 'Prog Four', themen: ['Medizin'], karriere: [], frist: null, rolling: false,
    kategorie: 'K', status: 'zu-pruefen', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: [] },
];

check('sorted by score desc, then frist asc (fixtures)', () => {
  const res = matchProfile(FIX, ['Bio', 'Biologie', 'Chemie', 'Physik'], 'postdoc', { top: 10 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score]),
    [['p3', 4], ['p1', 3]]
  );
});

check('full punkte breakdown matches Python (p3)', () => {
  const res = matchProfile(FIX, ['Bio', 'Biologie', 'Chemie', 'Physik'], 'postdoc', { top: 10 });
  const p3 = res.find((r) => r.id === 'p3');
  assert.deepStrictEqual(p3.punkte, [
    { name: 'Thema', punkte: 3, max: 3, detail: 'Bio, Biologie, Chemie, Physik' },
    { name: 'Karriere', punkte: 1, max: 1, detail: 'Karrierestufe im Programm gelistet' },
  ]);
});

check('begruendung matches Python exactly (p3)', () => {
  const res = matchProfile(FIX, ['Bio', 'Biologie', 'Chemie', 'Physik'], 'postdoc', { top: 10 });
  const p3 = res.find((r) => r.id === 'p3');
  assert.strictEqual(
    p3.begruendung,
    'Themen-Ueberlappung: Bio, Biologie, Chemie, Physik; Karrierestufe passt zum Programm; ' +
      'Frist noch offen – vor Nutzung gegen Portal prüfen; bis ca. 2.0 Mio. Euro'
  );
});

check('begruendung matches Python exactly (p1)', () => {
  const res = matchProfile(FIX, ['Bio', 'Biologie', 'Chemie', 'Physik'], 'postdoc', { top: 10 });
  const p1 = res.find((r) => r.id === 'p1');
  assert.strictEqual(
    p1.begruendung,
    'Themen-Ueberlappung: Bio, Biologie; Karrierestufe passt zum Programm; ' +
      'Frist noch offen – vor Nutzung gegen Portal prüfen; bis ca. 100 Tausend Euro'
  );
});

check('rolling programme gets rolling frist text (p2)', () => {
  const res = matchProfile(FIX, ['Medizin'], 'prof', { top: 10 });
  const p2 = res.find((r) => r.id === 'p2');
  assert.strictEqual(p2.rolling, true);
  assert.ok(p2.begruendung.includes('Rolling – jederzeit einreichbar'));
});

check('karriere is a hard filter', () => {
  const res = matchProfile(FIX, ['Bio'], 'prof', { top: 10 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score]),
    [['p2', 2], ['p3', 2]]
  );
});

check('no karriere filter when karriere is null', () => {
  const res = matchProfile(FIX, ['Medizin'], null, { top: 10 });
  assert.deepStrictEqual(
    res.map((r) => r.id),
    ['p2', 'p4']
  );
});

check('empty fields return no matches', () => {
  assert.deepStrictEqual(matchProfile(FIX, [], 'postdoc', { top: 10 }), []);
  assert.deepStrictEqual(matchProfile(FIX, ['   '], 'postdoc', { top: 10 }), []);
});

check('top <= 0 returns no matches', () => {
  assert.deepStrictEqual(matchProfile(FIX, ['Bio'], 'postdoc', { top: 0 }), []);
});

check('top limits result count', () => {
  const res = matchProfile(FIX, ['Bio', 'Biologie', 'Chemie', 'Physik'], 'postdoc', { top: 1 });
  assert.strictEqual(res.length, 1);
  assert.strictEqual(res[0].id, 'p3');
});

check('programme with no karriere list is not filtered out', () => {
  const res = matchProfile(FIX, ['Medizin'], 'postdoc', { top: 10 });
  assert.ok(res.some((r) => r.id === 'p4'));
});

// ---------------------------------------------------------------------------
// 2.2  matchProfile(): Parität mit Python auf dem echten Katalog
//      (Erwartungswerte mit mcp/match.py berechnet; nur id/score/frist werden
//       verglichen, die Begründung enthält datumsabhängige Frist-Texte)
// ---------------------------------------------------------------------------
section('2.2  matchProfile() – Parität auf echtem Katalog (dashboard/data/catalog.json)');

check('real catalog scenario A: ["Biologie"] postdoc, top 5', () => {
  const py = [
    ['erc-plus-2026', 2, '2026-09-02'],
    ['msca-pf', 2, '2026-09-09'],
    ['cost-netzwerk', 2, '2026-09-10'],
    ['dfg-emmy-noether', 2, '2026-10-01'],
    ['erc-stg-2027', 2, '2026-10-14'],
  ];
  const res = matchProfile(PROGS, ['Biologie'], 'postdoc', { top: 5 });
  const js = res.map((r) => [r.id, r.score, r.frist]);
  assert.deepStrictEqual(js, py);
});

check('real catalog scenario B: ["Maschinelles Lernen", "KI"] prof, top 5', () => {
  const py = [
    ['erc-plus-2026', 3, '2026-09-02'],
    ['cost-netzwerk', 3, '2026-09-10'],
    ['dfg-heisenberg', 3, '2026-10-01'],
    ['volkswagen-stiftung', 3, '2026-10-15'],
    ['eu-eic-pathfinder', 3, '2026-10-28'],
  ];
  const res = matchProfile(PROGS, ['Maschinelles Lernen', 'KI'], 'prof', { top: 5 });
  const js = res.map((r) => [r.id, r.score, r.frist]);
  assert.deepStrictEqual(js, py);
});

check('real catalog scenario C: ["Chemie"] no karriere, top 3', () => {
  const py = [
    ['erc-plus-2026', 1, '2026-09-02'],
    ['msca-pf', 1, '2026-09-09'],
    ['cost-netzwerk', 1, '2026-09-10'],
  ];
  const res = matchProfile(PROGS, ['Chemie'], null, { top: 3 });
  const js = res.map((r) => [r.id, r.score, r.frist]);
  assert.deepStrictEqual(js, py);
});

check('real catalog: empty fields return []', () => {
  assert.deepStrictEqual(matchProfile(PROGS, [], 'postdoc', { top: 3 }), []);
});

// ---------------------------------------------------------------------------
// Zusammenfassung
// ---------------------------------------------------------------------------
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) {
  console.log('\nFailures:');
  failures.forEach((f) => console.log('  - ' + f));
  process.exit(1);
}
console.log('ALL TESTS PASSED');
