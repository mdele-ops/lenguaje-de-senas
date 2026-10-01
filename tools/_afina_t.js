window.__afinaT = async function (n, semilla) {
  const ctl = window.__LSM_CONTROLLER__;
  const base = JSON.parse(JSON.stringify(ctl.getCatalog().senas.find((s) => s.letra === 'T').pose));
  let s = semilla || 99;
  const rnd = () => { s = (s * 1664525 + 1013904223) % 4294967296; return s / 4294967296; };
  const pm = (a) => (rnd() * 2 - 1) * a;
  const b = { tcurl: 0.2, sep: 9.6, t1x: -16.4, t1y: -7.5, t1z: 77.4, t2x: 40.9, t3x: 22.8 };
  const arma = (r) => {
    const p = JSON.parse(JSON.stringify(base));
    p.thumb = Object.assign({}, p.thumb, { curl: r.tcurl });
    p.index.spread = -r.sep; p.middle.spread = r.sep;
    p.extra.RightHandThumb1 = { x: r.t1x, y: r.t1y, z: r.t1z };
    p.extra.RightHandThumb2 = { x: r.t2x };
    p.extra.RightHandThumb3 = { x: r.t3x };
    return p;
  };
  const med = (r) => { ctl.applyTestPose(arma(r)); return window.__medT(); };
  const m0 = med(b);
  const obj = 0.165; // gap con el indice: un poco mas que 0.130
  const res = [];
  for (let i = 0; i < n; i++) {
    const r = { tcurl: b.tcurl + pm(0.08), sep: b.sep + pm(3), t1x: b.t1x + pm(8), t1y: b.t1y + pm(10),
      t1z: b.t1z + pm(8), t2x: b.t2x + pm(10), t3x: b.t3x + pm(10) };
    if (r.tcurl < 0) r.tcurl = 0;
    const m = med(r);
    const castigo = 12 * Math.abs(m.gapIdxPunta - obj)
      + 10 * Math.abs(m.camDesvio - m0.camDesvio) + 10 * Math.abs(m.camCima - m0.camCima)
      + 10 * Math.abs(m.sobreFrente - m0.sobreFrente) + 6 * Math.abs(m.gapMedPunta - m0.gapMedPunta)
      + 3 * Math.abs(m.thUpDir - m0.thUpDir) + 0.003 * Math.abs(m.dobla - m0.dobla)
      + 20 * Math.max(0, 0.095 - m.gapMedPunta) + 10 * Math.abs(r.sep - b.sep) / 10;
    res.push({ p: castigo, r, m: { cd: m.camDesvio, cc: m.camCima, so: m.sobreFrente, up: m.thUpDir,
      gI: m.gapIdxPunta, gM: m.gapMedPunta, gB: m.gapBase, dob: m.dobla } });
  }
  res.sort((a, c) => a.p - c.p);
  window.__afinaTres = res; window.__armaT = arma;
  return { m0: { cd: m0.camDesvio, cc: m0.camCima, so: m0.sobreFrente, up: m0.thUpDir, gI: m0.gapIdxPunta, gM: m0.gapMedPunta, dob: m0.dobla }, top: res.slice(0, 5) };
};