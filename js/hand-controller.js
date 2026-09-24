/**
 * Controlador LSM: catálogo + model-viewer.
 * Aplica poses por esqueleto con transición (1–3 s) y fuerza redibujado.
 */
(function (global) {
  "use strict";

  const DEG = Math.PI / 180;
  const CATALOG_URL = "data/catalogo-lsm.json";
  const TRANSITION_MIN_MS = 1000;
  const TRANSITION_MAX_MS = 3000;
  const TRANSITION_DEFAULT_MS = 2000;

  function scoreScene(scene) {
    if (!scene || typeof scene.traverse !== "function") return 0;
    let mixamo = 0;
    let bones = 0;
    try {
      scene.traverse(function (obj) {
        if (!obj) return;
        if (obj.isBone || obj.type === "Bone") bones++;
        if (obj.name && /mixamo|^(Left|Right)(Hand|Arm|ForeArm|Shoulder)|^(Hips|Spine|Neck|Head)/i.test(obj.name)) mixamo++;
      });
    } catch (_) {
      return 0;
    }
    return mixamo * 10 + bones;
  }

  function collectSceneCandidates(modelViewer) {
    const out = [];
    function add(value) {
      if (value && typeof value.traverse === "function" && out.indexOf(value) === -1) {
        out.push(value);
      }
    }
    if (modelViewer.model) {
      add(modelViewer.model);
      add(modelViewer.model.scene);
    }
    const symbols = Object.getOwnPropertySymbols(modelViewer);
    for (let i = 0; i < symbols.length; i++) {
      const value = modelViewer[symbols[i]];
      add(value);
      if (value && typeof value === "object") {
        add(value.model);
        add(value.scene);
        add(value.target);
        if (value.target) add(value.target.scene);
      }
    }
    return out;
  }

  function getScene(modelViewer) {
    if (!modelViewer) return null;
    const candidates = collectSceneCandidates(modelViewer);
    let best = null;
    let bestScore = 0;
    for (let i = 0; i < candidates.length; i++) {
      const score = scoreScene(candidates[i]);
      if (score > bestScore) {
        bestScore = score;
        best = candidates[i];
      }
    }
    return best || candidates[0] || null;
  }

  function boneAliases(name) {
    const aliases = [name];
    if (/[:.]/.test(name)) aliases.push(name.replace(/[:.]/g, ""));
    return aliases;
  }

  function indexBones(scene) {
    const map = Object.create(null);
    if (!scene) return map;

    function remember(obj) {
      if (!obj || !obj.name) return;
      boneAliases(obj.name).forEach(function (alias) {
        map[alias] = obj;
      });
    }

    scene.traverse(function (obj) {
      if (obj && (obj.isBone || obj.type === "Bone" || (obj.name && /mixamo|^(Left|Right)(Hand|Arm|ForeArm|Shoulder)|^(Hips|Spine|Neck|Head)/i.test(obj.name)))) {
        remember(obj);
      }
    });

    return map;
  }

  function copyQuat(q) {
    return { x: q.x, y: q.y, z: q.z, w: q.w };
  }

  function captureQuats(bones) {
    const out = Object.create(null);
    Object.keys(bones).forEach(function (name) {
      const bone = bones[name];
      if (bone && bone.quaternion) out[name] = copyQuat(bone.quaternion);
    });
    return out;
  }

  function setQuat(bone, q) {
    if (!bone || !q || !bone.quaternion) return;
    bone.quaternion.set(q.x, q.y, q.z, q.w);
    if (bone.quaternion.normalize) bone.quaternion.normalize();
  }

  function slerpQuat(a, b, t) {
    var ax = a.x,
      ay = a.y,
      az = a.z,
      aw = a.w;
    var bx = b.x,
      by = b.y,
      bz = b.z,
      bw = b.w;

    var cosHalf = aw * bw + ax * bx + ay * by + az * bz;
    if (cosHalf < 0) {
      bx = -bx;
      by = -by;
      bz = -bz;
      bw = -bw;
      cosHalf = -cosHalf;
    }

    var scale0;
    var scale1;
    if (1 - cosHalf > 1e-5) {
      var sinHalf = Math.sqrt(1 - cosHalf * cosHalf);
      var half = Math.atan2(sinHalf, cosHalf);
      scale0 = Math.sin((1 - t) * half) / sinHalf;
      scale1 = Math.sin(t * half) / sinHalf;
    } else {
      scale0 = 1 - t;
      scale1 = t;
    }

    return {
      x: scale0 * ax + scale1 * bx,
      y: scale0 * ay + scale1 * by,
      z: scale0 * az + scale1 * bz,
      w: scale0 * aw + scale1 * bw,
    };
  }

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function lerpNum(a, b, t) {
    const av = typeof a === "number" ? a : 0;
    const bv = typeof b === "number" ? b : 0;
    return av + (bv - av) * t;
  }

  function lerpXYZ(a, b, t) {
    a = a || {};
    b = b || {};
    return {
      x: lerpNum(a.x, b.x, t),
      y: lerpNum(a.y, b.y, t),
      z: lerpNum(a.z, b.z, t),
    };
  }

  function clonePose(pose) {
    if (!pose) return null;
    try {
      return JSON.parse(JSON.stringify(pose));
    } catch (_) {
      return pose;
    }
  }

  function mergePoseKeyframe(basePose, kf) {
    const pose = clonePose(basePose) || {};
    if (!kf) return pose;
    if (kf.muneca) {
      pose.muneca = Object.assign({}, pose.muneca || {}, kf.muneca);
    }
    if (kf.extra) {
      pose.extra = Object.assign({}, pose.extra || {});
      Object.keys(kf.extra).forEach(function (name) {
        pose.extra[name] = Object.assign(
          {},
          pose.extra[name] || {},
          kf.extra[name]
        );
      });
    }
    ["thumb", "index", "middle", "ring", "pinky"].forEach(function (finger) {
      if (kf[finger]) {
        pose[finger] = Object.assign({}, pose[finger] || {}, kf[finger]);
      }
    });
    return pose;
  }

  function sampleCyclePose(basePose, keyframes, t) {
    const kfs = keyframes || [];
    if (!kfs.length) return basePose;
    if (t <= kfs[0].t) return mergePoseKeyframe(basePose, kfs[0]);
    const last = kfs[kfs.length - 1];
    if (t >= last.t) return mergePoseKeyframe(basePose, last);
    let i = 0;
    while (i < kfs.length - 1 && kfs[i + 1].t < t) i++;
    const a = kfs[i];
    const b = kfs[i + 1];
    const span = b.t - a.t || 1;
    const u = (t - a.t) / span;
    const blended = { muneca: lerpXYZ(a.muneca, b.muneca, u) };
    if (a.extra || b.extra) {
      const names = Object.create(null);
      Object.keys(a.extra || {}).forEach(function (n) {
        names[n] = true;
      });
      Object.keys(b.extra || {}).forEach(function (n) {
        names[n] = true;
      });
      blended.extra = {};
      Object.keys(names).forEach(function (n) {
        blended.extra[n] = lerpXYZ(
          (a.extra && a.extra[n]) || {},
          (b.extra && b.extra[n]) || {},
          u
        );
      });
    }
    return mergePoseKeyframe(basePose, blended);
  }

  function cycleT(cycle, now) {
    const holdStart = Number(cycle.holdStartMs) || 0;
    const duration = Number(cycle.durationMs) || 1400;
    const holdEnd = Number(cycle.holdEndMs) || 0;
    const reset = Number(cycle.resetMs) || 500;
    const elapsedRaw = now - cycle.start;
    let elapsed;
    if (cycle.loop) {
      elapsed = elapsedRaw % (holdStart + duration + holdEnd + reset);
    } else {
      elapsed = Math.min(elapsedRaw, holdStart + duration + holdEnd);
    }
    if (elapsed <= holdStart) return 0;
    if (elapsed <= holdStart + duration) {
      const raw = (elapsed - holdStart) / duration;
      return cycle.ease === "linear" ? raw : easeInOutCubic(raw);
    }
    if (elapsed <= holdStart + duration + holdEnd) return 1;
    const back = (elapsed - holdStart - duration - holdEnd) / reset;
    const backT = Math.min(1, Math.max(0, back));
    return 1 - (cycle.ease === "linear" ? backT : easeInOutCubic(backT));
  }

  function rotateLocal(bone, axis, radians) {
    if (!bone || !radians) return;
    if (axis === "x" && bone.rotateX) bone.rotateX(radians);
    else if (axis === "y" && bone.rotateY) bone.rotateY(radians);
    else if (bone.rotateZ) bone.rotateZ(radians);
  }

  function normalize(text) {
    return String(text || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .trim();
  }

  function matchAnimation(available, preferred, aliases) {
    if (!available || !available.length) return null;
    const list = available.map(function (name) {
      return { raw: name, key: normalize(name) };
    });
    const candidates = [preferred].concat(aliases || []).filter(Boolean);

    for (let i = 0; i < candidates.length; i++) {
      const key = normalize(candidates[i]);
      const exact = list.find(function (a) {
        return a.key === key;
      });
      if (exact) return exact.raw;
    }

    for (let i = 0; i < candidates.length; i++) {
      const key = normalize(candidates[i]);
      if (key.length < 2) continue;
      const partial = list.find(function (a) {
        return a.key.includes(key) || key.includes(a.key);
      });
      if (partial) return partial.raw;
    }
    return null;
  }

  // Cada letra con movimiento describe el suyo (la J y la K giran la muñeca,
  // la Ñ desliza, la X jala en diagonal); si no lo declara se usa el texto genérico.
  function cycleLabel(cycle) {
    return (cycle && cycle.etiqueta) || "trazo con la muñeca";
  }

  function clampTransitionMs(ms) {
    const n = Number(ms);
    if (!isFinite(n)) return TRANSITION_DEFAULT_MS;
    return Math.max(TRANSITION_MIN_MS, Math.min(TRANSITION_MAX_MS, n));
  }

  function createController(options) {
    const mv = options.modelViewer;
    const onStatus =
      typeof options.onStatus === "function" ? options.onStatus : function () {};

    let catalog = null;
    let bones = Object.create(null);
    let restPose = Object.create(null);
    let availableAnimations = [];
    let letterMap = Object.create(null);
    let poseRaf = 0;
    let holdTarget = null;
    let transition = null;
    let poseCycle = null;
    let modelReady = false;
    let alphabetBuilt = false;
    let needsRenderFns = [];
    let restApplied = false;

    function indexCatalog(data, fuente) {
      catalog = data;
      letterMap = Object.create(null);
      (catalog.senas || []).forEach(function (sena, index) {
        letterMap[sena.letra] = Object.assign({}, sena, { index: index });
      });
      onStatus(
        "Catálogo LSM cargado (" +
          fuente +
          "): " +
          (catalog.senas || []).length +
          " señas."
      );
      return catalog;
    }

    async function loadCatalog(url) {
      if (global.LSM_CATALOG && global.LSM_CATALOG.senas) {
        return indexCatalog(global.LSM_CATALOG, "embebido");
      }
      try {
        const response = await fetch(url || CATALOG_URL, { cache: "no-store" });
        if (!response.ok) throw new Error("HTTP " + response.status);
        return indexCatalog(await response.json(), "JSON");
      } catch (err) {
        if (global.LSM_CATALOG && global.LSM_CATALOG.senas) {
          return indexCatalog(global.LSM_CATALOG, "embebido-fallback");
        }
        throw new Error(
          "No se pudo cargar el catálogo. Incluye js/catalogo-lsm.js o sirve data/catalogo-lsm.json. " +
            (err && err.message ? err.message : "")
        );
      }
    }

    function getLetters() {
      return (catalog && catalog.senas ? catalog.senas : []).map(function (s) {
        return s.letra;
      });
    }

    function getSena(letra) {
      return letterMap[letra] || null;
    }

    function getDefaultLetter() {
      if (!catalog || !catalog.senas || !catalog.senas.length) return null;
      const neutral = catalog.senas.find(function (s) {
        return s.neutral;
      });
      return neutral ? neutral.letra : catalog.senas[0].letra;
    }

    function getTransitionMs() {
      const fromCatalog =
        catalog && catalog.rig && catalog.rig.transitionMs != null
          ? catalog.rig.transitionMs
          : TRANSITION_DEFAULT_MS;
      return clampTransitionMs(fromCatalog);
    }

    function cacheNeedsRender() {
      needsRenderFns = [];
      const symbols = Object.getOwnPropertySymbols(mv);
      for (let i = 0; i < symbols.length; i++) {
        const sym = symbols[i];
        const desc = sym.description || String(sym);
        if (/needsRender/i.test(desc) && typeof mv[sym] === "function") {
          needsRenderFns.push(mv[sym].bind(mv));
        }
      }
    }

    function updateSkinnedMeshes(scene) {
      if (!scene || !scene.traverse) return;
      scene.traverse(function (obj) {
        if (obj && obj.isSkinnedMesh && obj.skeleton) {
          if (typeof obj.skeleton.update === "function") obj.skeleton.update();
          obj.matrixWorldNeedsUpdate = true;
        }
        if (obj) obj.matrixWorldNeedsUpdate = true;
      });
    }

    function forceRender(opts) {
      const aggressive = !!(opts && opts.aggressive);
      const scene = getScene(mv);
      if (scene) {
        if (scene.updateMatrixWorld) scene.updateMatrixWorld(true);
        updateSkinnedMeshes(scene);
        if ("isDirty" in scene) scene.isDirty = true;
        if (typeof scene.queueRender === "function") scene.queueRender();
      }

      for (let i = 0; i < needsRenderFns.length; i++) {
        try {
          needsRenderFns[i]();
        } catch (_) {
          /* ignore */
        }
      }

      if (typeof mv.requestUpdate === "function") {
        try {
          mv.requestUpdate();
        } catch (_) {
          /* ignore */
        }
      }

      // Solo durante transición: fuerza un frame sin pelear con el drag del usuario
      if (aggressive) {
        try {
          if (
            typeof mv.getCameraOrbit === "function" &&
            typeof mv.jumpCameraToGoal === "function"
          ) {
            const orbit = mv.getCameraOrbit();
            if (orbit) {
              mv.cameraOrbit =
                orbit.theta + "rad " + orbit.phi + "rad " + orbit.radius + "m";
              mv.jumpCameraToGoal();
            }
          }
        } catch (_) {
          /* ignore */
        }
      }
    }

    function stopPoseLoop() {
      if (poseRaf) {
        cancelAnimationFrame(poseRaf);
        poseRaf = 0;
      }
      transition = null;
      holdTarget = null;
      poseCycle = null;
    }

    function pauseMixer() {
      try {
        mv.pause();
        mv.animationName = "";
        if (typeof mv.currentTime === "number") mv.currentTime = 0;
      } catch (_) {
        /* ignore */
      }
    }

    // Algunos modelos (p.ej. rigs Mixamo exportados en T-pose) no traen una
    // postura de reposo natural: los brazos quedan extendidos en cruz. Estas
    // correcciones (rig.restCorrections) doblan hombro/codo UNA sola vez,
    // antes de capturar la pose de reposo, para que el resto del sistema
    // (curvatura de dedos, muñeca) siga funcionando igual sobre una postura
    // ya natural.
    function applyRestCorrections() {
      if (restApplied) return;
      const rig = (catalog && catalog.rig) || {};
      const corrections = rig.restCorrections || [];
      let applied = 0;
      corrections.forEach(function (item) {
        const bone = bones[item.hueso];
        if (!bone) return;
        (item.rotaciones || []).forEach(function (pair) {
          const axis = pair[0];
          const deg = pair[1];
          rotateLocal(bone, axis, deg * DEG);
        });
        applied++;
      });
      if (applied) restApplied = true;
    }

    function refreshSkeleton() {
      const scene = getScene(mv);
      const nextBones = indexBones(scene);
      if (!Object.keys(nextBones).length && Object.keys(bones).length) {
        return Object.keys(bones).length;
      }
      bones = nextBones;
      applyRestCorrections();
      restPose = captureQuats(bones);
      cacheNeedsRender();
      return Object.keys(bones).length;
    }

    // Qué articulación representa cada POSICIÓN dentro de rig.huesos[finger].
    // Cada entrada puede ser: una clave (string), varias claves combinadas
    // (array, se suman sus grados) o vacía/null (ese hueso no rota, p.ej. la
    // punta del dedo en rigs Mixamo). Así el mismo código sirve para rigs con
    // distinta cantidad/orden de huesos por dedo.
    const DEFAULT_THUMB_JOINT_ORDER = ["trapez", "meta", "prox", "dist"];
    const DEFAULT_FINGER_JOINT_ORDER = ["meta", "prox", "midd", "dist"];
    const FINGER_CURL_DEFAULTS = { prox: 70, midd: 85, dist: 65 };
    const THUMB_CURL_DEFAULTS = { trapez: 22, meta: 30, prox: 40, dist: 35 };
    // Hasta dónde dobla cada falange de los cuatro dedos (rig.flexMaxGrados).
    // El curl y el extra del catálogo giran sobre el mismo eje y se suman, así
    // que sin tope una pose puede pedirle 120° a un nudillo que solo da 90 y el
    // dedo se enrolla sobre sí mismo. El pulgar queda fuera: otra anatomía.
    const FINGER_FLEX_DEFAULTS = { prox: 80, midd: 100, dist: 70 };

    function maxFlexDeg(keys) {
      if (!keys) return null;
      const rig = (catalog && catalog.rig) || {};
      const limits = rig.flexMaxGrados || FINGER_FLEX_DEFAULTS;
      const list = Array.isArray(keys) ? keys : [keys];
      let total = 0;
      let found = false;
      list.forEach(function (k) {
        if (!k || limits[k] == null) return;
        total += limits[k];
        found = true;
      });
      return found ? total : null;
    }

    function sumDeg(keys, curl, maxMap, defaults) {
      if (!keys) return 0;
      const list = Array.isArray(keys) ? keys : [keys];
      let total = 0;
      list.forEach(function (k) {
        if (!k) return;
        const v = maxMap && maxMap[k] != null ? maxMap[k] : defaults[k] || 0;
        total += v;
      });
      return curl * total;
    }

    function hasKey(keys, key) {
      if (!keys) return false;
      return Array.isArray(keys) ? keys.indexOf(key) !== -1 : keys === key;
    }

    function applyFingerCurl(finger, cfg, extras, flexed) {
      const rig = catalog.rig || {};
      const chain = (rig.huesos && rig.huesos[finger]) || [];
      const curlMax = rig.curlMaxGrados || {};
      const thumbMax = rig.thumbCurlMaxGrados || {};
      const axis = rig.ejeCurl || "z";
      const curlSign = rig.curlSign == null ? 1 : Number(rig.curlSign);
      const amount = cfg ? cfg.curl : 0;
      const twist = cfg ? cfg.twist : undefined;
      const spread = cfg ? cfg.spread : undefined;
      const aside = cfg ? cfg.aside : undefined;
      const curl = Math.max(-1, Math.min(1, amount == null ? 0 : amount));
      const isThumb = finger === "thumb";
      const jointOrderCfg = rig.jointOrder || {};
      const jointOrder = isThumb
        ? jointOrderCfg.thumb || DEFAULT_THUMB_JOINT_ORDER
        : jointOrderCfg.dedo || DEFAULT_FINGER_JOINT_ORDER;

      chain.forEach(function (boneName, i) {
        const bone = bones[boneName];
        const rest = restPose[boneName];
        if (!bone || !rest) return;

        setQuat(bone, rest);

        const joint = jointOrder[i];
        let deltaDeg = isThumb
          ? sumDeg(joint, curl, thumbMax, THUMB_CURL_DEFAULTS)
          : sumDeg(joint, curl, curlMax, FINGER_CURL_DEFAULTS);

        if (!isThumb) {
          // El extra del catálogo dobla sobre el mismo eje que el curl, así
          // que entra aquí: si se aplicara aparte, el tope no serviría de nada.
          const extraRots = extras && extras[boneName];
          const extraDeg =
            extraRots && typeof extraRots[axis] === "number" ? extraRots[axis] : 0;
          if (extraDeg && flexed) flexed[boneName] = axis;
          deltaDeg += extraDeg * curlSign;
          const limit = maxFlexDeg(joint);
          if (limit != null && deltaDeg > limit) deltaDeg = limit;
        }

        rotateLocal(bone, axis, curlSign * deltaDeg * DEG);

        if (typeof twist === "number" && hasKey(joint, "prox")) {
          rotateLocal(bone, "y", twist * DEG);
        }
        if (typeof spread === "number" && hasKey(joint, "prox")) {
          rotateLocal(bone, "z", spread * DEG);
        }
        if (isThumb && typeof aside === "number" && hasKey(joint, "trapez")) {
          rotateLocal(bone, "y", aside * 32 * DEG);
        }
      });
    }

    function bakePoseToBones(pose) {
      if (!catalog) return;

      // Siempre partir del reposo. Si no, extra de brazo/antebrazo de una
      // letra (p. ej. C) se queda o se acumula al pasar a la siguiente.
      Object.keys(restPose).forEach(function (name) {
        setQuat(bones[name], restPose[name]);
      });

      if (!pose) return;

      // Huesos cuya rotación en el eje de curvatura ya la resolvió
      // applyFingerCurl, recortada al tope de la articulación.
      const flexed = Object.create(null);
      ["thumb", "index", "middle", "ring", "pinky"].forEach(function (finger) {
        applyFingerCurl(finger, pose[finger] || { curl: 0 }, pose.extra, flexed);
      });

      const wristBoneName = getWristBoneName();
      const wristBone = bones[wristBoneName];
      const wristRest = restPose[wristBoneName];
      if (wristBone && wristRest) {
        setQuat(wristBone, wristRest);
        if (pose.muneca) {
          const m = pose.muneca;
          if (m.x) rotateLocal(wristBone, "x", m.x * DEG);
          if (m.y) rotateLocal(wristBone, "y", m.y * DEG);
          if (m.z) rotateLocal(wristBone, "z", m.z * DEG);
        }
      }

      // Rotaciones extra por hueso (se aplican encima de curl/spread/muñeca).
      if (pose.extra) {
        Object.keys(pose.extra).forEach(function (name) {
          const bone = bones[name];
          const rots = pose.extra[name];
          if (!bone || !rots) return;
          if (rots.x && flexed[name] !== "x") rotateLocal(bone, "x", rots.x * DEG);
          if (rots.y && flexed[name] !== "y") rotateLocal(bone, "y", rots.y * DEG);
          if (rots.z && flexed[name] !== "z") rotateLocal(bone, "z", rots.z * DEG);
        });
      }
    }

    function getWristBoneName() {
      const rig = (catalog && catalog.rig) || {};
      return rig.wristBone || "radius_ulna";
    }

    function getFingerBoneNames() {
      const rig = (catalog && catalog.rig) || {};
      const huesos = rig.huesos || {};
      const names = [];
      Object.keys(huesos).forEach(function (finger) {
        (huesos[finger] || []).forEach(function (name) {
          names.push(name);
        });
      });
      return names;
    }

    function hasRecognizedSkeleton() {
      const names = getFingerBoneNames();
      for (let i = 0; i < names.length; i++) {
        if (bones[names[i]]) return true;
      }
      return false;
    }

    function applyQuats(quatMap) {
      Object.keys(quatMap).forEach(function (name) {
        setQuat(bones[name], quatMap[name]);
      });
    }

    function tick() {
      const now = performance.now();

      if (transition) {
        const raw = Math.min(1, (now - transition.start) / transition.duration);
        const t = easeInOutCubic(raw);
        const names = Object.keys(transition.to);
        for (let i = 0; i < names.length; i++) {
          const name = names[i];
          const fromQ = transition.from[name] || restPose[name];
          const toQ = transition.to[name];
          if (!fromQ || !toQ || !bones[name]) continue;
          setQuat(bones[name], slerpQuat(fromQ, toQ, t));
        }
        forceRender({ aggressive: true });

        if (raw >= 1) {
          const doneLabel = transition.label;
          const doneCycle = transition.cycle;
          holdTarget = transition.to;
          transition = null;
          applyQuats(holdTarget);
          forceRender({ aggressive: true });
          if (doneCycle && doneCycle.keyframes && doneCycle.keyframes.length) {
            poseCycle = Object.assign({ start: now }, doneCycle);
            holdTarget = null;
            onStatus(
              doneLabel
                ? "Letra " + doneLabel + " · " + cycleLabel(doneCycle)
                : cycleLabel(doneCycle)
            );
          } else if (doneLabel) {
            onStatus(
              doneLabel === "Neutral"
                ? "Estado Neutral · mano en reposo"
                : "Pose LSM · " + doneLabel
            );
          }
        }
      } else if (poseCycle) {
        const t = cycleT(poseCycle, now);
        bakePoseToBones(
          sampleCyclePose(poseCycle.basePose, poseCycle.keyframes, t)
        );
        forceRender({ aggressive: true });
        if (!poseCycle.loop) {
          const holdStart = Number(poseCycle.holdStartMs) || 0;
          const duration = Number(poseCycle.durationMs) || 1400;
          const holdEnd = Number(poseCycle.holdEndMs) || 0;
          if (now - poseCycle.start >= holdStart + duration + holdEnd) {
            holdTarget = captureQuats(bones);
            poseCycle = null;
          }
        }
      } else if (holdTarget) {
        applyQuats(holdTarget);
        forceRender({ aggressive: false });
      }

      poseRaf = requestAnimationFrame(tick);
    }

    function ensureLoop() {
      if (!poseRaf) poseRaf = requestAnimationFrame(tick);
    }

    function startTransitionToPose(pose, label, cycle) {
      pauseMixer();
      if (!Object.keys(bones).length) refreshSkeleton();

      poseCycle = null;
      const startPose =
        cycle && cycle.keyframes && cycle.keyframes.length
          ? sampleCyclePose(pose, cycle.keyframes, 0)
          : pose;
      const from = captureQuats(bones);
      bakePoseToBones(startPose);
      const to = captureQuats(bones);
      applyQuats(from);

      transition = {
        from: from,
        to: to,
        start: performance.now(),
        duration: getTransitionMs(),
        label: label || "",
        cycle: cycle
          ? Object.assign({}, cycle, { basePose: pose || {} })
          : null,
      };
      holdTarget = null;
      ensureLoop();
      forceRender({ aggressive: true });
    }

    function playAnimation(animName) {
      stopPoseLoop();
      try {
        mv.pause();
      } catch (_) {
        /* ignore */
      }
      mv.animationName = animName;
      mv.currentTime = 0;
      const playResult = mv.play();
      if (playResult && typeof playResult.catch === "function") {
        playResult.catch(function () {});
      }
      forceRender();
    }

    function getLetterPlayMs(letra) {
      const trans = getTransitionMs();
      const sena = getSena(letra);
      if (sena && sena.ciclo && sena.ciclo.keyframes) {
        const c = sena.ciclo;
        return (
          trans +
          (Number(c.holdStartMs) || 0) +
          (Number(c.durationMs) || 1400) +
          (Number(c.holdEndMs) || 400)
        );
      }
      return trans + 850;
    }

    function mostrarSena(letra, options) {
      const opts = options || {};
      const sena = getSena(letra);
      if (!sena) {
        onStatus("Letra no encontrada en el catálogo: " + letra);
        return { modo: "error" };
      }

      if (!modelReady) {
        onStatus("Esperando a que cargue el modelo 3D…");
        return { modo: "pending", sena: sena };
      }

      if (sena.neutral || sena.pose === null) {
        if (!Object.keys(restPose).length) refreshSkeleton();
        startTransitionToPose(null, "Neutral");
        onStatus(
          "Transición a Neutral (" + (getTransitionMs() / 1000).toFixed(1) + " s)"
        );
        return { modo: "neutral", sena: sena };
      }

      const clip = matchAnimation(
        availableAnimations,
        sena.animacion,
        sena.aliases
      );
      const esClipGenerico =
        clip &&
        /pose_ok|do_handriggedaction/i.test(clip) &&
        !normalize(sena.animacion || "").includes(normalize(clip));

      if (clip && !esClipGenerico) {
        playAnimation(clip);
        onStatus("Animación: " + clip + " · Letra " + letra);
        return { modo: "animacion", clip: clip, sena: sena };
      }

      if (sena.pose) {
        if (!Object.keys(bones).length) refreshSkeleton();
        if (!hasRecognizedSkeleton()) {
          onStatus(
            "Catálogo conectado, pero no se pudo leer el esqueleto del modelo 3D para la letra " +
              letra
          );
          return { modo: "none", sena: sena };
        }
        const cycle =
          sena.ciclo && sena.ciclo.keyframes && sena.ciclo.keyframes.length
            ? Object.assign({}, sena.ciclo, {
                loop: opts.loop !== false && sena.ciclo.loop !== false,
              })
            : null;
        startTransitionToPose(sena.pose, letra, cycle);
        onStatus(
          cycle
            ? "Letra " + letra + " · " + cycleLabel(cycle)
            : "Transición a " +
                letra +
                " (" +
                (getTransitionMs() / 1000).toFixed(1) +
                " s)"
        );
        return { modo: cycle ? "ciclo" : "pose", sena: sena };
      }

      if (clip) {
        playAnimation(clip);
        onStatus("Animación de respaldo: " + clip + " · Letra " + letra);
        return { modo: "animacion", clip: clip, sena: sena };
      }

      onStatus("Sin animación ni pose para la letra " + letra);
      return { modo: "none", sena: sena };
    }

    function worldPos(bone) {
      if (!bone || !bone.matrixWorld || !bone.matrixWorld.elements) return null;
      const e = bone.matrixWorld.elements;
      return { x: e[12], y: e[13], z: e[14] };
    }

    function applyCatalogCamera() {
      const rig = (catalog && catalog.rig) || {};
      const scene = getScene(mv);
      if (scene && scene.updateMatrixWorld) scene.updateMatrixWorld(true);

      const rigBones = rig.huesos || {};
      const names = [getWristBoneName()];
      ["index", "middle", "ring", "pinky", "thumb"].forEach(function (finger) {
        const list = rigBones[finger];
        if (list && list.length) names.push(list[list.length - 1]);
      });
      const pts = [];
      names.forEach(function (name) {
        const p = worldPos(bones[name]);
        if (p) pts.push(p);
      });
      if (pts.length >= 2) {
        // El modelo cuelga del target de la cámara: el punto en espacio del
        // modelo es la posición mundo menos la del target.
        const off =
          (scene && scene.target && scene.target.position) ||
          { x: 0, y: 0, z: 0 };
        let x = 0;
        let y = 0;
        let z = 0;
        pts.forEach(function (p) {
          x += p.x;
          y += p.y;
          z += p.z;
        });
        x = x / pts.length - (off.x || 0);
        y = y / pts.length - (off.y || 0);
        z = z / pts.length - (off.z || 0);
        // El visor es ancho. Si la cámara mira el centro geométrico de la
        // mano, la palma queda a la derecha junto al torso. Este sesgo
        // la deja en el centro del recuadro.
        const bias = rig.cameraBias || [0, 0, 0];
        x += bias[0] || 0;
        y += bias[1] || 0;
        z += bias[2] || 0;
        mv.cameraTarget =
          x.toFixed(3) + "m " + y.toFixed(3) + "m " + z.toFixed(3) + "m";
      } else if (rig.cameraTarget) {
        mv.cameraTarget = rig.cameraTarget;
      }
      mv.cameraOrbit = rig.cameraOrbit || "0deg 84deg 2.5m";
      if (typeof mv.fieldOfView === "string" || mv.fieldOfView) {
        mv.fieldOfView = "30deg";
      }
      if (typeof mv.jumpCameraToGoal === "function") {
        try {
          mv.jumpCameraToGoal();
        } catch (_) {
          /* ignore */
        }
      }
    }

    function onModelLoad() {
      availableAnimations = mv.availableAnimations
        ? mv.availableAnimations.slice()
        : [];
      pauseMixer();
      const boneCount = refreshSkeleton();
      applyCatalogCamera();
      modelReady = hasRecognizedSkeleton() || boneCount > 10;
      forceRender({ aggressive: true });
      onStatus(
        "Modelo listo · " +
          availableAnimations.length +
          " animaciones · " +
          boneCount +
          " nodos"
      );
      return {
        animations: availableAnimations,
        bones: Object.keys(bones),
      };
    }

    function onModelError(detail) {
      modelReady = false;
      restApplied = false;
      onStatus(
        "Error al cargar el modelo 3D. Verifica model2.glb. " + (detail || "")
      );
    }

    return {
      loadCatalog: loadCatalog,
      getLetters: getLetters,
      getSena: getSena,
      getDefaultLetter: getDefaultLetter,
      getCatalog: function () {
        return catalog;
      },
      getTransitionMs: getTransitionMs,
      getLetterPlayMs: getLetterPlayMs,
      mostrarSena: mostrarSena,
      onModelLoad: onModelLoad,
      onModelError: onModelError,
      refreshSkeleton: refreshSkeleton,
      forceRender: forceRender,
      isModelReady: function () {
        return modelReady;
      },
      getAvailableAnimations: function () {
        return availableAnimations.slice();
      },
      markAlphabetBuilt: function () {
        alphabetBuilt = true;
      },
      isAlphabetBuilt: function () {
        return alphabetBuilt;
      },
      applyTestPose: function (pose) {
        stopPoseLoop();
        pauseMixer();
        if (!Object.keys(bones).length) refreshSkeleton();
        bakePoseToBones(pose);
        holdTarget = captureQuats(bones);
        ensureLoop();
        forceRender({ aggressive: true });
      },
    };
  }

  global.LSMHand = {
    CATALOG_URL: CATALOG_URL,
    createController: createController,
  };
})(window);
