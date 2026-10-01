"""Busqueda de la E partiendo del puno, como la A y la S.

La A y la S del catalogo son `curl: 0.95` en los cuatro dedos y salen bien. La E
es el mismo puno pero SIN cerrar del todo: los dedos se detienen cuando las
yemas topan con el pulgar, que va tumbado por delante de la palma.

Intentar armarla a mano grado a grado, poniendo un `extra` por articulacion, no
funciono: el reparto prox/media/distal se descompensa enseguida y sale una garra
(ver `search_e11.py`). Con `curl` el reparto lo hace el rig (72/90/68 grados por
unidad) y solo hay que elegir cuanto se cierra y donde se pone el pulgar.
"""
import itertools
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

from pose_lab_e import ARM, T1, T2, T3
from search_e11 import MEASURE_JS
from search_e9 import abrir, banda

ROOT = Path(__file__).resolve().parents[1]
FINGERS = ["index", "middle", "ring", "pinky"]
FAN = (-1.5, -0.5, 0.5, 1.5)


def pose_e(
    curl, conv=0, tcurl=0.5, taside=-0.5,
    t1x=0, t1y=0, t1z=0, t2x=0, t3x=0, arm_z=-18,
):
    """E como puno abierto: `curl` cierra los cuatro dedos por igual y el
    pulgar se coloca con su curl mas retoques por hueso."""
    def four(v):
        return v if isinstance(v, (tuple, list)) else (v,) * 4

    curl = four(curl)
    t1 = {}
    for eje, v in (("x", t1x), ("y", t1y), ("z", t1z)):
        if v:
            t1[eje] = v
    extra = {ARM: {"z": arm_z}}
    if t1:
        extra[T1] = t1
    if t2x:
        extra[T2] = {"x": t2x}
    if t3x:
        extra[T3] = {"x": t3x}
    pose = {"thumb": {"curl": tcurl, "aside": taside}, "extra": extra}
    for i, f in enumerate(FINGERS):
        pose[f] = {"curl": curl[i], "spread": FAN[i] * conv}
    return pose


def score_dedos(m):
    p = 0.0
    # puno claramente cerrado: las yemas bien por debajo de los nudillos
    p += 6.0 * banda(m["baja"], 0.30, 0.62)
    # reparto natural del doblez, sin garra ni dedo recto
    p += 3.0 * banda(m["pip"], 70, 105)
    p += 3.0 * banda(m["dip"], 40, 80)
    # las yemas se quedan por delante de la palma, sobre el pulgar
    p += 3.0 * banda(m["yemaFrente"], 0.05, 0.45)
    # dedos separados, sin atravesarse
    p += 6.0 * banda(m["sep"], 0.17, 0.26)
    return p


def score_pulgar(m):
    p = 0.0
    # las yemas tocan el pulgar...
    p += 8.0 * banda(m["yemaThumb"], 0.03, 0.18)
    # ...y lo hacen apoyandose ENCIMA: el pulgar pasa por debajo de ellas.
    # Sin esto el pulgar cruza por delante de los dedos y sale una S.
    p += 8.0 * banda(m["pulgarBajoYemas"], 0.06, 0.32)
    p += 3.0 * banda(m["thumbLen"], 0.18, 0.46)
    p += 2.0 * banda(m["thumbFrente"], 0.08, 0.50)
    return p


def linea(nombre, m, score):
    return (
        f"{nombre:38s} sc={score:6.3f} pip={m['pip']:5.1f} dip={m['dip']:5.1f} "
        f"baja={m['baja']:.2f} frente={m['yemaFrente']:+.2f} sep={m['sep']:.3f} | "
        f"yema>pulgar={m['yemaThumb']:.2f} bajo={m['pulgarBajoYemas']:+.2f} "
        f"across={m['across']:+.2f} tLen={m['thumbLen']:.2f}"
    )


def main():
    cat = json.loads((ROOT / "data" / "catalogo-lsm.json").read_text("utf-8"))
    senas = {s["letra"]: s for s in cat["senas"]}

    with sync_playwright() as p:
        browser, page = abrir(p)

        def ev(pose):
            page.evaluate("(x) => window.__LSM_CONTROLLER__.applyTestPose(x)", pose)
            return page.evaluate(MEASURE_JS)

        for letra in ("E", "A", "S"):
            m = ev(senas[letra]["pose"])
            print(f"{letra:>2s}:", linea(letra, m, score_dedos(m) + score_pulgar(m)))
        print()

        # ---- Fase 1: cuanto se cierra el puno --------------------------------
        g1 = list(
            itertools.product(
                (0.60, 0.68, 0.76, 0.84, 0.92),   # curl
                (-8, -4, 0, 4),                   # conv
            )
        )
        print(f"Fase 1 (cierre): {len(g1)}")
        r1 = []
        for curl, conv in g1:
            mm = ev(pose_e(curl, conv, tcurl=0.5, taside=-0.5, t2x=50))
            r1.append((score_dedos(mm), (curl, conv), mm))
        r1.sort(key=lambda t: t[0])
        for sc, k, mm in r1[:10]:
            print(" ", linea(f"curl{k[0]} conv{k[1]}", mm, sc))
        print()

        # ---- Fase 2: pulgar tumbado bajo las yemas ---------------------------
        top = [k for _, k, _ in r1[:3]]
        g2 = list(
            itertools.product(
                (0.3, 0.45, 0.6, 0.75),    # tcurl
                (-0.9, -0.6, -0.3, 0.0),   # aside
                (-30, 0, 30),              # t1x
                (-50, -25, 0),             # t1y
                (0, 20, 40),               # t1z
                (0, 30, 60),               # t2x
                (0, 30, 60),               # t3x
            )
        )
        print(f"Fase 2 (pulgar): {len(g2)} x {len(top)}")
        r2 = []
        for curl, conv in top:
            for tcurl, aside, t1x, t1y, t1z, t2x, t3x in g2:
                mm = ev(
                    pose_e(curl, conv, tcurl, aside, t1x, t1y, t1z, t2x, t3x)
                )
                r2.append(
                    (
                        score_dedos(mm) + score_pulgar(mm),
                        ((curl, conv), (tcurl, aside, t1x, t1y, t1z, t2x, t3x)),
                        mm,
                    )
                )
        r2.sort(key=lambda t: t[0])
        print("MEJORES")
        for sc, k, mm in r2[:15]:
            d, t = k
            print(
                " ",
                linea(
                    f"c{d[0]} v{d[1]}|tc{t[0]} a{t[1]} x{t[2]} y{t[3]} z{t[4]} t2{t[5]} t3{t[6]}",
                    mm, sc,
                ),
            )
        browser.close()

    out = ROOT / "tools" / "screenshots" / "search_e13.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            [{"score": sc, "dedos": k[0], "pulgar": k[1], "m": mm} for sc, k, mm in r2[:40]],
            indent=2,
        ),
        "utf-8",
    )
    print("\n->", out)


if __name__ == "__main__":
    main()
