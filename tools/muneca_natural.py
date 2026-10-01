"""Endereza la muneca: el reposo del rig la dejaba doblada 90 grados.

El reposo apuntaba el antebrazo horizontal hacia adelante, asi que para que la
mano quedara vertical el hueso RightHand tenia que doblarse 90.5 grados (la
correccion x: -88). Una muneca real llega a unos 70, asi que la piel se plegaba
como una manguera en vez de verse como una muneca.

El arreglo sube el antebrazo (hombro 15 grados adelante y 12 afuera, antebrazo
25 arriba) y compensa en la muneca con la rotacion inversa exacta, de modo que
la ORIENTACION DE LA MANO no cambia en ninguna letra: lo unico que se mueve es
el brazo, que ahora sube hasta la altura del menton como el de una persona que
seña. Los valores se resolvieron sobre el modelo, no a ojo; el error medido de
orientacion es de 0.002 grados en el peor caso.

Tres grupos de letras:

- AUTOMATICO (B, D, F, I, J, K, L, U, V, W): no tocan brazo ni antebrazo, asi
  que heredan el reposo nuevo sin necesitar nada. La muneca pasa de 90.5 a 51.
- CONVERTIR (A, C, E, O, P, R, S, T): tenian un giro extra de brazo/antebrazo
  para orientar la mano. Ese giro se traduce a un extra equivalente en la
  muneca, que da la misma orientacion sin bajar el antebrazo.
- RESTAURAR (G, H, M, N, Ñ, Q, X, Y, Z): apuntan la mano hacia abajo o de lado,
  asi que con el antebrazo vertical la muneca quedaria PEOR. Estas conservan su
  brazo actual: se reexpresan sus valores (y los fotogramas de su movimiento)
  en el reposo nuevo para que queden identicas a como estaban. Les toca su
  propio angulo de brazo en una segunda pasada.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "data" / "catalogo-lsm.json"

VERSION = "1.4.0"

# Con la mano mas alta, el indice de la L se salia 3% por arriba del recuadro.
# Subir el sesgo 1.5 cm baja todo lo justo: ahora el punto mas alto (L) queda a
# 0.91 y el mas bajo (reposo) a -0.80, con -1..1 como borde.
SESGO_CAMARA = [0.12, -0.025, -0.02]

# Reposo nuevo: secuencia x -> y -> z sobre la T-pose del rig, por hueso.
REPOSO = {
    "RightArm": {"x": 77.898, "y": -0.776, "z": -14.98},
    "RightForeArm": {"x": -107.302, "y": 22.023, "z": -78.201},
    "RightHand": {"x": -49.935, "y": 9.674, "z": 11.432},
}

# Letras cuyo giro de brazo se traduce a un extra en la muneca.
CONVERTIR = {
    "A": {"x": -19.094, "y": 3.166, "z": -0.245},
    "C": {"x": -24.108, "y": -1.877, "z": -19.395},
    "E": {"x": -17.23, "y": -4.999, "z": -2.462},
    "O": {"x": -28.933, "y": -3.319, "z": -10.592},
    "P": {"x": 5.01, "y": -5.065, "z": -29.603},
    "R": {"x": -17.23, "y": -4.999, "z": -2.462},
    "S": {"x": -17.23, "y": -4.999, "z": -2.462},
    "T": {"x": -17.23, "y": -4.999, "z": -2.462},
}

# Letras que conservan su brazo actual, reexpresado en el reposo nuevo.
BRAZO = {"x": 11.511, "y": 3.841, "z": -3.489}
BRAZO_ABIERTO = {"x": 11.511, "y": 3.841, "z": 14.511}
ANTEBRAZO = {"x": 27.693, "y": 25.322, "z": -12.105}

RESTAURAR = {
    "G": {
        "brazo": BRAZO_ABIERTO,
        "antebrazo": ANTEBRAZO,
        "muneca": {"x": -39.092, "y": -0.428, "z": 75.072},
    },
    "H": {
        "brazo": BRAZO_ABIERTO,
        "antebrazo": ANTEBRAZO,
        "muneca": {"x": -39.092, "y": -0.428, "z": 75.072},
    },
    "M": {
        "brazo": BRAZO,
        "antebrazo": ANTEBRAZO,
        "muneca": {"x": 111.779, "y": -7.027, "z": 13.211},
    },
    "N": {
        "brazo": BRAZO,
        "antebrazo": ANTEBRAZO,
        "muneca": {"x": 111.779, "y": -7.027, "z": 13.211},
    },
    "Ñ": {
        "brazo": BRAZO,
        "antebrazo": ANTEBRAZO,
        "muneca": {"x": 109.047, "y": 4.659, "z": 13.154},
        "fotogramas": [
            {"brazo": {"x": 5.562, "y": 25.084, "z": -1.976}},
            {"brazo": {"x": 8.946, "y": 13.515, "z": -3.101}},
            {"brazo": {"x": 12.012, "y": 1.905, "z": -3.514}},
        ],
    },
    "Q": {
        "brazo": BRAZO,
        "antebrazo": ANTEBRAZO,
        "muneca": {"x": 96.946, "y": -10.187, "z": 55.978},
        "fotogramas": [
            {
                "brazo": {"x": 11.618, "y": 3.869, "z": -3.496},
                "antebrazo": {"x": 18.959, "y": 27.001, "z": -12.027},
            },
            {
                "brazo": {"x": 16.555, "y": 5.125, "z": -3.884},
                "antebrazo": {"x": 19.048, "y": 26.984, "z": -12.029},
            },
            {
                "brazo": {"x": 20.163, "y": 6.017, "z": -4.234},
                "antebrazo": {"x": 21.476, "y": 26.521, "z": -12.078},
            },
            {
                "brazo": {"x": 21.443, "y": 6.327, "z": -4.372},
                "antebrazo": {"x": 25.556, "y": 25.735, "z": -12.112},
            },
            {
                "brazo": {"x": 20.046, "y": 5.988, "z": -4.222},
                "antebrazo": {"x": 30.174, "y": 24.84, "z": -12.076},
            },
            {
                "brazo": {"x": 16.37, "y": 5.079, "z": -3.867},
                "antebrazo": {"x": 34.112, "y": 24.076, "z": -11.981},
            },
            {
                "brazo": {"x": 11.404, "y": 3.813, "z": -3.482},
                "antebrazo": {"x": 36.309, "y": 23.651, "z": -11.904},
            },
            {
                "brazo": {"x": 6.482, "y": 2.527, "z": -3.21},
                "antebrazo": {"x": 36.222, "y": 23.668, "z": -11.907},
            },
            {
                "brazo": {"x": 2.903, "y": 1.579, "z": -3.081},
                "antebrazo": {"x": 33.85, "y": 24.127, "z": -11.989},
            },
            {
                "brazo": {"x": 1.637, "y": 1.241, "z": -3.05},
                "antebrazo": {"x": 29.823, "y": 24.908, "z": -12.081},
            },
            {
                "brazo": {"x": 3.019, "y": 1.609, "z": -3.085},
                "antebrazo": {"x": 25.202, "y": 25.804, "z": -12.112},
            },
            {
                "brazo": {"x": 6.666, "y": 2.576, "z": -3.218},
                "antebrazo": {"x": 21.209, "y": 26.572, "z": -12.074},
            },
            {
                "brazo": {"x": 11.618, "y": 3.869, "z": -3.496},
                "antebrazo": {"x": 18.959, "y": 27.001, "z": -12.027},
            },
        ],
    },
    "X": {
        "brazo": BRAZO,
        "antebrazo": ANTEBRAZO,
        "muneca": {"x": -16.818, "y": 6.191, "z": -103.94},
        "fotogramas": [
            {"antebrazo": {"x": 27.693, "y": 25.322, "z": -12.105}},
            {"antebrazo": {"x": 39.338, "y": 23.068, "z": -23.768}},
        ],
    },
    "Y": {
        "brazo": BRAZO,
        "antebrazo": {"x": 35.231, "y": 22.735, "z": -5.838},
        "muneca": {"x": -33.291, "y": -1.969, "z": 37.193},
    },
    "Z": {
        "brazo": BRAZO,
        "antebrazo": {"x": 1.329, "y": 4.569, "z": 2.914},
        "muneca": {"x": -39.092, "y": -0.428, "z": -14.928},
        "fotogramas": [
            {"antebrazo": {"x": 1.329, "y": 4.569, "z": 2.914}},
            {"antebrazo": {"x": 5.475, "y": 3.831, "z": -24.26}},
            {"antebrazo": {"x": 39.644, "y": -2.661, "z": 3.38}},
            {"antebrazo": {"x": 43.779, "y": -3.428, "z": -23.27}},
        ],
    },
}

HUESO = {"brazo": "RightArm", "antebrazo": "RightForeArm"}


def rotaciones(valores):
    return [[eje, valores[eje]] for eje in ("x", "y", "z")]


def main():
    data = json.loads(CATALOGO.read_text(encoding="utf-8"))

    data["rig"]["cameraBias"] = list(SESGO_CAMARA)
    print(f"sesgo de camara: {SESGO_CAMARA}")

    for correccion in data["rig"]["restCorrections"]:
        nuevo = REPOSO.get(correccion["hueso"])
        if nuevo:
            correccion["rotaciones"] = rotaciones(nuevo)
            print(f"reposo {correccion['hueso']}: {nuevo}")

    for sena in data["senas"]:
        letra = sena["letra"]
        pose = sena.get("pose")
        if not pose:
            continue

        if letra in CONVERTIR:
            extra = pose.setdefault("extra", {})
            extra.pop("RightArm", None)
            extra.pop("RightForeArm", None)
            extra["RightHand"] = dict(CONVERTIR[letra])
            print(f"{letra}: giro de brazo -> muneca {CONVERTIR[letra]}")
            continue

        if letra in RESTAURAR:
            ajuste = RESTAURAR[letra]
            extra = pose.setdefault("extra", {})
            extra["RightArm"] = dict(ajuste["brazo"])
            extra["RightForeArm"] = dict(ajuste["antebrazo"])
            extra.pop("RightHand", None)
            pose["muneca"] = dict(ajuste["muneca"])

            fotogramas = ajuste.get("fotogramas") or []
            claves = (sena.get("ciclo") or {}).get("keyframes") or []
            if len(fotogramas) != len(claves):
                raise SystemExit(
                    f"{letra}: {len(fotogramas)} fotogramas calculados para "
                    f"{len(claves)} del catalogo"
                )
            for valores, clave in zip(fotogramas, claves):
                extra_clave = clave.setdefault("extra", {})
                extra_clave.pop("RightHand", None)
                # Cada fotograma declara los tres ejes de brazo y antebrazo: el
                # controlador mezcla eje por eje, asi que un valor viejo suelto
                # sobrescribiria el de la pose base.
                for nombre, hueso in HUESO.items():
                    extra_clave[hueso] = dict(valores.get(nombre, ajuste[nombre]))
                clave["muneca"] = dict(ajuste["muneca"])
            print(f"{letra}: brazo actual reexpresado ({len(claves)} fotogramas)")

    data["version"] = VERSION
    CATALOGO.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"OK: {CATALOGO.name} v{VERSION}")


if __name__ == "__main__":
    main()
