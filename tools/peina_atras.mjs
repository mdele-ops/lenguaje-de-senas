// Peina el pelo del avatar hacia atras (detras de las orejas).
//
// El malla "haircut" de model2.glb tiene dos mechones que caen a los lados de la
// cara. Este script los barre hacia atras girando los vertices alrededor del eje
// vertical de la cabeza (el radio se conserva, asi que el pelo no se mete en el
// craneo). Lo de arriba (raiz y linea del pelo) no se mueve; el barrido crece
// conforme se baja por el mechon.
//
//   node tools/peina_atras.mjs [entrada.glb] [salida.glb]
//
// Por defecto lee y escribe model2.glb. El script NO es idempotente: partir
// siempre del GLB original (git show HEAD:model2.glb) para reintentar.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const ENTRADA = process.argv[2] || path.join(RAIZ, "model2.glb");
const SALIDA = process.argv[3] || path.join(RAIZ, "model2.glb");

// --- Parametros del peinado --------------------------------------------------
const CENTRO_Z = 0.02;          // eje vertical de la cabeza (m)
const ESCALA_X = 0.09;          // semiejes para tratar la cabeza como circulo
const ESCALA_Z = 0.11;
const Y_SIN_BARRIDO = 1.72;     // por encima: el pelo se queda como esta
const Y_BARRIDO_TOTAL = 1.62;   // por debajo: barrido completo
const AZIMUT_DETRAS_OREJA = (124 * Math.PI) / 180; // donde termina el pelo del frente
const VOLUMEN_EXTRA = 0.08;     // las capas del frente quedan por fuera (evita z-fighting)

const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
};

// --- GLB ---------------------------------------------------------------------
const glb = fs.readFileSync(ENTRADA);
if (glb.readUInt32LE(0) !== 0x46546c67) throw new Error("No es un GLB");
const jsonLen = glb.readUInt32LE(12);
const json = JSON.parse(glb.subarray(20, 20 + jsonLen).toString("utf8"));
const binOffset = 20 + jsonLen + 8;
const binLen = glb.readUInt32LE(20 + jsonLen);
const bin = Buffer.from(glb.subarray(binOffset, binOffset + binLen));

const nodoPelo = json.nodes.find((n) => n.name === "haircut");
const prim = json.meshes[nodoPelo.mesh].primitives[0];
const accPos = json.accessors[prim.attributes.POSITION];
const accNor = json.accessors[prim.attributes.NORMAL];

function vista(acc) {
  const bv = json.bufferViews[acc.bufferView];
  const stride = bv.byteStride || 12;
  const base = (bv.byteOffset || 0) + (acc.byteOffset || 0);
  return { base, stride, count: acc.count };
}
const vp = vista(accPos);
const vn = vista(accNor);

const leer = (v, i) => [0, 1, 2].map((c) => bin.readFloatLE(v.base + i * v.stride + c * 4));
const escribir = (v, i, xyz) => xyz.forEach((x, c) => bin.writeFloatLE(x, v.base + i * v.stride + c * 4));

const min = [Infinity, Infinity, Infinity];
const max = [-Infinity, -Infinity, -Infinity];
let movidos = 0;

for (let i = 0; i < vp.count; i++) {
  const [x, y, z] = leer(vp, i);
  const peso = 1 - smooth(Y_BARRIDO_TOTAL, Y_SIN_BARRIDO, y);

  let nx = x, nz = z, giro = 0;
  if (peso > 0) {
    const u = x / ESCALA_X;
    const v = (z - CENTRO_Z) / ESCALA_Z;
    const r = Math.hypot(u, v);
    if (r > 1e-6) {
      const lado = x >= 0 ? 1 : -1;
      const fi = Math.atan2(Math.abs(u), v); // 0 = frente, PI = nuca
      const fiPeinado = AZIMUT_DETRAS_OREJA + (fi * (Math.PI - AZIMUT_DETRAS_OREJA)) / Math.PI;
      const fiNuevo = fi + peso * (fiPeinado - fi);
      const capa = 1 + peso * VOLUMEN_EXTRA * (1 - fi / Math.PI);
      nx = lado * r * capa * Math.sin(fiNuevo) * ESCALA_X;
      nz = CENTRO_Z + r * capa * Math.cos(fiNuevo) * ESCALA_Z;
      giro = fiNuevo - fi; // cuanto giro el vertice (para la normal)
      movidos++;
    }
  }
  escribir(vp, i, [nx, y, nz]);
  [nx, y, nz].forEach((c, k) => {
    min[k] = Math.min(min[k], c);
    max[k] = Math.max(max[k], c);
  });

  if (giro !== 0) {
    const [ax, ay, az] = leer(vn, i);
    // El punto (lado*sin(fi), cos(fi)) pasa a fi + giro; la normal gira igual.
    const lado = x >= 0 ? 1 : -1;
    const bx = ax * Math.cos(giro) + lado * az * Math.sin(giro);
    const bz = -lado * ax * Math.sin(giro) + az * Math.cos(giro);
    escribir(vn, i, [bx, ay, bz]);
  }
}

accPos.min = min;
accPos.max = max;

// --- Reescribir el GLB -------------------------------------------------------
const nuevoJson = Buffer.from(JSON.stringify(json), "utf8");
const relleno = (4 - (nuevoJson.length % 4)) % 4;
const jsonPad = Buffer.concat([nuevoJson, Buffer.alloc(relleno, 0x20)]);
const total = 12 + 8 + jsonPad.length + 8 + bin.length;
const cab = Buffer.alloc(12);
cab.writeUInt32LE(0x46546c67, 0);
cab.writeUInt32LE(2, 4);
cab.writeUInt32LE(total, 8);
const ch1 = Buffer.alloc(8);
ch1.writeUInt32LE(jsonPad.length, 0);
ch1.writeUInt32LE(0x4e4f534a, 4);
const ch2 = Buffer.alloc(8);
ch2.writeUInt32LE(bin.length, 0);
ch2.writeUInt32LE(0x004e4942, 4);
fs.writeFileSync(SALIDA, Buffer.concat([cab, ch1, jsonPad, ch2, bin]));
console.log(`vertices movidos: ${movidos}/${vp.count}  ->  ${SALIDA}`);
