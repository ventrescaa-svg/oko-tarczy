// Puszcza prawdziwy Detector z oko-tarczy.html na wycinkach z eksportu "Nauka AI".
// Użycie: node narzedzia/test_rzutow.js oko-tarczy.html katalog_z_rozpakuj [walk|old]
//   NOISE=4 SEED=1  -> dodaje szum kamery (sprawdzenie stabilności), V=1 -> lista rzutów
// Wynik: ile rzutów dostało to samo pole, co ostatecznie zapisał gracz (tap = poprawione stuknięciem).
const fs = require('fs'), path = require('path'), os = require('os');
const [htmlFile, dir, mode] = process.argv.slice(2);
const html = fs.readFileSync(htmlFile, 'utf8');
const core = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
const tmp = path.join(os.tmpdir(), 'oko-core-' + process.pid + '.js');
fs.writeFileSync(tmp, core);
const C = require(tmp);
const M = JSON.parse(fs.readFileSync(path.join(dir, 'manifest.json'), 'utf8'));
let n = 0, ok = 0, tapN = 0, tapOk = 0, prior = 0, skipped = 0;
const rows = [];
M.samples.forEach((s, k) => {
  const id = k + 1;
  const rd = (t) => new Uint8ClampedArray(fs.readFileSync(path.join(dir, `${String(id).padStart(3, '0')}_${t}.rgba`)));
  const ref = rd('ref'), cur = rd('cur');
  // próbki sprzed 2026.10.17 bywają bez zdjęcia "przed" (ref == cur) - nie da się ich odtworzyć
  if (Buffer.from(ref).equals(Buffer.from(cur)) || s.label.source === 'deleted' || s.label.source === 'keypad') { skipped++; return; }
  if (process.env.NOISE) {
    let seed = (+process.env.SEED || 1) * 7919 + id * 104729;
    const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
    const g = () => { let u = 0; for (let t = 0; t < 4; t++) u += rnd(); return (u - 2) * 1.732; };
    for (const im of [ref, cur]) for (let i = 0; i < im.length; i += 4) for (let c = 0; c < 3; c++) im[i + c] += g() * +process.env.NOISE;
  }
  const w = s.crop.w, h = s.crop.h;
  const Hp = C.mulH([1, 0, -s.crop.x0, 0, 1, -s.crop.y0, 0, 0, 1], s.proc.Hp);
  const pp = [(s.video[0] / 2 - s.proc.x) * s.proc.s - s.crop.x0, (s.video[1] / 2 - s.proc.y) * s.proc.s - s.crop.y0];
  const c = C.applyH(s.proc.Hp, 0, 0), p6 = C.applyH(s.proc.Hp, 170, 0), p11 = C.applyH(s.proc.Hp, -170, 0);
  const q = Math.hypot(p6[0] - c[0], p6[1] - c[1]) >= Math.hypot(p11[0] - c[0], p11[1] - c[1]) ? p6 : p11, l = Math.hypot(q[0] - c[0], q[1] - c[1]);
  const cfg = { w, h, Hp, nearDir: [(q[0] - c[0]) / l, (q[1] - c[1]) / l], thr: 60, shadows: true, pp,
    pointMm: +(process.env.PMM || s.pointMm || 14), pointMaxMm: +(process.env.PMAX || 25) };
  if (mode === 'walk') cfg.tipModel = 'walk';
  if (process.env.NOSHADOW) cfg.shadowTip = false;   // bez grota z cienia rzutki (19u)
  if (mode === 'old') cfg.offsetMm = s.offsetMm || 0;   // stare wersje z "Korektą grota"
  const det = new C.Detector(cfg);
  det.reset(ref);
  // od 2026.10.19q próbka ma też stan detektora: poprzednie rzutki tury (occ) i numer rzutu w turze
  const occFile = path.join(dir, `${String(id).padStart(3, '0')}_occ.rgba`);
  if (!process.env.NOSTATE && s.dartsInTurn > 1 && fs.existsSync(occFile)) {
    const o = rd('occ'); for (let i = 0; i < w * h; i++) det.occ[i] = o[i * 4] > 127 ? 1 : 0;
    det.dartsInTurn = s.dartsInTurn - 1;
  }
  const ev = det.analyze(Uint8ClampedArray.from(cur), 1000, false, false);
  const d = ev.find(e => e.type === 'dart');
  n++; const tap = s.label.source === 'tap'; if (tap) tapN++;
  if (!d) { rows.push(`${id} ${s.label.source} ${s.label.label} -> brak rzutki`); return; }
  // HI=1: grot jeszcze raz na ostrym wycinku (od 2026.10.19l), tak jak hiRefine w aplikacji
  if (process.env.HI && s.hiCrop && fs.existsSync(path.join(dir, `${String(id).padStart(3, '0')}_hiref.rgba`))) {
    const hc = s.hiCrop, z = hc.z, ox = (s.crop.x0 / s.crop.k) * z - hc.x0, oy = (s.crop.y0 / s.crop.k) * z - hc.y0;   // crop px -> hi px
    const hr = rd('hiref'), hcur = rd('hicur'), bt = d.det.barrelTip;
    const thrLow = Math.max(det.pointMin, det.pointK * (det.noise || 0));
    const r = C.refineTipHi(hr, hcur, hc.w, hc.h, det.lastGain || 1, { tip: [bt[0] * z + ox, bt[1] * z + oy], axis: d.det.axis }, z,
      { thrLow, pxPerMm: d.det.pxPerMm * z, pointMm: det.pointMm, pointMaxMm: det.pointMaxMm });
    const tip = [(r.tip[0] - ox) / z, (r.tip[1] - oy) / z], b = C.applyH(det.Hpi, tip[0], tip[1]);
    if (Math.hypot(b[0] - d.board[0], b[1] - d.board[1]) <= +(process.env.HIMAX || 15)) { d.board = b; d.det.tip = tip; d.det.tipBy = r.byPrior ? 'prior' : 'seen'; }
    // od 2026.10.19u: cień rzutki poprawia grot "zobaczony" także po ostrym obrazie, tak jak w aplikacji
    if (!process.env.NOSHADOW && C.fuseShadowTip(d.det, 1.1 * det.pointMaxMm * d.det.pxPerMm)) d.board = C.applyH(det.Hpi, d.det.tip[0], d.det.tip[1]);
  }
  const lab = C.scoreAt(d.board[0], d.board[1]).label, good = lab === s.label.label;
  ok += good; if (tap) tapOk += good; if (d.det.tipBy === 'prior') prior++;
  rows.push(`${String(id).padStart(3)} ${s.label.source.padEnd(9)} gracz=${s.label.label.padEnd(4)} app=${lab.padEnd(4)} ${good ? 'OK ' : 'ŹLE'} grot:${d.det.tipBy}`);
});
fs.unlinkSync(tmp);
if (process.env.V) console.log(rows.join('\n'));
console.log(`rzutów ${n}: dobre pole ${ok} | poprawiane stuknięciem: ${tapOk}/${tapN} | grot zgadnięty z długości: ${prior} | pominięte: ${skipped}`);
