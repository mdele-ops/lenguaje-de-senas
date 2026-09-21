"""Mide los angulos reales de cada articulacion del indice.

Sirve para comprobar si `extra` (grados sueltos por hueso) produce la misma
flexion que `curl`, y hacia donde apunta cada falange respecto de la palma.
"""
import time

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, BONES, FINGERS, _GET_SCENE
from search_e9 import abrir

ANG_JS = (
    """
() => {
  const mv = document.getElementById('handViewer');
"""
    + _GET_SCENE
    + """
  const scene = getScene(mv);
  scene.updateMatrixWorld(true);
  const B = {};
  scene.traverse((o) => { if (o && o.name) B[o.name] = o; });
  const P = (n) => {
    const e = B[n].matrixWorld.elements;
    return { x: e[12], y: e[13], z: e[14] };
  };
  const sub = (a, b) => ({ x: a.x-b.x, y: a.y-b.y, z: a.z-b.z });
  const norm = (v) => { const l = Math.hypot(v.x, v.y, v.z) || 1; return { x: v.x/l, y: v.y/l, z: v.z/l }; };
  const dot = (a, b) => a.x*b.x + a.y*b.y + a.z*b.z;
  const cross = (a, b) => ({ x: a.y*b.z-a.z*b.y, y: a.z*b.x-a.x*b.z, z: a.x*b.y-a.y*b.x });
  const ang = (a, b) => Math.acos(Math.max(-1, Math.min(1, dot(norm(a), norm(b))))) * 180 / Math.PI;

  const wrist = P('mixamorig1RightHand_035');
  const k1 = P('mixamorig1RightHandIndex1_040');
  const k4 = P('mixamorig1RightHandPinky1_052');
  // marco de la palma: largo (muneca->nudillo indice), ancho (indice->menique)
  const largo = norm(sub(k1, wrist));
  const ancho = norm(sub(k4, k1));
  const normal = norm(cross(ancho, largo));  // sale por una de las caras

  const p1 = P('mixamorig1RightHandIndex1_040');
  const p2 = P('mixamorig1RightHandIndex2_041');
  const p3 = P('mixamorig1RightHandIndex3_042');
  const p4 = P('mixamorig1RightHandIndex4_043');
  const prox = sub(p2, p1), midd = sub(p3, p2), dist = sub(p4, p3);
  return {
    // flexion de cada articulacion (angulo entre falanges consecutivas)
    mcp: ang(largo, prox),
    pip: ang(prox, midd),
    dip: ang(midd, dist),
    // hacia donde mira la falange proximal: 0 = en el plano de la palma,
    // 90 = perpendicular (apuntando a la camara). En la E deberia rondar 60-90.
    proxFueraDePlano: 90 - ang(normal, prox),
    // altura de la yema respecto al nudillo, en largos de palma
    yemaBajoNudillo: dot(sub(p1, p4), largo) / (Math.hypot(k1.x-wrist.x, k1.y-wrist.y, k1.z-wrist.z) || 1),
  };
}
"""
)


def solo_extra(**grados):
    ex = {ARM: {"z": -18}}
    for f in FINGERS:
        b = BONES[f]
        if grados.get("mcp"):
            ex[b[0]] = {"x": grados["mcp"]}
        if grados.get("pip"):
            ex[b[1]] = {"x": grados["pip"]}
        if grados.get("dip"):
            ex[b[2]] = {"x": grados["dip"]}
    return {"extra": ex}


def con_curl(c):
    pose = {f: {"curl": c} for f in FINGERS}
    pose["extra"] = {ARM: {"z": -18}}
    return pose


CASOS = {
    "reposo": solo_extra(),
    "curl 0.5": con_curl(0.5),
    "curl 0.9": con_curl(0.9),
    "curl 1.0": con_curl(1.0),
    "extra mcp36": solo_extra(mcp=36),
    "extra mcp65": solo_extra(mcp=65),
    "extra mcp85": solo_extra(mcp=85),
    "extra mcp110": solo_extra(mcp=110),
    "extra 65/81/61": solo_extra(mcp=65, pip=81, dip=61),
    "extra 85/85/0": solo_extra(mcp=85, pip=85),
    "extra 110/95/40": solo_extra(mcp=110, pip=95, dip=40),
}


def main():
    with sync_playwright() as p:
        browser, page = abrir(p)
        print(f"{'caso':18s} {'mcp':>6s} {'pip':>6s} {'dip':>6s} {'proxFuera':>10s} {'yema<nud':>9s}")
        for nombre, pose in CASOS.items():
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            time.sleep(0.25)
            a = page.evaluate(ANG_JS)
            print(
                f"{nombre:18s} {a['mcp']:6.1f} {a['pip']:6.1f} {a['dip']:6.1f} "
                f"{a['proxFueraDePlano']:10.1f} {a['yemaBajoNudillo']:9.2f}"
            )
        browser.close()


if __name__ == "__main__":
    main()
