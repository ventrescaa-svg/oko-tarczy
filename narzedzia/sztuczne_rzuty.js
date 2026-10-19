// Synthetic throws rendered at full video resolution (1080x1920) on Piotr's real board picture:
// low-res tip (processing picture, 540x960) vs refineTipHi on the full-res crop.
const fs = require('fs'); const SP = process.env.SP || __dirname;
const html = fs.readFileSync(process.env.HTML || '/home/claude/oko-tarczy/oko-tarczy.html', 'utf8');
fs.writeFileSync(SP + '/core_s.js', [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1]);
const C = require(SP + '/core_s.js');
const VW = 1080, VH = 1920, W = 540, H = 960;
const bg = new Uint8ClampedArray(fs.readFileSync(SP + '/img/plain2.rgba'));
const Hv = JSON.parse(fs.readFileSync(SP + '/Hnew2.json'));
const Hp = C.mulH([0.5, 0, 0, 0, 0.5, 0, 0, 0, 1], Hv), Hpi = C.invertH(Hp);
const cam = C.cameraFromH(Hv, VW / 2, VH / 2);
let seed = +(process.env.SEED || 7); const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff; };
const gauss = () => { let u = 0; for (let t = 0; t < 4; t++) u += rnd(); return (u - 2) * 1.732; };
const NS = +(process.env.NOISE || 3), BLUR = +(process.env.BLUR || 0.8);
function blur(img, w, h, sig, x0, y0, x1, y1) {
  if (!sig) return img;
  const r = Math.ceil(2.5 * sig), k = []; let s = 0; for (let i = -r; i <= r; i++) { const v = Math.exp(-i * i / (2 * sig * sig)); k.push(v); s += v; }
  for (let i = 0; i < k.length; i++) k[i] /= s;
  const tmp = new Float32Array(img.length), out = Uint8ClampedArray.from(img);
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) for (let c = 0; c < 3; c++) { let a = 0; for (let i = -r; i <= r; i++) a += k[i + r] * img[(y * w + Math.min(w - 1, Math.max(0, x + i))) * 4 + c]; tmp[(y * w + x) * 4 + c] = a; }
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) for (let c = 0; c < 3; c++) { let a = 0; for (let i = -r; i <= r; i++) { const yy = Math.min(y1 - 1, Math.max(y0, y + i)); a += k[i + r] * tmp[(yy * w + x) * 4 + c]; } out[(y * w + x) * 4 + c] = a; }
  return out;
}
function addNoise(img) { const o = Uint8ClampedArray.from(img); for (let i = 0; i < o.length; i++) if ((i & 3) !== 3) o[i] = o[i] + gauss() * NS; return o; }
function down(img) { // 2x2 box -> processing picture
  const o = new Uint8ClampedArray(W * H * 4);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) { const p = ((2 * y) * VW + 2 * x) * 4, q = p + VW * 4, d = (y * W + x) * 4;
    for (let c = 0; c < 3; c++) o[d + c] = (img[p + c] + img[p + 4 + c] + img[q + c] + img[q + 4 + c] + 2) >> 2; o[d + 3] = 255; }
  return o;
}
// Dart in 3D: tip at board (bx,by,0), axis dir; parts [z0,z1,radius,color] along the axis (mm).
function renderDart(img, bx, by, dir, vis, ptCol) {
  const parts = [[0, vis, 1.2, ptCol], [vis, vis + 40, 3.6, 'bar'], [vis + 40, vis + 75, 2.2, [40, 50, 150]], [vis + 75, vis + 110, 9, [210, 40, 40]]];
  const P = (t) => C.camProject(cam, bx + dir[0] * t, by + dir[1] * t, dir[2] * t);
  let minx = 1e9, miny = 1e9, maxx = -1e9, maxy = -1e9;
  const segs = parts.map(([a, b, r, col]) => { const p = P(a), q = P(b); const zc = (cam.r1[2] * (bx + dir[0] * (a + b) / 2) + cam.r2[2] * (by + dir[1] * (a + b) / 2) + cam.r3[2] * dir[2] * (a + b) / 2 + cam.t[2]);
    const rp = r * cam.f / zc; [p, q].forEach(v => { minx = Math.min(minx, v[0] - rp - 2); maxx = Math.max(maxx, v[0] + rp + 2); miny = Math.min(miny, v[1] - rp - 2); maxy = Math.max(maxy, v[1] + rp + 2); });
    return { p, q, rp, col }; });
  const x0 = Math.max(0, Math.floor(minx)), x1 = Math.min(VW, Math.ceil(maxx)), y0 = Math.max(0, Math.floor(miny)), y1 = Math.min(VH, Math.ceil(maxy));
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) {
    const acc = [0, 0, 0]; let cov = 0;
    for (let sy = 0; sy < 3; sy++) for (let sx = 0; sx < 3; sx++) {
      const X = x + (sx + 0.5) / 3, Y = y + (sy + 0.5) / 3;
      for (let k = segs.length - 1; k >= 0; k--) { // point drawn last wins (nearest the board)
        const { p, q, rp, col } = segs[k];
        const dx = q[0] - p[0], dy = q[1] - p[1], L2 = dx * dx + dy * dy;
        let t = L2 ? ((X - p[0]) * dx + (Y - p[1]) * dy) / L2 : 0; if (t < 0 || t > 1) continue;
        const ex = X - (p[0] + t * dx), ey = Y - (p[1] + t * dy), d = Math.hypot(ex, ey);
        if (d > rp) continue;
        let c;
        if (col === 'bar') { const sh = 0.6 + 0.4 * Math.cos(d / rp * 1.4); const knurl = (Math.floor(t * 30) & 1) ? 0.85 : 1; c = [200 * sh * knurl, 202 * sh * knurl, 208 * sh * knurl]; }
        else c = col.map(v => v * (0.8 + 0.4 * (1 - d / rp)));
        acc[0] += c[0]; acc[1] += c[1]; acc[2] += c[2]; cov++;
        k = -1; break;
      }
      if (cov === 0) {}
    }
    if (!cov) continue;
    const o = (y * VW + x) * 4, f = cov / 9;
    for (let c = 0; c < 3; c++) img[o + c] = img[o + c] * (1 - f) + acc[c] / cov * f;
  }
  return [x0, y0, x1, y1];
}
const N = +(process.env.N || 40);
const res = { lo: [], hi: [], loOk: 0, hiOk: 0, n: 0, hiPrior: 0, loPrior: 0 };
const zH = 2;
for (let n = 0; n < N; n++) {
  const r = Math.sqrt(rnd()) * 165, a = rnd() * 2 * Math.PI, bx = r * Math.cos(a), by = r * Math.sin(a);
  const tx = (rnd() - 0.5) * 0.35, ty = (rnd() - 0.3) * 0.4; const dir = [tx, -ty, 1]; const nn = Math.hypot(...dir); dir.forEach((v, i) => dir[i] = v / nn);
  const vis = 10 + rnd() * 8, ptCol = rnd() < 0.85 ? [35, 35, 38] : [150, 150, 155];
  const before = blur(bg, VW, VH, BLUR, 0, 0, VW, VH);
  const after = Uint8ClampedArray.from(bg); const bb = renderDart(after, bx, by, dir, vis, ptCol);
  const afterB = blur(after, VW, VH, BLUR, Math.max(0, bb[0] - 5), Math.max(0, bb[1] - 5), Math.min(VW, bb[2] + 5), Math.min(VH, bb[3] + 5));
  const fb = addNoise(before), fa = addNoise(afterB);
  const lb = down(fb), la = down(fa);
  const det = new C.Detector({ w: W, h: H, Hp, nearDir: [1, 0], thr: 60, shadows: true, pp: [W / 2, H / 2], pointMm: 14, pointMaxMm: 25 });
  let t = 0; det.step(lb, t); for (let k = 0; k < 3; k++) { t += 100; det.step(down(addNoise(before)), t); }
  const ev = det.analyze(la, t + 100, false, false).find(e => e.type === 'dart');
  const truth = [bx, by], tl = C.scoreAt(bx, by).label;
  if (!ev) { console.log(n, 'brak rzutki', tl); continue; }
  res.n++;
  const bLo = ev.board, eLo = Math.hypot(bLo[0] - bx, bLo[1] - by);
  // hi
  const d = ev.det, bt = d.barrelTip, R = Math.round(zH * 100);
  const cx0 = Math.max(0, Math.round(bt[0] * zH) - R), cy0 = Math.max(0, Math.round(bt[1] * zH) - R);
  const cw = Math.min(VW - cx0, 2 * R), ch = Math.min(VH - cy0, 2 * R);
  const crop = (img) => { const o = new Uint8ClampedArray(cw * ch * 4); for (let y = 0; y < ch; y++) o.set(img.subarray(((y + cy0) * VW + cx0) * 4, ((y + cy0) * VW + cx0 + cw) * 4), y * cw * 4); return o; };
  const thrLow = Math.max(det.pointMin, det.pointK * (det.noise || 0)) * (+(process.env.TK || 1));
  const Rh = C.refineTipHi(crop(fb), crop(fa), cw, ch, det.lastGain || 1, { tip: [bt[0] * zH - cx0, bt[1] * zH - cy0], axis: d.axis }, zH,
    { thrLow, pxPerMm: d.pxPerMm * zH, pointMm: 14, pointMaxMm: 25 });
  const tipP = [(Rh.tip[0] + cx0) / zH, (Rh.tip[1] + cy0) / zH], bHi = C.applyH(Hpi, tipP[0], tipP[1]), eHi = Math.hypot(bHi[0] - bx, bHi[1] - by);
  const lLo = C.scoreAt(...bLo).label, lHi = C.scoreAt(...bHi).label;
  res.lo.push(eLo); res.hi.push(eHi); if (lLo === tl) res.loOk++; if (lHi === tl) res.hiOk++;
  if (d.tipBy === 'prior') res.loPrior++; if (Rh.byPrior) res.hiPrior++;
  if (process.env.V) console.log(n, tl, 'lo', lLo, eLo.toFixed(1), d.tipBy, ' hi', lHi, eHi.toFixed(1), Rh.byPrior ? 'prior' : 'seen', 'sh', Rh.shift.map(v => v.toFixed(2)).join(','), 'vis', vis.toFixed(0), JSON.stringify(Rh.info));
}
const med = (a) => { const b = a.slice().sort((x, y) => x - y); return b.length ? b[b.length >> 1] : NaN; };
const mean = (a) => a.reduce((s, v) => s + v, 0) / a.length;
console.log('rzutów', res.n, '| niska: pole', res.loOk, 'błąd śr', mean(res.lo).toFixed(2), 'med', med(res.lo).toFixed(2), 'zgad', res.loPrior,
  '| wysoka: pole', res.hiOk, 'błąd śr', mean(res.hi).toFixed(2), 'med', med(res.hi).toFixed(2), 'zgad', res.hiPrior);
