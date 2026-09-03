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
  const y = Number(m[1]);
  const mo = Number(m[2]);
  const d = Number(m[3]);
  // Parität zu Python date.fromisoformat: überlaufende Komponenten
  // (z.B. 2026-13-99, 2026-02-30, 9999-99-99) ablehnen statt sie von der
  // Date-Konstruktion normalisieren zu lassen.
  const probe = new Date(Date.UTC(y, mo - 1, d));
  if (
    probe.getUTCFullYear() !== y ||
    probe.getUTCMonth() !== mo - 1 ||
    probe.getUTCDate() !== d
  ) {
    return null;
  }
  return new Date(y, mo - 1, d);
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
// Python: f"{budget_max / 1_000:.0f}" (Tausend) bzw. f"{...:.1f}" (Mio) nutzt
// Round-Half-To-Even (Banker's Rounding). JS Math.round rundet 0.5 hingegegen
// IMMER auf -> bei genau halbzahligen Ergebnissen Abweichung zu Python.
// _pyRoundHalfEven() repliziert exakt das Python-Format-Rounding (nur für die
// hier vorkommenden positiven Vielfachen von 0.001 nötig, z. B. 500 -> '0').
function _pyRoundHalfEven(x) {
  const lower = Math.floor(x);
  const frac = x - lower;
  if (frac < 0.5) return lower;
  if (frac > 0.5) return lower + 1;
  return lower % 2 === 0 ? lower : lower + 1; // exakt .5 -> zur geraden Zahl
}
function _budgetBeschreibung(budgetMax) {
  if (!budgetMax) return '';
  if (budgetMax >= 1_000_000) return `bis ca. ${(budgetMax / 1_000_000).toFixed(1)} Mio. Euro`;
  return `bis ca. ${_pyRoundHalfEven(budgetMax / 1_000)} Tausend Euro`;
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

// 2.1.8 Weitere Randfälle – alle Erwartungswerte gegen mcp/match.py verifiziert
check('theme is substring of longer compound field', () => {
  // Python: 'chemie' in 'chemieingenieurwesen' -> True
  assert.strictEqual(_fits(['Chemie'], 'Chemieingenieurwesen'), true);
});
check('field with trailing whitespace is trimmed before matching', () => {
  // Python: field.lower().strip()
  assert.strictEqual(_fits(['Bio'], 'Bio '), true);
});
check('theme with surrounding whitespace still matches', () => {
  // Python: Themen werden NICHT gestrippt -> '  biologie  ' enthält 'biologie'
  assert.strictEqual(_fits(['  Biologie  '], 'Biologie'), true);
});
check('empty-string theme inside non-empty field matches (Python semantics)', () => {
  // Python: '' in 'x' -> True;  JS: 'x'.includes('') -> True  =>  Parität
  assert.strictEqual(_fits([''], 'x'), true);
});
check('empty-string theme + empty field returns false (beide Seiten)', () => {
  assert.strictEqual(_fits([''], ''), false);
  assert.strictEqual(_fits([''], '   '), false);
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
// 2.3  _fristText(): deterministische Zweige (keine Tagesdatum-Abhängigkeit)
//      Erwartungswerte 1:1 aus mcp/match.py übernommen
// ---------------------------------------------------------------------------
section('2.3  _fristText() – deterministische Zweige');

check('rolling takes precedence over any frist', () => {
  assert.strictEqual(
    _fristText('2026-09-02', true),
    'Rolling – jederzeit einreichbar, keine feste Frist'
  );
  assert.strictEqual(
    _fristText(null, true),
    'Rolling – jederzeit einreichbar, keine feste Frist'
  );
});

check('no frist and not rolling', () => {
  assert.strictEqual(
    _fristText(null, false),
    'Frist noch offen – vor Nutzung gegen Portal prüfen'
  );
  assert.strictEqual(
    _fristText('', false),
    'Frist noch offen – vor Nutzung gegen Portal prüfen'
  );
});

check('invalid date (month/day overflow) -> Format unklar (Python: fromisoformat wirft)', () => {
  assert.strictEqual(_fristText('2026-13-99', false), 'Frist 2026-13-99 (Format unklar, prüfen)');
  assert.strictEqual(_fristText('2026-02-30', false), 'Frist 2026-02-30 (Format unklar, prüfen)');
  assert.strictEqual(_fristText('9999-99-99', false), 'Frist 9999-99-99 (Format unklar, prüfen)');
});

check('unparseable frist string -> Format unklar', () => {
  assert.strictEqual(_fristText('nix', false), 'Frist nix (Format unklar, prüfen)');
  assert.strictEqual(_fristText('2026-1-1', false), 'Frist 2026-1-1 (Format unklar, prüfen)');
  assert.strictEqual(_fristText('2026/09/02', false), 'Frist 2026/09/02 (Format unklar, prüfen)');
});

check('valid frist parses (delta is computed, format used)', () => {
  // Nur Struktur prüfen: Tag/Monat/Jahr korrekt formatiert; der Tages-Delta
  // ist tagesdatum-abhängig und wird hier nicht hart kodiert.
  const t = _fristText('2999-01-01', false);
  assert.ok(t.startsWith('Frist 01.01.2999 –'), t);
});

// ---------------------------------------------------------------------------
// 2.4  _punkteTeile(): Struktur (Parität zu Python _punkte_teile)
// ---------------------------------------------------------------------------
section('2.4  _punkteTeile() – Struktur');

check('breakdown with matched fields, no karriere', () => {
  assert.deepStrictEqual(
    _punkteTeile({ gesamt: 2, thema: 2, karriere: 0, felder: ['Bio', 'Physik'] }),
    [
      { name: 'Thema', punkte: 2, max: 3, detail: 'Bio, Physik' },
      { name: 'Karriere', punkte: 0, max: 1, detail: null },
    ]
  );
});

check('breakdown with karriere hit (max theme score)', () => {
  assert.deepStrictEqual(
    _punkteTeile({ gesamt: 4, thema: 3, karriere: 1, felder: ['Bio', 'Chemie', 'Physik'] }),
    [
      { name: 'Thema', punkte: 3, max: 3, detail: 'Bio, Chemie, Physik' },
      { name: 'Karriere', punkte: 1, max: 1, detail: 'Karrierestufe im Programm gelistet' },
    ]
  );
});

check('breakdown with no hits', () => {
  assert.deepStrictEqual(
    _punkteTeile({ gesamt: 0, thema: 0, karriere: 0, felder: [] }),
    [
      { name: 'Thema', punkte: 0, max: 3, detail: null },
      { name: 'Karriere', punkte: 0, max: 1, detail: null },
    ]
  );
});

// ---------------------------------------------------------------------------
// 2.5  _begruendung(): deterministische Volltexte gegen mcp/match.py
//      (fixtures ohne frist -> keine Tagesdatum-Abhängigkeit)
// ---------------------------------------------------------------------------
section('2.5  _begruendung() – deterministische Volltexte');

check('_begruendung: offenes Programm (frei) exakt wie Python', () => {
  const prog = { themen: ['frei'], karriere: ['postdoc'], frist: null, rolling: false, budget_max: 500000, status: 'verifiziert' };
  const parts = _score(prog, ['Astrophysik'], 'postdoc');
  assert.strictEqual(
    _begruendung(prog, parts),
    'Themen-Ueberlappung: Astrophysik; offen fuer alle Fachrichtungen; Karrierestufe passt zum Programm; ' +
      'Frist noch offen – vor Nutzung gegen Portal prüfen; bis ca. 500 Tausend Euro'
  );
});

check('_begruendung: zu-pruefen, keine Karriere-Liste, kein Budget exakt wie Python', () => {
  const prog = { themen: ['Bio'], karriere: [], frist: null, rolling: false, status: 'zu-pruefen' };
  const parts = _score(prog, ['Biologie'], 'postdoc');
  assert.deepStrictEqual(parts, { gesamt: 1, thema: 1, karriere: 0, felder: ['Biologie'] });
  assert.strictEqual(
    _begruendung(prog, parts),
    'Themen-Ueberlappung: Biologie; Karrierestufe nicht gelistet – Eignung im Einzelfall prüfen; ' +
      'Frist noch offen – vor Nutzung gegen Portal prüfen; Achtung: Details/Frist vor Antrag gegen Portal prüfen'
  );
});

// ---------------------------------------------------------------------------
// 2.2  matchProfile(): weitere Katalog-Szenarien
//      (Erwartungswerte mit mcp/match.py berechnet; nur id/score/frist)
// ---------------------------------------------------------------------------
section('2.2  matchProfile() – weitere Katalog-Szenarien (Erwartungswerte aus mcp/match.py)');

function expectScenario(label, fields, karriere, rolle, top, expected) {
  check(label, () => {
    const opts = rolle ? { top, rolle } : { top };
    const res = matchProfile(PROGS, fields, karriere, opts);
    assert.deepStrictEqual(
      res.map((r) => [r.id, r.score, r.frist ?? null]),
      expected
    );
  });
}

expectScenario('Physik prof top10', ['Physik'], 'prof', null, 10, [
  ['erc-plus-2026', 2, '2026-09-02'], ['cost-netzwerk', 2, '2026-09-10'],
  ['dfg-heisenberg', 2, '2026-10-01'], ['volkswagen-stiftung', 2, '2026-10-15'],
  ['eu-eic-pathfinder', 2, '2026-10-28'], ['anr-attractiv-science', 2, '2026-12-01'],
  ['fritz-thyssen', 2, '2027-02-01'], ['erc-syg-2027', 2, '2027-05-11'],
  ['erc-adg-2027', 2, null], ['dfg-sachbeihilfe', 2, null],
]);

expectScenario('Informatik postdoc top5', ['Informatik'], 'postdoc', null, 5, [
  ['erc-plus-2026', 2, '2026-09-02'], ['msca-pf', 2, '2026-09-09'],
  ['cost-netzwerk', 2, '2026-09-10'], ['dfg-emmy-noether', 2, '2026-10-01'],
  ['erc-stg-2027', 2, '2026-10-14'],
]);

expectScenario('Medizin ohne Karriere top4', ['Medizin'], null, null, 4, [
  ['erc-plus-2026', 1, '2026-09-02'], ['msca-pf', 1, '2026-09-09'],
  ['cost-netzwerk', 1, '2026-09-10'], ['dfg-emmy-noether', 1, '2026-10-01'],
]);

expectScenario('KI prof top6', ['KI'], 'prof', null, 6, [
  ['erc-plus-2026', 2, '2026-09-02'], ['cost-netzwerk', 2, '2026-09-10'],
  ['dfg-heisenberg', 2, '2026-10-01'], ['volkswagen-stiftung', 2, '2026-10-15'],
  ['eu-eic-pathfinder', 2, '2026-10-28'], ['eu-horizon-digital', 2, '2026-11-08'],
]);

expectScenario('mehrere Felder prof top10 (Thema-Score gedeckelt auf 3)', ['Biologie', 'Chemie', 'Physik'], 'prof', null, 10, [
  ['erc-plus-2026', 4, '2026-09-02'], ['cost-netzwerk', 4, '2026-09-10'],
  ['dfg-heisenberg', 4, '2026-10-01'], ['volkswagen-stiftung', 4, '2026-10-15'],
  ['eu-eic-pathfinder', 4, '2026-10-28'], ['anr-attractiv-science', 4, '2026-12-01'],
  ['fritz-thyssen', 4, '2027-02-01'], ['erc-syg-2027', 4, '2027-05-11'],
  ['erc-adg-2027', 4, null], ['dfg-sachbeihilfe', 4, null],
]);

expectScenario('wenige Felder ohne Karriere top2', ['Maschinelles Lernen', 'Robotik'], null, null, 2, [
  ['erc-plus-2026', 2, '2026-09-02'], ['msca-pf', 2, '2026-09-09'],
]);

expectScenario('rolle=lead top5', ['Biologie'], 'postdoc', 'lead', 5, [
  ['erc-plus-2026', 2, '2026-09-02'], ['msca-pf', 2, '2026-09-09'],
  ['cost-netzwerk', 2, '2026-09-10'], ['dfg-emmy-noether', 2, '2026-10-01'],
  ['erc-stg-2027', 2, '2026-10-14'],
]);

expectScenario('rolle=partner schränkt ein (top3)', ['Physik'], 'prof', 'partner', 3, [
  ['cost-netzwerk', 2, '2026-09-10'], ['eu-eic-pathfinder', 2, '2026-10-28'],
  ['erc-syg-2027', 2, '2027-05-11'],
]);

expectScenario('unbekannte Karrierestufe -> leere Trefferliste', ['Physik'], 'professorin', null, 5, []);

expectScenario('top1 liefert nur den besten Treffer', ['Physik'], 'postdoc', null, 1, [
  ['erc-plus-2026', 2, '2026-09-02'],
]);

expectScenario('breites Profil ohne Karriere top8 (stable sort bei gleichem Frist-Tag)', ['KI', 'Informatik', 'Robotik'], null, null, 8, [
  ['erc-plus-2026', 3, '2026-09-02'], ['msca-pf', 3, '2026-09-09'],
  ['cost-netzwerk', 3, '2026-09-10'], ['dfg-emmy-noether', 3, '2026-10-01'],
  ['dfg-heisenberg', 3, '2026-10-01'], ['erc-stg-2027', 3, '2026-10-14'],
  ['volkswagen-stiftung', 3, '2026-10-15'], ['eu-eic-pathfinder', 3, '2026-10-28'],
]);

expectScenario('viele Felder prof top20 (None-Fristen am Ende, alle Score 4)', ['AI', 'Informatik', 'Mathematik'], 'prof', null, 20, [
  ['erc-plus-2026', 4, '2026-09-02'], ['cost-netzwerk', 4, '2026-09-10'],
  ['dfg-heisenberg', 4, '2026-10-01'], ['volkswagen-stiftung', 4, '2026-10-15'],
  ['eu-eic-pathfinder', 4, '2026-10-28'], ['anr-attractiv-science', 4, '2026-12-01'],
  ['fritz-thyssen', 4, '2027-02-01'], ['erc-syg-2027', 4, '2027-05-11'],
  ['erc-adg-2027', 4, null], ['dfg-sachbeihilfe', 4, null],
  ['dfg-sfb', 4, null], ['loewe-hessen', 4, null],
  ['humboldt-prof', 4, null], ['dfg-reinhart-koselleck', 4, null],
  ['dfg-forschungsgruppen', 4, null], ['dfg-schwerpunktprogramme', 4, null],
  ['dfg-kolleg-forschungsgruppen', 4, null], ['dfg-wissenschaftliche-netzwerke', 4, null],
  ['dfg-forschungsimpulse', 4, null], ['humboldt-forschungsstipendium', 4, null],
]);

// ---------------------------------------------------------------------------
// 2.2  matchProfile(): weitere Katalog-Szenarien (TEST-JS-2)
//      Alle Erwartungswerte wurden LIVE mit mcp/match.py (match_profile)
//      berechnet und verifiziert (Stand: 2026-09-03). Es werden nur
//      id/score/frist verglichen; die Begründung enthält datumsabhängige
//      Frist-Texte und wird für Katalog-Fälle nicht hart kodiert.
// ---------------------------------------------------------------------------
section('2.2  matchProfile() – weitere Katalog-Szenarien (TEST-JS-2, Erwartungswerte aus mcp/match.py)');

check('junior Biologie top5', () => {
  const res = matchProfile(PROGS, ['Biologie'], 'junior', { top: 5 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 2, '2026-09-02'], ['cost-netzwerk', 2, '2026-09-10'],
      ['erc-stg-2027', 2, '2026-10-14'], ['volkswagen-stiftung', 2, '2026-10-15'],
      ['eu-eic-pathfinder', 2, '2026-10-28'],
    ]
  );
});

check('postdoc Nachhaltigkeit top5', () => {
  const res = matchProfile(PROGS, ['Nachhaltigkeit'], 'postdoc', { top: 5 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 2, '2026-09-02'], ['msca-pf', 2, '2026-09-09'],
      ['cost-netzwerk', 2, '2026-09-10'], ['dfg-emmy-noether', 2, '2026-10-01'],
      ['erc-stg-2027', 2, '2026-10-14'],
    ]
  );
});

check('prof Physik-Cluster top10 (Thema-Score gedeckelt)', () => {
  const res = matchProfile(PROGS, ['Physik', 'Quantenphysik', 'Astrophysik'], 'prof', { top: 10 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 4, '2026-09-02'], ['cost-netzwerk', 4, '2026-09-10'],
      ['dfg-heisenberg', 4, '2026-10-01'], ['volkswagen-stiftung', 4, '2026-10-15'],
      ['eu-eic-pathfinder', 4, '2026-10-28'], ['anr-attractiv-science', 4, '2026-12-01'],
      ['fritz-thyssen', 4, '2027-02-01'], ['erc-syg-2027', 4, '2027-05-11'],
      ['erc-adg-2027', 4, null], ['dfg-sachbeihilfe', 4, null],
    ]
  );
});

check('null Kunst+Archäologie top8 (Geisteswissenschaften)', () => {
  const res = matchProfile(PROGS, ['Kunst', 'Archäologie'], null, { top: 8 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['gerda-henkel', 2, '2026-09-01'], ['erc-plus-2026', 2, '2026-09-02'],
      ['msca-pf', 2, '2026-09-09'], ['cost-netzwerk', 2, '2026-09-10'],
      ['dfg-emmy-noether', 2, '2026-10-01'], ['dfg-heisenberg', 2, '2026-10-01'],
      ['erc-stg-2027', 2, '2026-10-14'], ['volkswagen-stiftung', 2, '2026-10-15'],
    ]
  );
});

check('junior KI top6', () => {
  const res = matchProfile(PROGS, ['KI'], 'junior', { top: 6 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 2, '2026-09-02'], ['cost-netzwerk', 2, '2026-09-10'],
      ['erc-stg-2027', 2, '2026-10-14'], ['volkswagen-stiftung', 2, '2026-10-15'],
      ['eu-eic-pathfinder', 2, '2026-10-28'], ['daad-stipendium', 2, '2026-12-31'],
    ]
  );
});

check('postdoc BIOLOGIE uppercase (Case-Insensitivität)', () => {
  const res = matchProfile(PROGS, ['BIOLOGIE'], 'postdoc', { top: 3 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 2, '2026-09-02'], ['msca-pf', 2, '2026-09-09'],
      ['cost-netzwerk', 2, '2026-09-10'],
    ]
  );
});

check('postdoc Bio substring (Teilstring-Feld)', () => {
  const res = matchProfile(PROGS, ['Bio'], 'postdoc', { top: 3 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 2, '2026-09-02'], ['msca-pf', 2, '2026-09-09'],
      ['cost-netzwerk', 2, '2026-09-10'],
    ]
  );
});

check('postdoc Ökologie (Umlaut-Feld)', () => {
  const res = matchProfile(PROGS, ['Ökologie'], 'postdoc', { top: 5 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 2, '2026-09-02'], ['msca-pf', 2, '2026-09-09'],
      ['cost-netzwerk', 2, '2026-09-10'], ['dfg-emmy-noether', 2, '2026-10-01'],
      ['erc-stg-2027', 2, '2026-10-14'],
    ]
  );
});

check('null exotic field -> nur Wildcards treffen', () => {
  const res = matchProfile(PROGS, ['Exotisches Feld QX'], null, { top: 5 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 1, '2026-09-02'], ['msca-pf', 1, '2026-09-09'],
      ['cost-netzwerk', 1, '2026-09-10'], ['dfg-emmy-noether', 1, '2026-10-01'],
      ['dfg-heisenberg', 1, '2026-10-01'],
    ]
  );
});

check('junior 5 Felder top10 (Cap bei 3 gilt, Score 4)', () => {
  const res = matchProfile(PROGS, ['Biologie', 'Chemie', 'Physik', 'Mathematik', 'Informatik'], 'junior', { top: 10 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 4, '2026-09-02'], ['cost-netzwerk', 4, '2026-09-10'],
      ['erc-stg-2027', 4, '2026-10-14'], ['volkswagen-stiftung', 4, '2026-10-15'],
      ['eu-eic-pathfinder', 4, '2026-10-28'], ['daad-stipendium', 4, '2026-12-31'],
      ['msc-itn', 4, '2027-01-12'], ['erc-cog-2027', 4, '2027-01-12'],
      ['fritz-thyssen', 4, '2027-02-01'], ['msc-cofund', 4, '2027-03-20'],
    ]
  );
});

check('null Chemie rolle=lead top5', () => {
  const res = matchProfile(PROGS, ['Chemie'], null, { top: 5, rolle: 'lead' });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 1, '2026-09-02'], ['msca-pf', 1, '2026-09-09'],
      ['cost-netzwerk', 1, '2026-09-10'], ['dfg-emmy-noether', 1, '2026-10-01'],
      ['dfg-heisenberg', 1, '2026-10-01'],
    ]
  );
});

check('junior Biologie rolle=partner top5', () => {
  const res = matchProfile(PROGS, ['Biologie'], 'junior', { top: 5, rolle: 'partner' });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['cost-netzwerk', 2, '2026-09-10'], ['eu-eic-pathfinder', 2, '2026-10-28'],
      ['msc-itn', 2, '2027-01-12'], ['msc-cofund', 2, '2027-03-20'],
      ['erc-syg-2027', 2, '2027-05-11'],
    ]
  );
});

check('senior Biologie top5', () => {
  const res = matchProfile(PROGS, ['Biologie'], 'senior', { top: 5 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['cost-netzwerk', 2, '2026-09-10'], ['dfg-heisenberg', 2, '2026-10-01'],
      ['anr-attractiv-science', 2, '2026-12-01'], ['erc-syg-2027', 2, '2027-05-11'],
      ['erc-adg-2027', 2, null],
    ]
  );
});

check('student Biologie top5', () => {
  const res = matchProfile(PROGS, ['Biologie'], 'student', { top: 5 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['daad-stipendium', 2, '2026-12-31'], ['dfg-graduiertenkolleg', 2, null],
      ['studienstiftung-promotion', 2, null], ['deutschlandstipendium', 2, null],
      ['bfw-cusanuswerk', 2, null],
    ]
  );
});

check('real catalog: top=0 -> leere Trefferliste', () => {
  assert.deepStrictEqual(matchProfile(PROGS, ['Biologie'], 'postdoc', { top: 0 }), []);
});

check('real catalog: top=-5 -> leere Trefferliste', () => {
  assert.deepStrictEqual(matchProfile(PROGS, ['Biologie'], 'postdoc', { top: -5 }), []);
});

check('real catalog: Whitespace-Feld wird ignoriert', () => {
  const res = matchProfile(PROGS, ['Biologie', '   '], 'postdoc', { top: 5 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 2, '2026-09-02'], ['msca-pf', 2, '2026-09-09'],
      ['cost-netzwerk', 2, '2026-09-10'], ['dfg-emmy-noether', 2, '2026-10-01'],
      ['erc-stg-2027', 2, '2026-10-14'],
    ]
  );
});

check('null Psychologie top4', () => {
  const res = matchProfile(PROGS, ['Psychologie'], null, { top: 4 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 1, '2026-09-02'], ['msca-pf', 1, '2026-09-09'],
      ['cost-netzwerk', 1, '2026-09-10'], ['dfg-emmy-noether', 1, '2026-10-01'],
    ]
  );
});

check('prof Informatik top6', () => {
  const res = matchProfile(PROGS, ['Informatik'], 'prof', { top: 6 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 2, '2026-09-02'], ['cost-netzwerk', 2, '2026-09-10'],
      ['dfg-heisenberg', 2, '2026-10-01'], ['volkswagen-stiftung', 2, '2026-10-15'],
      ['eu-eic-pathfinder', 2, '2026-10-28'], ['eu-horizon-digital', 2, '2026-11-08'],
    ]
  );
});

check('postdoc Medizin top4', () => {
  const res = matchProfile(PROGS, ['Medizin'], 'postdoc', { top: 4 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 2, '2026-09-02'], ['msca-pf', 2, '2026-09-09'],
      ['cost-netzwerk', 2, '2026-09-10'], ['dfg-emmy-noether', 2, '2026-10-01'],
    ]
  );
});

// --- Tiefe Snapshots (top=30): prüfen die Sortierung bis weit in die Tabelle ---
check('deep snapshot: Nachhaltigkeit junior top30', () => {
  const res = matchProfile(PROGS, ['Nachhaltigkeit'], 'junior', { top: 30 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 2, '2026-09-02'], ['cost-netzwerk', 2, '2026-09-10'],
      ['erc-stg-2027', 2, '2026-10-14'], ['volkswagen-stiftung', 2, '2026-10-15'],
      ['eu-eic-pathfinder', 2, '2026-10-28'], ['dbu-umwelt', 2, '2026-12-01'],
      ['daad-stipendium', 2, '2026-12-31'], ['msc-itn', 2, '2027-01-12'],
      ['erc-cog-2027', 2, '2027-01-12'], ['fritz-thyssen', 2, '2027-02-01'],
      ['bmbf-energie-nachhaltigkeit', 2, '2027-02-28'], ['msc-cofund', 2, '2027-03-20'],
      ['erc-syg-2027', 2, '2027-05-11'], ['dfg-sachbeihilfe', 2, null],
      ['dfg-graduiertenkolleg', 2, null], ['loewe-hessen', 2, null],
      ['bfw-cusanuswerk', 2, null], ['bfw-ev-studienwerk', 2, null],
      ['bfw-fes', 2, null], ['bfw-hbs', 2, null], ['bfw-kas', 2, null],
      ['bfw-rls', 2, null], ['bfw-hss', 2, null], ['bfw-fns', 2, null],
      ['bfw-sdw', 2, null], ['bfw-avicenna', 2, null], ['dfg-irtg', 2, null],
      ['max-weber-bayern', 2, null], ['dfg-forschungsgruppen', 2, null],
      ['dfg-schwerpunktprogramme', 2, null],
    ]
  );
});

check('deep snapshot: Informatik+Robotik prof top30', () => {
  const res = matchProfile(PROGS, ['Informatik', 'Robotik'], 'prof', { top: 30 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score, r.frist ?? null]),
    [
      ['erc-plus-2026', 3, '2026-09-02'], ['cost-netzwerk', 3, '2026-09-10'],
      ['dfg-heisenberg', 3, '2026-10-01'], ['volkswagen-stiftung', 3, '2026-10-15'],
      ['eu-eic-pathfinder', 3, '2026-10-28'], ['anr-attractiv-science', 3, '2026-12-01'],
      ['fritz-thyssen', 3, '2027-02-01'], ['erc-syg-2027', 3, '2027-05-11'],
      ['erc-adg-2027', 3, null], ['dfg-sachbeihilfe', 3, null],
      ['dfg-sfb', 3, null], ['loewe-hessen', 3, null], ['humboldt-prof', 3, null],
      ['dfg-reinhart-koselleck', 3, null], ['dfg-forschungsgruppen', 3, null],
      ['dfg-schwerpunktprogramme', 3, null], ['dfg-kolleg-forschungsgruppen', 3, null],
      ['dfg-wissenschaftliche-netzwerke', 3, null], ['dfg-forschungsimpulse', 3, null],
      ['humboldt-forschungsstipendium', 3, null], ['nrw-mwk-wissenschaft', 3, null],
      ['nsf-international', 3, null], ['ukri-international', 3, null],
      ['dach-snsf-fwf', 3, null], ['kavli-foundation', 3, null],
      ['templeton-foundation', 3, null], ['leverhulme-trust', 3, null],
      ['royal-society', 3, null], ['jsps-international', 3, null],
      ['arc-international', 3, null],
    ]
  );
});

// ---------------------------------------------------------------------------
// 2.2  matchProfile(): Fixture-Randfälle (TEST-JS-2)
//      Vollständige Begründungs- und Punkte-Texte 1:1 aus mcp/match.py
//      übernommen (weniger Fixtures HABEN KEINE Frist -> deterministisch).
// ---------------------------------------------------------------------------
section('2.2  matchProfile() – Fixture-Randfälle (TEST-JS-2, Erwartungswerte aus mcp/match.py)');

const WILD = [
  { id: 'a-frei', name: 'A frei', themen: ['frei'], karriere: ['prof'], frist: null, rolling: false,
    kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: [] },
  { id: 'b-alle', name: 'B alle', themen: ['alle'], karriere: ['prof'], frist: null, rolling: false,
    kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: 500, rolle: [] },
  { id: 'c-offen', name: 'C offen', themen: ['thematisch-offen'], karriere: ['prof'], frist: null, rolling: false,
    kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: [] },
  { id: 'd-kein', name: 'D kein', themen: ['Astronomie'], karriere: ['prof'], frist: null, rolling: false,
    kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: [] },
];

check('Wildcard-Varianten: frei/alle/thematisch-offen matchen exotisches Feld', () => {
  const res = matchProfile(WILD, ['Chemie'], 'prof', { top: 10 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score]),
    [['a-frei', 2], ['b-alle', 2], ['c-offen', 2]]
  );
  // Programm ohne Treffer (Astronomie) erscheint nicht
  assert.ok(!res.some((r) => r.id === 'd-kein'));
});

check('Wildcard "frei" -> Begründung enthält "offen fuer alle Fachrichtungen"', () => {
  const res = matchProfile(WILD, ['Chemie'], 'prof', { top: 10 });
  const a = res.find((r) => r.id === 'a-frei');
  assert.strictEqual(
    a.begruendung,
    'Themen-Ueberlappung: Chemie; offen fuer alle Fachrichtungen; Karrierestufe passt zum Programm; ' +
      'Frist noch offen – vor Nutzung gegen Portal prüfen'
  );
  assert.deepStrictEqual(a.punkte, [
    { name: 'Thema', punkte: 1, max: 3, detail: 'Chemie' },
    { name: 'Karriere', punkte: 1, max: 1, detail: 'Karrierestufe im Programm gelistet' },
  ]);
});

check('Wildcard "alle" mit winzigem Budget -> "bis ca. 0 Tausend Euro"', () => {
  const res = matchProfile(WILD, ['Chemie'], 'prof', { top: 10 });
  const b = res.find((r) => r.id === 'b-alle');
  assert.strictEqual(
    b.begruendung,
    'Themen-Ueberlappung: Chemie; offen fuer alle Fachrichtungen; Karrierestufe passt zum Programm; ' +
      'Frist noch offen – vor Nutzung gegen Portal prüfen; bis ca. 0 Tausend Euro'
  );
});

check('Wildcard "thematisch-offen" -> KEIN "offen fuer alle Fachrichtungen" (Parität!)', () => {
  const res = matchProfile(WILD, ['Chemie'], 'prof', { top: 10 });
  const c = res.find((r) => r.id === 'c-offen');
  assert.strictEqual(
    c.begruendung,
    'Themen-Ueberlappung: Chemie; Karrierestufe passt zum Programm; ' +
      'Frist noch offen – vor Nutzung gegen Portal prüfen'
  );
  assert.ok(!c.begruendung.includes('offen fuer alle Fachrichtungen'));
});

const SAME = [
  { id: 'x1', name: 'X1', themen: ['frei'], karriere: ['prof'], frist: '2026-09-09', rolling: false,
    kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: [] },
  { id: 'x2', name: 'X2', themen: ['frei'], karriere: ['prof'], frist: '2026-09-09', rolling: false,
    kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: [] },
  { id: 'x3', name: 'X3', themen: ['frei'], karriere: ['prof'], frist: '2026-09-09', rolling: false,
    kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: [] },
];

check('stabile Sortierung: gleicher Score + gleiche Frist -> Katalog-Reihenfolge', () => {
  const res = matchProfile(SAME, ['Chemie'], 'prof', { top: 3 });
  assert.deepStrictEqual(
    res.map((r) => r.id),
    ['x1', 'x2', 'x3']
  );
});

check('hits folgen der REIHENFOLGE DER FELDER (nicht der Themen-Liste)', () => {
  const res = matchProfile(FIX, ['Chemie', 'Bio', 'Physik'], 'prof', { top: 10 });
  const p3 = res.find((r) => r.id === 'p3');
  assert.deepStrictEqual(p3.punkte[0].detail, 'Chemie, Bio, Physik');
  assert.strictEqual(p3.begruendung, 'Themen-Ueberlappung: Chemie, Bio, Physik; Karrierestufe passt zum Programm; ' +
    'Frist noch offen – vor Nutzung gegen Portal prüfen; bis ca. 2.0 Mio. Euro');
  // p2 (frei, prof, rolling) matcht alle drei Felder ebenfalls exakt wie Python
  const p2 = res.find((r) => r.id === 'p2');
  assert.strictEqual(p2.begruendung, 'Themen-Ueberlappung: Chemie, Bio, Physik; offen fuer alle Fachrichtungen; ' +
    'Karrierestufe passt zum Programm; Rolling – jederzeit einreichbar, keine feste Frist');
});

const BUDGET_TEXT = {
  id: 'c1', name: 'C1', themen: ['Bio'], karriere: ['postdoc'], frist: null, rolling: false,
  kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01',
  budget_max: 500000, budget_text: 'Custom text here', rolle: [],
};

check('budget_text überschreibt budget_beschreibung', () => {
  const res = matchProfile([BUDGET_TEXT], ['Biologie'], 'postdoc', { top: 5 });
  const r = res[0];
  assert.strictEqual(r.begruendung, 'Themen-Ueberlappung: Biologie; Karrierestufe passt zum Programm; ' +
    'Frist noch offen – vor Nutzung gegen Portal prüfen; Custom text here');
  assert.deepStrictEqual(r.punkte, [
    { name: 'Thema', punkte: 1, max: 3, detail: 'Biologie' },
    { name: 'Karriere', punkte: 1, max: 1, detail: 'Karrierestufe im Programm gelistet' },
  ]);
});

const DUP = {
  id: 'd1', name: 'D1', themen: ['Bio'], karriere: ['postdoc'], frist: null, rolling: false,
  kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: [],
};

check('doppelte Felder bleiben in der Trefferliste (Parität zum Python-Verhalten)', () => {
  const res = matchProfile([DUP], ['Biologie', 'Biologie', 'Chemie'], 'postdoc', { top: 5 });
  const r = res[0];
  assert.strictEqual(r.score, 3); // thema 2 (gekappt nicht nötig) + karriere 1
  assert.deepStrictEqual(r.punkte[0].detail, 'Biologie, Biologie');
  assert.strictEqual(r.begruendung, 'Themen-Ueberlappung: Biologie, Biologie; Karrierestufe passt zum Programm; ' +
    'Frist noch offen – vor Nutzung gegen Portal prüfen');
});

const FREI_PLUS = {
  id: 'e1', name: 'E1', themen: ['frei', 'Biologie'], karriere: ['postdoc'], frist: null, rolling: false,
  kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: [],
};

check('themen=[frei, ...] -> Begründung enthält "offen fuer alle Fachrichtungen"', () => {
  const res = matchProfile([FREI_PLUS], ['Biologie'], 'postdoc', { top: 5 });
  assert.ok(res[0].begruendung.includes('offen fuer alle Fachrichtungen'));
});

check('Programm ohne Karriere-Liste wird vom harten Filter NICHT ausgeschlossen (p4)', () => {
  const res = matchProfile(FIX, ['Medizin'], 'postdoc', { top: 10 });
  assert.deepStrictEqual(res.map((r) => r.id), ['p4']);
  const p4 = res[0];
  assert.strictEqual(p4.score, 1);
  assert.strictEqual(p4.begruendung, 'Themen-Ueberlappung: Medizin; Karrierestufe nicht gelistet – Eignung im Einzelfall prüfen; ' +
    'Frist noch offen – vor Nutzung gegen Portal prüfen; Achtung: Details/Frist vor Antrag gegen Portal prüfen');
  assert.deepStrictEqual(p4.punkte, [
    { name: 'Thema', punkte: 1, max: 3, detail: 'Medizin' },
    { name: 'Karriere', punkte: 0, max: 1, detail: null },
  ]);
});

check('unbekannte Karrierestufe -> leere Trefferliste (Fixture)', () => {
  assert.deepStrictEqual(matchProfile(FIX, ['Bio'], 'professorin', { top: 10 }), []);
});

const ROLLE_FIX = [
  { id: 'p1', name: 'P1', themen: ['Bio'], karriere: ['postdoc'], frist: null, rolling: false,
    kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: [] },
  { id: 'p2', name: 'P2', themen: ['Bio'], karriere: ['postdoc'], frist: null, rolling: false,
    kategorie: 'K', status: 'verifiziert', quelle: 'q', standDatum: '2026-01-01', budget_max: null, rolle: ['lead'] },
];

check('Rollen-Filter: Programm mit leerer rolle-Liste wird ausgeschlossen', () => {
  assert.deepStrictEqual(
    matchProfile(ROLLE_FIX, ['Biologie'], 'postdoc', { top: 5, rolle: 'lead' }).map((r) => r.id),
    ['p2']
  );
  assert.deepStrictEqual(
    matchProfile(ROLLE_FIX, ['Biologie'], 'postdoc', { top: 5 }).map((r) => r.id),
    ['p1', 'p2']
  );
});

check('harter Karriere-Filter + Rollen und Cap: Reihenfolge p2(3) > p3(2) > p4(1)', () => {
  const res = matchProfile(FIX, ['Medizin', 'Bio'], 'prof', { top: 10 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score]),
    [['p2', 3], ['p3', 2], ['p4', 1]]
  );
  const p4 = res.find((r) => r.id === 'p4');
  assert.deepStrictEqual(p4.punkte[0].detail, 'Medizin');
});

check('5 Felder auf Fixture: Cap bei 3, Detail listet alle Treffer', () => {
  const res = matchProfile(FIX, ['Bio', 'Biologie', 'Chemie', 'Physik', 'Mathematik'], 'postdoc', { top: 10 });
  assert.deepStrictEqual(
    res.map((r) => [r.id, r.score]),
    [['p3', 4], ['p1', 3]]
  );
  const p3 = res[0];
  assert.deepStrictEqual(p3.punkte[0].detail, 'Bio, Biologie, Chemie, Physik, Mathematik');
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
