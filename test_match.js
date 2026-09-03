// Loader-Shim: erlaubt `node test_match.js` auch aus dem Repository-Wurzel.
// Die eigentlichen Tests + die 1:1-JS-Referenzimplementierung der Matching-Logik
// liegen in dashboard/test_match.js (einzige Quelle der Wahrheit).
//
// Hintergrund: Die TaskFleet-Acceptance-Gate führt `node test_match.js` aus dem
// Worktree-Root aus; der Test selbst liegt unter dashboard/. Dieser Shim leitet
// nur an dieselbe Datei weiter und ändert KEIN Testverhalten.

require('./dashboard/test_match.js');
