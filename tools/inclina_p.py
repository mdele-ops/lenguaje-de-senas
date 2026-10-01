"""P: inclina la mano hacia adelante (la muñeca la dejaba doblada hacia atras).

Mide la direccion del antebrazo y de la mano en 3D (el avatar mira a +z, la
camara de practica esta en +z) y busca el giro de RightHand que sube la
componente z del eje de la mano (muñeca->nudillo del medio) sin romper la
lectura de la letra: medio horizontal, indice en diagonal, palma de canto.

Uso: python _run.py inclina_p.py [z_objetivo]
"""
import copy, itertools, json, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import search_e9 as se9
from search_e9 import abrir

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tools" / "screenshots" / "inclina_p"
OUT.mkdir(parents=True, exist_ok=True)
se9.URL = "http://127.0.0.1:8123/practica.html?letra=%E2%97%8B&v=incl"
CAT = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
SENAS = CAT["senas"] if isinstance(CAT, dict) else CAT

JS = """
() => {
  const mv = document.getElementById('handViewer');
  function getScene(mv){ if (mv.model&&mv.model.traverse) return mv.model; if (mv.model&&mv.model.scene) return mv.model.scene;
    for (const s of Object.getOwnPropertySymbols(mv)){const v=mv[s]; if(v&&v.traverse) return v; if(v&&v.model&&v.model.traverse) return v.model;} return null;}
  const sc = getScene(mv); sc.updateMatrixWorld(true);
  const B = {}; sc.traverse(o=>{ if(o.name) B[o.name.replace(/^mixamorig\\d*/,'').replace(/_\\d+$/,'')] = o; });
  const P = n => { const e=B[n].matrixWorld.elements; return {x:e[12],y:e[13],z:e[14]}; };
  const sub=(a,b)=>({x:a.x-b.x,y:a.y-b.y,z:a.z-b.z});
  const nrm=v=>{const l=Math.hypot(v.x,v.y,v.z)||1;return {x:v.x/l,y:v.y/l,z:v.z/l};};
  const cross=(a,b)=>({x:a.y*b.z-a.z*b.y,y:a.z*b.x-a.x*b.z,z:a.x*b.y-a.y*b.x});
  const d=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z);
  const ang=(a,b)=>Math.atan2(b.y-a.y,b.x-a.x)*180/Math.PI;
  const w=P('RightHand'), fo=P('RightForeArm'), i1=P('RightHandIndex1'), i4=P('RightHandIndex4'),
        m1=P('RightHandMiddle1'), m4=P('RightHandMiddle4'), p1=P('RightHandPinky1');
  const palm=d(w,i1)||1;
  const n=nrm(cross(sub(p1,i1),sub(m1,w)));
  const hand=nrm(sub(m1,w)), fore=nrm(sub(w,fo));
  return { handZ:hand.z, foreZ:fore.z, idxAng:ang(i1,i4), midAng:ang(m1,m4), palmNz:n.z,
    idxScr:Math.hypot(i4.x-i1.x,i4.y-i1.y)/palm, midScr:Math.hypot(m4.x-m1.x,m4.y-m1.y)/palm,
    hand:[hand.x,hand.y,hand.z] };
}
"""

def pose_cat():
    for s in SENAS:
        if s.get("letra") == "P":
            return copy.deepcopy(s["pose"])

def con(base, x, y, z, my=None):
    p = copy.deepcopy(base)
    p["extra"]["RightHand"] = {"x": x, "y": y, "z": z}
    if my is not None:
        p["muneca"] = {"y": my}
    return p

def main():
    zt = float(sys.argv[1]) if len(sys.argv) > 1 else -0.25
    base = pose_cat()
    with sync_playwright() as p:
        for intento in range(6):
            browser, page = abrir(p)
            time.sleep(1.0)
            page.evaluate("(x)=>window.__LSM_CONTROLLER__.applyTestPose(x)", base)
            time.sleep(0.5)
            if abs(page.evaluate(JS)["foreZ"] - 0.54) < 0.05:
                break
            print("reposo distinto, reintento", intento, flush=True)
            browser.close()
        ap = lambda pose: page.evaluate("(x)=>window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
        ap(base); m0 = page.evaluate(JS)
        if abs(m0["foreZ"] - 0.54) > 0.05:
            raise SystemExit("esqueleto de reposo distinto al esperado (foreZ=%.2f): repetir" % m0["foreZ"])
        print("ACTUAL", {k: (round(v, 2) if isinstance(v, float) else v) for k, v in m0.items()})
        res = []
        for x, y, z in itertools.product(range(-30, 51, 10), range(-40, 31, 10), range(-40, 21, 10)):
            ap(con(base, x, y, z)); m = page.evaluate(JS)
            # de la P actual solo se quiere cambiar la inclinacion hacia delante
            s = (80 * abs(m["handZ"] - zt) + 1.0 * abs(m["midAng"] - m0["midAng"])
                 + 0.6 * abs(m["idxAng"] - m0["idxAng"]) + 40 * max(0, abs(m["palmNz"]) - 0.25)
                 + 30 * max(0, 0.85 - m["midScr"]) + 30 * max(0, 0.7 - m["idxScr"]))
            res.append((s, (x, y, z), m))
        res.sort(key=lambda t: t[0])
        for s, k, m in res[:8]:
            print(k, round(s, 1), {a: round(m[a], 2) for a in ("handZ", "idxAng", "midAng", "palmNz", "idxScr", "midScr")})
        (OUT / "mejor.json").write_text(json.dumps(res[0][1]), "utf-8")
        browser.close()

if __name__ == "__main__":
    main()



