"""Por que en las pruebas el avatar sale en cruz y en la pagina no.

`rig.restCorrections` dobla hombro y codo UNA vez, antes de capturar el reposo.
Si eso no ha pasado, la mano se queda en la T del rig: las medidas de dedos
siguen valiendo (son rotaciones locales) pero la luz cae distinta y las fotos no
representan lo que ve la persona. Aqui se comprueba si la correccion esta puesta.
"""
import time

from playwright.sync_api import sync_playwright

from lab_e2 import abrir, preparar

BRAZO_JS = """
() => {
  const mv = document.getElementById('handViewer');
  let s = null;
  for (const sym of Object.getOwnPropertySymbols(mv)) {
    const v = mv[sym];
    if (v && typeof v.traverse === 'function') { s = v; break; }
    if (v && v.model && typeof v.model.traverse === 'function') { s = v.model; break; }
    if (v && v.target && typeof v.target.traverse === 'function') { s = v.target; break; }
  }
  s.updateMatrixWorld(true);
  const B = {};
  s.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const b = B[n];
    if (!b || !b.matrixWorld) return null;
    const e = b.matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const q = (n) => {
    const b = B[n];
    return b ? { x: +b.quaternion.x.toFixed(3), y: +b.quaternion.y.toFixed(3),
                 z: +b.quaternion.z.toFixed(3), w: +b.quaternion.w.toFixed(3) } : null;
  };
  const hombro = P('RightArm'), codo = P('RightForeArm'), mano = P('RightHand');
  const dir = (a, b) => {
    const d = { x: b.x-a.x, y: b.y-a.y, z: b.z-a.z };
    const l = Math.hypot(d.x, d.y, d.z) || 1;
    return { x: +(d.x/l).toFixed(2), y: +(d.y/l).toFixed(2), z: +(d.z/l).toFixed(2) };
  };
  return {
    animacion: mv.animationName || null,
    animaciones: (mv.availableAnimations || []).slice(0, 8),
    brazoQ: q('RightArm'),
    antebrazo: dir(hombro, codo),   // y ~ 0 = en cruz, y < 0 = brazo bajado
    manoDesdeCodo: dir(codo, mano),
    alturaMano: +mano.y.toFixed(3),
    alturaCabeza: P('Head') ? +P('Head').y.toFixed(3) : null,
  };
}
"""


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        preparar(page)
        print("al cargar:            ", page.evaluate(BRAZO_JS))
        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('F', { loop: false })")
        time.sleep(3.4)
        print("tras mostrar la F:    ", page.evaluate(BRAZO_JS))
        print("vuelve a leer el esqueleto:",
              page.evaluate("() => window.__LSM_CONTROLLER__.refreshSkeleton()"))
        page.evaluate("() => window.__LSM_CONTROLLER__.mostrarSena('F', { loop: false })")
        time.sleep(3.4)
        print("tras releer y mostrar:", page.evaluate(BRAZO_JS))
        browser.close()


if __name__ == "__main__":
    main()
