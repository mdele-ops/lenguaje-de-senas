# Glosario de poses LSM (`catalogo-lsm.json`)

Referencia de los campos que definen cada seña del alfabeto y cómo los valores numéricos afectan al modelo `model.glb` (mano derecha del esqueleto Mixamo).

El controlador (`js/hand-controller.js`) toma la pose en reposo (bind) y aplica rotaciones locales sobre los huesos del esqueleto.

---

## 1. Campos de cada seña (`senas[]`)

| Campo | Tipo | Qué hace |
|---|---|---|
| `letra` | string | Identificador mostrado en la UI (ej. `"A"`, `"Ñ"`, `"○"` para Neutral). |
| `nombre` | string | Nombre legible de la seña. |
| `descripcion` | string | Texto explicativo bajo la letra en la práctica. |
| `animacion` | string \| null | Nombre preferido de un clip dentro del `.glb`. Si existe un clip dedicado, se usa en lugar de la pose. |
| `aliases` | string[] | Nombres alternativos para emparejar clips (ej. `"letra_a"`, `"LSM_A"`). |
| `pose` | object \| null | Parámetros de flexión por dedo. `null` = mano sin modificar (Neutral). |
| `ciclo` | object | Opcional. Movimiento de la seña (letras que no son estáticas, como la **J**). Ver §10. |
| `neutral` | boolean | Si es `true`, restaura la pose original del modelo. |

---

## 2. Parámetros por dedo (`pose.thumb` / `index` / `middle` / `ring` / `pinky`)

Cada dedo admite estos campos:

### `curl` — cierre / flexión del dedo

| | |
|---|---|
| **Rango** | `0.0` … `1.0` (se recorta si sale del rango) |
| **Unidad** | Fracción del máximo definido en `rig.curlMaxGrados` (o `thumbCurlMaxGrados` para el pulgar) |
| **Eje** | El de `rig.ejeCurl` (por defecto `"z"`), con signo `rig.curlSign` |

**Qué hace el número**

- `0.0` → dedo extendido (rest pose).
- `0.5` → flexión a la mitad del máximo.
- `1.0` → flexión máxima (puño / dedo cerrado).

**Fórmula (dedos índice–meñique)**

```
grados = curl × curlMaxGrados[articulación]
```

Articulaciones afectadas (no se rota el primer hueso de la cadena, `*Index1`/`*Middle1`/etc., que actúa como metacarpiano):

Cada dedo en `rig.huesos` es un arreglo de 4 huesos. La **posición** dentro del arreglo, interpretada según `rig.jointOrder.dedo`, define su articulación:

| Posición | Rol (rig Mixamo actual) | Clave en `curlMaxGrados` | Valor actual |
|---|---|---|---|
| índice 0 | falange proximal (nudillo principal) | `prox` | 72° |
| índice 1 | falange media | `midd` | 90° |
| índice 2 | falange distal | `dist` | 68° |
| índice 3 | punta del dedo (sin curl) | — | — |

Ejemplo actual (huesos de `model.glb`, mano derecha Mixamo):

```json
"index": [
  "mixamorig1RightHandIndex1_040",
  "mixamorig1RightHandIndex2_041",
  "mixamorig1RightHandIndex3_042",
  "mixamorig1RightHandIndex4_043"
]
```

Ejemplo: `"index": { "curl": 1.0 }` rota el índice hasta **72° + 90° + 68°** repartidos en sus tres falanges (máximo de cierre).

**Pulgar** usa `thumbCurlMaxGrados`, también por posición en el arreglo `rig.huesos.thumb` (el rig Mixamo solo tiene 3 huesos que realmente rotan, por eso `meta`+`prox` se combinan en el hueso central):

| Posición | Rol (rig Mixamo actual) | Claves sumadas | Valor actual |
|---|---|---|---|
| índice 0 | base/trapecio (CMC) | `trapez` | 24° |
| índice 1 | nudillo (MCP) | `meta` + `prox` | 34° + 48° = 82° |
| índice 2 | falange distal (IP) | `dist` | 42° |
| índice 3 | punta del pulgar (sin curl) | — | — |

---

### `aside` — apertura lateral del pulgar

| | |
|---|---|
| **Rango recomendado** | `0.0` … `1.0` |
| **Aplica a** | Solo `thumb`, primer hueso de la cadena (posición 0, "trapecio") |
| **Eje** | `y` (rotación local) |

**Qué hace el número**

```
grados = aside × 32
```

- `0.0` → pulgar sin apertura extra.
- `0.45` → ~14.4° hacia afuera (útil en la letra **A**).
- `1.0` → 32° de apertura máxima típica.

Sirve para separar el pulgar del puño (A, L, Y) sin cerrarlo con `curl`.

---

### `spread` — separación / aducción del dedo

| | |
|---|---|
| **Rango recomendado** | aprox. `-15` … `15` |
| **Unidad** | Grados |
| **Aplica a** | Hueso en posición "prox" del dedo (posición 1 en dedos, posición 2 en pulgar) |
| **Eje** | `x` (rotación local) |

**Qué hace el número**

- Valor **positivo** → empuja el dedo en un sentido (p. ej. índice hacia afuera).
- Valor **negativo** → sentido contrario (p. ej. meñique hacia adentro).
- `0` → sin separación extra.

Ejemplo letra **B**: `"index": { "spread": 4 }` y `"pinky": { "spread": -4 }` acercan los dedos entre sí.

---

### `twist` — torsión del dedo

| | |
|---|---|
| **Rango recomendado** | aprox. `-20` … `20` |
| **Unidad** | Grados |
| **Aplica a** | Hueso en posición "prox" del dedo |
| **Eje** | `y` |

**Qué hace el número**

- Positivo / negativo cruzan o tuercen el dedo (útil en la **R**, índice y medio cruzados).
- `0` o ausente → sin torsión.

Ejemplo: `"index": { "twist": 10 }`, `"middle": { "twist": -10 }`.

---

## 3. Muñeca (`pose.muneca`)

| Campo | Unidad | Eje | Efecto |
|---|---|---|---|
| `x` | grados | local X | Inclina la mano arriba/abajo |
| `y` | grados | local Y | Gira la mano (p. ej. perfil en la **C**) |
| `z` | grados | local Z | Rota en el plano de la palma |

Ejemplo letra **C**: `"muneca": { "y": 90 }` deja la palma de lado (perpendicular a la cámara), que es lo que hace legible el arco de la C. Con giros intermedios (p. ej. `y: 50`) la palma queda a medias hacia el frente y el arco se ve de canto: la mano parece una pinza.

Los valores se suman a la rotación en reposo del hueso definido en `rig.wristBone` (en `model.glb`: `mixamorig1RightHand_035`; en el modelo anterior era `radius_ulna`).

---

## 4. Ajustes globales del rig (`rig`)

Estos no van por letra; definen cómo se interpretan todos los `curl` / ejes.

| Campo | Tipo | Efecto |
|---|---|---|
| `ejeCurl` | `"x"` \| `"y"` \| `"z"` | Eje local de flexión de los dedos. Actual: `"x"`. |
| `curlSign` | `1` o `-1` | Invierte el sentido del cierre. Si los dedos se abren al subir `curl`, prueba `-1`. |
| `transitionMs` | number | Duración de la transición entre poses (se limita a 1000–3000 ms). Actual: `2000`. |
| `curlMaxGrados` | object | Grados máximos por articulación al `curl: 1.0` (dedos). |
| `thumbCurlMaxGrados` | object | Igual para el pulgar. |
| `huesos` | object | Cadena de 4 nombres de huesos por dedo, en orden desde la base hasta la punta (debe coincidir con los nodos reales del `.glb` cargado; el controlador identifica la articulación por posición en el arreglo, no por el texto del nombre). |
| `wristBone` | string | Nombre del hueso que representa la muñeca/mano (recibe la rotación de `pose.muneca`). Por defecto `"radius_ulna"` si no se define. |
| `jointOrder` | object | Define qué representa cada POSICIÓN dentro de `huesos.thumb` / `huesos.<dedo>`. Cada entrada puede ser una clave (`"prox"`), varias combinadas (`["meta","prox"]`, se suman sus grados) o `null` (ese hueso no rota, p.ej. la punta en rigs Mixamo). Necesario porque distintos rigs ordenan sus huesos de forma diferente (el rig original tenía el metacarpiano fijo al INICIO de la cadena; el rig Mixamo de `model.glb` tiene la punta fija al FINAL). |
| `restCorrections` | array | Rotaciones que se aplican **una sola vez**, al cargar el modelo, ANTES de capturar la pose de reposo (`restPose`). Sirven para corregir modelos que vienen en T-pose (brazos en cruz) y no tienen una postura natural de fábrica: doblan hombro/codo/muñeca para que la mano quede al frente, con la palma hacia la cámara y los dedos hacia arriba, lista para "leer" las señas. Cada entrada es `{ "hueso": "<nombre>", "rotaciones": [["x"\|"y"\|"z", grados], ...] }`, aplicadas en orden con `bone.rotateX/Y/Z()` (rotación local, no absoluta). |

`model.glb` es un personaje Mixamo exportado en T-pose (a diferencia del modelo anterior, que ya traía el brazo en una postura natural). El `restCorrections` actual dobla brazo derecho, antebrazo y muñeca para simular una postura de "mano levantada, lista para señar", y hace lo mismo (en espejo) en el brazo izquierdo solo por estética visual:

```json
"restCorrections": [
  { "hueso": "mixamorig1RightArm_033",     "rotaciones": [["x", 90]] },
  { "hueso": "mixamorig1RightForeArm_034", "rotaciones": [["z", -90], ["y", -77]] },
  { "hueso": "mixamorig1RightHand_035",    "rotaciones": [["x", -88]] },
  { "hueso": "mixamorig1LeftArm_09",       "rotaciones": [["x", 90]] }
]
```

Si en el futuro se vuelve a cambiar de modelo y este ya trae una pose de reposo natural (brazo doblado, mano al frente), lo normal es dejar `restCorrections` vacío (`[]`).

---

## 5. Cómo combinar valores (guía rápida)

| Objetivo visual | Qué tocar |
|---|---|
| Puño cerrado (A, S) | `curl: 1.0` en index–pinky; pulgar con poco `curl` y algo de `aside` |
| Palma abierta (B) | `curl: 0` en dedos; `thumb.curl` alto (~0.9) para doblarlo sobre la palma |
| Forma de C | `muneca.y: 90` + `curl` bajo (~0.26) y el arco repartido vía `extra` en las tres falanges (nudillo ~20°, media ~34°, distal ~12°); el `curl` alto solo cierra las puntas y se convierte en O |
| Forma de E | `curl: 0.92` en los cuatro dedos (el puño lo hace el `curl`) + un retoque por falange vía `extra` para que los cuatro doblen los mismos grados + pulgar horizontal bajo las yemas, girado desde `Thumb1`; ver §8 |
| Un dedo arriba (D, I, L…) | Ese dedo en `curl: 0`; el resto en `curl` alto |
| Dedos separados (V, W) | `spread` opuesto en los dedos extendidos |
| Dedos cruzados (R) | `twist` opuesto en índice y medio |

---

## 6. Ejemplo completo (letra A)

```json
"pose": {
  "thumb":  { "curl": 0.15, "aside": 0.45 },
  "index":  { "curl": 1.0 },
  "middle": { "curl": 1.0 },
  "ring":   { "curl": 1.0 },
  "pinky":  { "curl": 1.0 }
}
```

Interpretación:

1. Índice–meñique al 100 % del máximo → puño.
2. Pulgar solo 15 % cerrado + `aside` 0.45 → queda al costado del índice, no encima del puño.

---

## 7. Ejemplo completo (letra C)

La C es la pose más delicada del alfabeto porque su forma solo existe si el arco
queda **de canto frente a la cámara**. Por eso lleva `muneca.y: 90` y el arco no se
consigue subiendo `curl`, sino repartiéndolo en las tres falanges con `extra`:

```json
"pose": {
  "thumb":  { "curl": 0.5, "aside": 0.8 },
  "index":  { "curl": 0.26, "spread": 4 },
  "middle": { "curl": 0.26, "spread": 1 },
  "ring":   { "curl": 0.26, "spread": -1 },
  "pinky":  { "curl": 0.26, "spread": -4 },
  "muneca": { "y": 90 },
  "extra": {
    "mixamorig1RightHandIndex1_040":  { "x": 20 },
    "mixamorig1RightHandIndex2_041":  { "x": 34 },
    "mixamorig1RightHandIndex3_042":  { "x": 12 },
    "mixamorig1RightHandThumb1_036":  { "x": -30, "y": 34, "z": 25 },
    "mixamorig1RightHandThumb2_037":  { "x": -30 },
    "mixamorig1RightArm_033":         { "z": -18 }
  }
}
```

(los tres huesos del índice se repiten igual en medio, anular y meñique)

Interpretación:

1. `muneca.y: 90` pone la palma hacia el costado. Es el valor crítico: con `y: 50`
   la palma queda a medias hacia el frente y la mano se lee como una pinza.
2. El arco de los cuatro dedos se reparte nudillo 20° → falange media 34° →
   distal 12°, más el `curl` 0.26 común. Subir `curl` en lugar de repartir cierra
   las puntas y la C se convierte en O.
3. `spread` de +4 a −4 acerca los cuatro dedos para que el arco se lea como una
   sola banda.
4. El pulgar con `curl` 0.5 y `aside` 0.8 se opone por debajo y cierra el arco
   dejando el hueco visible. Lo que lo levanta no es el `curl` sino el `extra`
   del trapecio: `z: 25` sube la punta y `x: -30` la orienta hacia los dedos;
   el `x: -30` de Thumb2 evita que el pulgar se doble de más al subirlo. Sin
   estas tres rotaciones el pulgar sale recto hacia el costado, por debajo de
   la palma, en una postura que la mano real no alcanza.
5. `mixamorig1RightArm_033` con `z: -18` separa la mano del pecho para que el
   hueco no se pierda contra el chaleco.

Para revisar cambios en esta letra: `py tools/verify_c.py` (fotografía la C por el
camino de producción y la pone junto a la foto de referencia).

---

## 8. Ejemplo completo (letra E)

La E es el mismo puño que la A y la S, cerrado casi por completo, y lo único que
la distingue es dónde queda el pulgar:

- **A** → pulgar estirado al costado del puño.
- **S** → pulgar largo, cruzado por delante de los dedos.
- **E** → pulgar **tumbado cruzando la palma**, con la uña al frente y la yema
  asomando junto a la del índice; las cuatro yemas se apoyan encima.

```json
"pose": {
  "thumb":  { "curl": 0.4 },
  "index":  { "curl": 0.78, "spread": -18 },
  "middle": { "curl": 0.98, "spread": -6 },
  "ring":   { "curl": 0.96, "spread": 6 },
  "pinky":  { "curl": 0.98, "spread": 18 },
  "nudillos": 0.54,
  "largo":  { "pinky": 1.02, "ring": 1.04 },
  "extra": {
    "RightHandThumb1":  { "x": -7, "y": -65, "z": 46 },
    "RightHandThumb2":  { "x": 40, "z": 22 },
    "RightHandThumb3":  { "x": 55, "y": -44, "z": -22 },
    "RightHandIndex1":  { "x": 14 },
    "RightHandIndex2":  { "x": 14 },
    "RightHandIndex3":  { "x": 6 },
    "RightHandMiddle1": { "x": 14 },
    "RightHandMiddle2": { "x": 14 },
    "RightHandMiddle3": { "x": 6 },
    "RightHandRing1":   { "x": 14 },
    "RightHandRing2":   { "x": 14 },
    "RightHandRing3":   { "x": 6 },
    "RightHandPinky1":  { "x": 14 },
    "RightHandPinky2":  { "x": 14 },
    "RightHandPinky3":  { "x": 6 },
    "RightHand":        { "x": -17.23, "y": -4.999, "z": -2.462 }
  }
}
```

Interpretación:

1. El grueso del doblez lo hace **`curl`**, no `extra`. Los cuatro dedos van
   entre 0.78 y 0.98 y los `extra` son los mismos para todos (14° / 14° / 6°):
   ya no hay un retoque distinto por dedo. La fila de yemas se nivela con las
   dos herramientas que no tocan ángulos —el `curl` de cada dedo y `largo`—, y
   eso deja el `extra` libre para lo que de verdad necesita retoque.
2. El índice dobla **menos** que los otros tres (0.78 frente a 0.96–0.98) a
   propósito: es el que tiene que dejar sitio a la yema del pulgar. Con los
   cuatro al mismo `curl`, el índice se le echa encima y el pulgar desaparece.
3. **`nudillos: 0.54`** es lo que junta los dedos. Aprieta las raíces de los
   nudillos hacia el del medio y el frente índice→meñique pasa de 0.61 a 0.28
   de palma; con eso las yemas quedan a 0.10–0.12 unas de otras, tocándose como
   en la foto, sin necesidad de forzar el `spread`. **Cuidado al comparar
   medidas de `ancho` entre letras**: la métrica se divide por ese mismo frente
   índice→meñique, así que en cuanto hay `nudillos` los valores de `ancho` se
   inflan y no son comparables con una letra que no lo lleva.
4. **`largo`** sube 2% el meñique y 4% el anular. Son los dos dedos cortos del
   rig y, con el mismo doblez que los demás, sus yemas se quedaban atrás; el
   alargue los pone en la misma fila (yemas a 0.68–0.73 de palma, dentro de
   0.05 unas de otras) sin cambiar ningún ángulo.
5. El pulgar se **orienta** con `Thumb1` y se **acomoda** con `Thumb2`/`Thumb3`.
   `Thumb1 { y: -65, z: 46 }` lo tumba cruzando la palma y le gira la uña al
   frente; `Thumb2 { x: 40, z: 22 }` y `Thumb3 { x: 55, y: -44, z: -22 }` sacan
   la yema hacia afuera, junto al índice, en vez de dejarla enterrada bajo los
   dedos. Aquí los tres ejes hacen falta: con solo `x` el pulgar se dobla sobre
   sí mismo hacia la muñeca. Ojo con el detalle de implementación: los `extra`
   del pulgar **no** se recortan con `flexMaxGrados` (solo los de los otros
   cuatro dedos), así que un valor exagerado sí rompe la malla y hay que
   comprobar el resultado a ojo.
6. `RightHand { x: -17.23, y: -4.999, z: -2.462 }` gira la mano para que la
   palma mire al frente, que es la vista de la lámina.

El defecto de la versión anterior no era el doblez de los dedos sino que **el
pulgar no se veía**: quedaba a la altura de los nudillos y **detrás** de la
palma (punta en `alto 1.01`, `frente −0.15`), o sea escondido por el puño. Al
mismo tiempo las yemas caían escalonadas (0.78 → 0.64) y separadas (huecos de
0.15–0.22), así que el puño no leía como puño cerrado.

Medidas en el marco de la palma (origen en la muñeca, `alto` hacia el nudillo
del medio, `ancho` hacia el lado del pulgar, `frente` hacia la cámara, todo
dividido por el largo de la palma):

| Métrica | Qué mide | Antes | Ahora |
|---|---|---|---|
| `yemasAlto` | altura de las cuatro yemas | 0.78 / 0.70 / 0.67 / 0.64 (escalonadas) | 0.73 / 0.69 / 0.68 / 0.72 (a nivel) |
| `gaps` | separación entre yemas vecinas | 0.20 / 0.22 / 0.15 | 0.11 / 0.12 / 0.10 |
| `tocaDedos` | distancia de la yema más cercana al pulgar | 0.20 | 0.10 |
| punta del pulgar | `alto` / `ancho` / `frente` | 1.01 / 0.17 / **−0.15** (detrás) | 0.66 / 0.24 / **0.28** (al frente) |
| `mpAng` / `ipAng` | doblez del pulgar en el nudillo y en la última falange | 71° / 12° | 75° / 86° |

Formas de equivocarse que ya se probaron y **no** funcionan:

- Repartir todo el doblez a mano con `extra` y `curl: 0` (nudillo 85° → media
  100° → distal 20°) saca el dedo entero por delante de la palma con la yema
  recta: queda una garra. El `extra` sirve para retocar, no para sustituir al
  `curl`.
- Nivelar la fila de yemas con un `extra` distinto por dedo. Se puede, pero
  cada valor depende del reposo horneado del `.glb` y hay que recalcular los
  doce en cuanto se toca el `curl`. Sale más limpio con `curl` + `largo`.
- Pedirle al pulgar la posición **exacta** de la foto. El pulgar de este rig
  mide **1.007 de palma** —y su falange distal sola, 0.38, es desproporcionada—
  así que no puede estar a la vez bajo (`alto 0.46`) y tumbado al frente
  (`frente 0.30`) sin salirse de los topes de las articulaciones: se llega a uno
  o al otro. El acuerdo es `alto 0.66` con `frente 0.28`, que en pantalla lee
  como la lámina aunque el número no coincida.
- Buscar la pose del pulgar a base de **tiros al azar**. Son diez grados de
  libertad y el azar se va siempre a los extremos: pulgar doblado 141° en el
  nudillo, o por debajo de la muñeca, o clavado 0.87 de palma hacia la cámara.
  Hay que ir con búsqueda por patrones desde varias semillas y con objetivos de
  dos lados (mínimo *y* máximo) más penalizaciones anatómicas sobre `mpAng`,
  `ipAng` y el `frente` de las falanges.
- Puntuar el pulgar solo por su **punta**. La punta acaba donde toca, pero el
  resto del dedo se despega de la palma y aparece el cuerno. Hay que medir las
  tres articulaciones contra el marco de la palma.
- Cerrar los cuatro dedos **de más** buscando un puño más compacto. Con
  `nudillos 0.57` y los cuatro `curl` altos el puño queda perfecto… y tapa el
  pulgar otra vez, que es justo lo que distingue la E.
- Fiarse de la **foto del usuario** para la orientación: está tomada desde abajo
  y ahí el pulgar se ve escorzado.
- Medir alturas en la **Y del mundo**. La E lleva `extra` en la muñeca, que gira
  la mano entera, así que esos números no se pueden comparar con letras que no
  lo llevan. Todo se mide en el marco de la palma.
- Juzgar la vista sin comprobar la **cámara**. `practica.html` limita la órbita
  (`min-camera-orbit="auto 55deg 0.45m"`), así que una captura puede enseñar la
  mano desde arriba y hacer parecer que los dedos están casi rectos. Conviene
  confirmar el punto de vista proyectando los huesos sobre la captura antes de
  sacar conclusiones.

Para revisar cambios en esta letra: `py tools/verifica_e15.py` (aplica la E por
el camino real de la app —`mostrarSena`, no `applyTestPose`— comprueba que la
pose del catálogo llega a la página y la pone al lado de A, S, T, O y C para ver
que siguen distinguiéndose).

Si en la máquina no hay Python ni Node, todo ese banco de pruebas queda
inservible y se puede trabajar igual desde el navegador:
`powershell -ExecutionPolicy Bypass -File tools\servidor.ps1 -Port 8124` levanta
el sitio (el `.glb` no se puede cargar por `file://`) y la pose se mide y se
ajusta con `Runtime.evaluate` sobre `window.__LSM_CONTROLLER__`. Para comparar
muchos candidatos de una vez, `mv.toDataURL('image/png')` permite montar una
hoja de contactos dentro de la propia página y sacarla en una sola captura.

---

## 9. Ejemplo completo (letra O)

La O es la C **cerrada**: el mismo arco de cuatro dedos, pero el pulgar sube a
buscar las yemas hasta que se tocan y el hueco pasa de abierto a agujero.

```json
"pose": {
  "thumb":  { "curl": 0.35, "aside": -0.5 },
  "index":  { "curl": 0.625, "spread": 4 },
  "middle": { "curl": 0.625, "spread": 1.3 },
  "ring":   { "curl": 0.625, "spread": -1.3 },
  "pinky":  { "curl": 0.625, "spread": -4 },
  "muneca": { "y": 70 },
  "extra": {
    "mixamorig1RightHandThumb1_036": { "x": -15, "y": 10, "z": 15 },
    "mixamorig1RightHandThumb2_037": { "x": 25 },
    "mixamorig1RightHandThumb3_038": { "x": 35 },
    "mixamorig1RightHandIndex1_040": { "x": 14.1 },
    "mixamorig1RightHandIndex2_041": { "x": 2 },
    "mixamorig1RightHandIndex3_042": { "x": -16.2 },
    "mixamorig1RightHandMiddle1_044": { "x": 12 },
    "mixamorig1RightHandMiddle2_045": { "x": 2 },
    "mixamorig1RightHandMiddle3_046": { "x": -6 },
    "mixamorig1RightHandRing1_048":  { "x": 7.1 },
    "mixamorig1RightHandRing2_049":  { "x": 6.6 },
    "mixamorig1RightHandRing3_050":  { "x": 10.9 },
    "mixamorig1RightHandPinky1_052": { "x": 14.6 },
    "mixamorig1RightHandPinky2_053": { "x": -3.9 },
    "mixamorig1RightHandPinky3_054": { "x": -13.5 },
    "mixamorig1RightArm_033":        { "z": -18 }
  }
}
```

Interpretación:

1. Lo único que separa la O de la C es que el aro **cierre**. La versión
   anterior era `curl` y nada más (0.6 en los cuatro dedos, 0.55 en el pulgar):
   la yema del pulgar se quedaba a **0.40** de palma de la del índice y el
   pulgar apuntaba al frente, así que la mano se leía como una garra. Ahora el
   contacto está en **0.086** y el aro cierra.
2. Como en la E, la orientación del pulgar **no** sale de `curl`/`aside`: la da
   el giro de la base, `Thumb1`. Aquí `Thumb2`/`Thumb3` sí llevan grados (25° y
   35°) porque en la O el pulgar tiene que **curvarse** para rodear el agujero;
   el dedo entero se dobla 103°, y eso en la E sería el anillo que hay que
   evitar pero aquí es justo la forma que se busca.
3. El arco de los cuatro dedos queda en **nudillo 62.6° / media 65.1° /
   distal 33.5°**, iguales en los cuatro. Los `extra` de índice–meñique son
   otra vez retoque de simetría, no pose: con el mismo `curl` la falange distal
   iba de 14° en el anular a 41° en el índice y el arco salía escalonado. Los
   calcula `py tools/calibra_o.py` (mismo método que `calibra_e.py`).
4. `muneca.y: 70` es lo que hace visible la letra. El agujero vive en el plano
   largo-frente de la palma, así que con la mano de frente se presenta **de
   canto**: el área del aro en la cámara de la app cae a 0.014 y la O no se lee.
   Girando la muñeca sube a 0.198. Con `y: 90` (el valor de la C) el área es
   algo mayor, 0.220, pero los cuatro dedos se tapan unos a otros; a 70° se ven
   escalonados como en la lámina.
5. `mixamorig1RightArm_033` con `z: -18` separa la mano del pecho, igual que en
   la C y la E.

Formas de equivocarse que ya se probaron y **no** funcionan:

- Puntuar el cierre solo con la distancia de la yema del índice al **cuerpo**
  del pulgar. La búsqueda se conforma con que el índice apoye a media altura y
  entonces el pulgar sigue de largo y sobresale por la derecha como una barra:
  el contorno deja de leerse como O. Hay que exigir **punta contra punta**.
- Buscar en rejilla los seis mandos del pulgar. Con pasos gruesos el óptimo
  queda pegado al borde en cuatro de ellos y no se entera; `tools/afina_o.py`
  recorre cada mando entero, de uno en uno.
- Poner el techo del arco demasiado bajo. Con el nudillo limitado a 62° la
  puntuación descartaba con 10 puntos de castigo la variante que en la hoja de
  contactos era la que más se parecía a la lámina.

Herramientas de esta letra: `py tools/afina_o.py` calcula la pose,
`py tools/final_o.py` la escribe en el catálogo con el antes/después, y
`py tools/verify_o.py` la comprueba por el camino real de la app y la pone al
lado de C, D y E para ver que siguen distinguiéndose. `py tools/variantes_o.py`
genera una hoja con el aro más o menos cerrado, para elegir mirando.

El truco que hace rápida la búsqueda está en `tools/medida_o.py`: el marco de la
palma (muñeca + fila de nudillos) no se mueve al doblar los dedos ni el pulgar,
así que las dos mitades se pueden medir por separado y cruzarse después. 180
formas de dedos por 1024 de pulgar salen de 1204 renderizados en vez de 184320.

---

## 10. Movimiento (`ciclo`) — ejemplo letra J

Algunas letras no son una postura fija: la **J** mantiene la forma de la I
(meñique arriba) y dibuja una **media luna** en el aire. Para eso la seña añade
un `ciclo` junto a su `pose`. La `pose` sigue siendo el punto de partida —el
controlador hace la transición normal de 2 s hasta ella— y el `ciclo` recorre
después una lista de `keyframes` encima de esa pose.

| Campo | Unidad | Qué hace |
|---|---|---|
| `keyframes` | array | Instantes del trazo. Cada uno lleva `t` (0 a 1) y las rotaciones de ese instante: `muneca` y/o `extra`. |
| `holdStartMs` | ms | Espera con la pose inicial antes de arrancar el trazo (deja leer la forma de la mano). |
| `durationMs` | ms | Duración del trazo completo, de `t: 0` a `t: 1`. |
| `holdEndMs` | ms | Espera al terminar, sosteniendo el último keyframe. |
| `resetMs` | ms | Regreso suave al inicio antes de repetir (solo con `loop`). |
| `loop` | boolean | Repite el trazo. Al practicar una letra suelta se repite; al deletrear una palabra la app pasa `loop: false` y se ejecuta una sola vez. |
| `ease` | `"linear"` | Por omisión el trazo acelera y frena (más humano). Con `"linear"` va a velocidad constante. |
| `etiqueta` | string | Cómo se nombra el movimiento en la barra de estado de la app. Si falta, se usa `"trazo con la muñeca"`. |

Solo se interpolan `muneca` y `extra`; los dedos se quedan como los dejó la
`pose`, que es justo lo que se necesita aquí: la forma de la mano no cambia
durante el movimiento, solo la orientación.

**Cuidado con los keyframes incompletos.** Al interpolar, `muneca` y cada hueso
de `extra` se rellenan con `0` en los ejes que el keyframe no menciona, y ese
resultado se escribe **encima** de la `pose`. Es decir: si la `pose` lleva
`muneca: { x: 150 }` y los keyframes no repiten ese `x`, la mano pierde su
orientación en cuanto arranca el trazo. Por eso cada keyframe de la Ñ repite la
muñeca completa y el `z: -18` del hombro, aunque solo esté animando la `y`.
Regla práctica: todo eje que la `pose` use en `muneca` o en un hueso de `extra`
que el `ciclo` toque debe aparecer en **todos** los keyframes.

La media luna de la J se arma con dos huesos a la vez:

- `muneca.z` gira la mano en el plano de la palma, y por lo tanto mueve la punta
  del meñique de derecha a izquierda. Es lo que dibuja el gancho: va de `0` a
  `84` grados.
- `extra.mixamorig1RightForeArm_034.x` dobla el codo, que es lo que **baja y
  sube** la mano entera. Sube hasta `42` a mitad del trazo y vuelve a `0`.

Combinados dan el recorrido de la J vista por el espectador: baja casi recto,
curva por abajo y engancha hacia la izquierda subiendo. Medido sobre el modelo,
la punta del meñique recorre unos 40 cm en vertical y 29 cm en horizontal.

`muneca.x` se mantiene bajo (máximo `6`) a propósito: inclina la mano hacia la
cámara y, si sube más, el meñique se ve escorzado y el trazo pierde legibilidad.

Herramientas de esta letra: `py tools/pose_lab_j13.py` compara variantes del
trazo dibujando el recorrido de la punta en un PNG, `py tools/pose_lab_j14.py`
acerca la cámara para revisar que la mano se vea natural en cada instante y
`py tools/verify_letter_j.py` lo comprueba por el camino real de la app.

Al medir posiciones de huesos con Playwright, **fija la cámara antes de empezar**
y no la muevas entre cuadros: al cambiar `cameraTarget`, model-viewer recentra la
escena y las coordenadas de mundo dejan de ser comparables entre muestras.

### Letra K — vaivén de muñeca

La **K** usa el mismo mecanismo con un trazo mucho más simple: la mano conserva
la forma (índice arriba, medio doblado, pulgar entre los dos) y solo bascula
hacia adelante y hacia atrás. Todo el movimiento vive en un único eje,
`muneca.x`, que va de `-18` (mano echada hacia atrás) a `30` (inclinada hacia
el frente). No se toca el codo ni el hombro, así que el brazo se queda quieto.

Ese eje se eligió midiendo con `py tools/pose_lab_k.py`, que aplica giros
sueltos de muñeca y antebrazo e imprime dónde queda la punta del índice:
`muneca.x` es el único que mueve la punta en profundidad (de `z = 0.09` a
`z = 0.37`) sin arrastrarla de lado. `muneca.y` y `muneca.z` la desplazan
lateralmente y los giros de antebrazo mueven la mano entera, que es justo lo
que aquí no se quiere.

`py tools/verify_letter_k.py` lo comprueba por el camino real de la app:
muestrea la profundidad de la punta durante varios ciclos y confirma que el
recorrido en profundidad es de 27 cm mientras el desplazamiento lateral se
queda en 0.7 cm.

### Letra Ñ — deslizamiento lateral

La **Ñ** mantiene la forma de la N (índice y medio colgando, anular y meñique
cerrados) y marca la tilde deslizando la mano **de izquierda a derecha** vista
por el espectador. La mano no gira: se traslada, así que el movimiento no vive
en la muñeca sino en el hombro, `extra.mixamorig1RightArm_033.y`, que va de
`22` (mano a la izquierda del espectador, sobre el fondo oscuro) a `-2` (junto
al torso, la posición de la N estática).

Ese hueso se eligió midiendo con `py tools/pose_lab_enie.py`, que prueba muñeca,
codo y hombro sobre la pose de la Ñ e imprime cuánto se mueve la punta del
índice en cada eje. La `y` del hombro es la única que da una traslación limpia:
±18 cm de lado con menos de 1 cm de subida y 4 cm de fondo, y sin tocar la
dirección de los dedos. Las alternativas deforman la letra: `muneca.z` mueve la
punta de lado pero **girando** la mano en el plano de la palma (la dirección del
índice pasa de `+0.41` a `-0.32`, o sea los dedos se inclinan en vez de
trasladarse) y `Arm_033.z` sube y baja la mano en lugar de moverla de lado.

La amplitud (`py tools/pose_lab_enie2.py` compara ±10°, ±14° y ±18°) se corrió
hacia la izquierda a propósito: con la ventana centrada en la pose estática, el
final del trazo deja la mano encima del chaleco y las dos puntas que se leen
—índice y medio— caen sobre el azul y el amarillo. Empezando en `22` el barrido
pasa casi entero sobre el fondo oscuro y termina en la posición conocida de la N.

`py tools/verify_letter_enie.py` lo comprueba por el camino real de la app:
29.5 cm de recorrido lateral con 1.5 cm de deriva vertical y 4 cm de fondo.

### Letra Q — círculo en el aire

La **Q** es la G vuelta hacia abajo: el índice baja en diagonal con la yema
enganchada (`extra.mixamorig1RightHandIndex3_042.x: 45`) y el pulgar cuelga por
dentro, dejando el hueco del pico. Sin cambiar de forma, la mano entera dibuja
un **círculo pequeño en sentido de las manecillas del reloj** visto por el
espectador.

Que el trazo es una traslación y no un giro de muñeca se lee en la propia
lámina: el centro del círculo cae a 0.44 largos de palma de las yemas, mientras
que la muñeca está a más de 1.5 palmas. Girando la muñeca el radio saldría el
triple de grande.

Para trasladar la mano por una circunferencia hacen falta dos huesos que
muevan en ejes distintos de la pantalla. `py tools/eje_q.py` los busca midiendo
cuánto se desplaza el pico por cada grado de cada hueso del brazo:

| Hueso | dx/grado | dy/grado |
|---|---|---|
| `Arm_033.x` | `+0.0445` | `-0.0030` |
| `ForeArm_034.x` | `+0.0092` | `-0.0489` |

O sea, el hombro en `x` mueve la mano casi en horizontal puro y el codo en `x`
casi en vertical puro (en largos de palma). Invirtiendo esa matriz de 2×2,
`py tools/movimiento_q.py` resuelve los grados de cada hueso para 12 puntos
repartidos por la circunferencia y escribe los keyframes: el hombro oscila
±10.2° y el codo ±8.9°.

Dos detalles del ciclo:

- `ease: "linear"`. Con la curva por omisión el círculo frena en el arranque y
  en el final, y se ve como si la mano dudara; a velocidad constante gira
  parejo.
- El keyframe de `t: 1` es idéntico al de `t: 0`, porque la vuelta cierra. Así
  el `resetMs` no tiene nada que deshacer y el bucle no da tirones.

`py tools/verify_letter_q.py` lo comprueba por el camino real de la app:
muestrea la animación durante un periodo completo del ciclo y confirma la
forma (pico de 36° apuntando al suelo, puño cerrado) y el trazo (radio de 0.43
palmas, 360° acumulados y sentido horario).

### Letra X — gancho de perfil y jalón diagonal

La **X** no es un puño con el índice un poco menos cerrado ni un gancho
apuntando a la cámara: el índice sale del puño (`curl: 0`) y se dobla en
PIP/DIP (`extra` 18° / 78° / 58°) formando el gancho de la lámina. Medio,
anular y meñique van en puño (`curl: 1.0`); el pulgar se recuesta al
costado como en la A (`aside: 0.4`).

La orientación es la que hace legible el gancho **de perfil**, apuntando
a la izquierda, con la muñeca abajo: `muneca.z: -90` pone el puño de pie
(fistUp ~ 0.9), `x: 20` gira el gancho hacia el lado y `y: 12` enseña el
dorso a 3/4, palma hacia el cuerpo. `muneca.x: 70` apuntaba el puño a la
cámara; `muneca.y: 72` lo acostaba de lado.

La flecha vino de la lámina no es un cabeceo de muñeca: es un **jalón
corto de toda la mano** en diagonal hacia arriba y a la derecha. Sobre
esa pose, `ForeArm.x` desplaza a la derecha y `ForeArm.z` negativo sube
la mano. El ciclo interpola el antebrazo de `(x: 0, z: 0)` a
`(x: 12, z: -12)`.

`py tools/verify_letter_x.py` comprueba forma (gancho PIP ~95°, puño
cerrado, puño de pie) y que el trazo del ciclo sea esa diagonal.

### Letra Z — trazo de la Z mayúscula

La **Z** mantiene el índice estirado y el resto en puño, palma al frente.
Las líneas vino de la lámina no son un giro del dedo: la yema recorre tres
rectas (derecha, diagonal abajo-izquierda, derecha) y la mano entera se
traslada con ella. El movimiento vive en el antebrazo, así la muñeca viaja
con la mano y el índice no cambia de forma.

`py tools/eje_z.py` mide el jacobiano **en pantalla**. En esta orientación:

| Hueso | dpx/grado | dpy/grado | En pantalla |
|---|---|---|---|
| `ForeArm_034.z` | `-3.11` | `+0.34` | horizontal |
| `ForeArm_034.x` | `+0.09` | `+2.15` | vertical |

`py tools/movimiento_z.py` resuelve las cuatro esquinas de una Z de ~84 px
(un largo de mano) y escribe los keyframes: el antebrazo oscila ±22° en `x`
y ±14° en `z`. `ease: "linear"` para que los tres trazos vayan a la misma
velocidad. El keyframe `t: 0` coincide con la `pose`, que es la esquina
superior izquierda.

`py tools/verify_letter_z.py` lo comprueba por el camino real de la app:
forma de señalar y un trazo con tres segmentos en Z.

---

Tras editar `data/catalogo-lsm.json`, regenera el embebido:

```bash
python tools/sync-catalog.py
```
