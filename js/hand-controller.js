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

  function isMixamoStyleName(name) {
    const n = String(name || "");
    if (/^(Left|Right)(Shoulder|Arm|ForeArm|Hand|UpLeg|Leg|Foot|ToeBase)/.test(n)) return true;
    if (/^(Left|Right)Hand(Thumb|Index|Middle|Ring|Pinky)\d/.test(n)) return true;
    if (/^(Hips|Spine|Spine1|Spine2|Neck|Head)(_\d+)?$/.test(n)) return true;
    if (/^girl_armature/i.test(n)) return true;
    if (/^mixamorig/i.test(n)) return true;
    if (/^_rootJoint$/i.test(n)) return true;
    return false;
  }

  function isPoseNode(obj) {
    if (!obj || !obj.name) return false;
    if (/Mesh|GEO|scaleCompensation/i.test(obj.name)) return false;
    if (obj.isBone || obj.type === "Bone") return true;
    if (/mixamo/i.test(obj.name)) return true;
    if (/^Boy_/i.test(obj.name)) return true;
    if (isMixamoStyleName(obj.name)) return true;
    if (/^(Left|Right)_/.test(obj.name)) return true;
    if (/\.(L|R)$/.test(obj.name)) return true;
    return /^(Hips|Spine|Chest|Neck|Head|AvatarRoot|Pelvis)$/.test(obj.name);
  }

  function scoreScene(scene) {
    if (!scene || typeof scene.traverse !== "function") return 0;
    let mixamo = 0;
    let avatar = 0;
    let bones = 0;
    try {
      scene.traverse(function (obj) {
        if (!obj) return;
        if (obj.isBone || obj.type === "Bone") bones++;
        if (obj.name && /mixamo/i.test(obj.name)) mixamo++;
        if (obj.name && /^Boy_/i.test(obj.name) && !/scaleCompensation|GEO/i.test(obj.name)) avatar++;
        if (obj.name && isMixamoStyleName(obj.name)) avatar++;
        if (obj.name && /^(Left|Right)_/.test(obj.name)) avatar++;
        if (obj.name && /\.(L|R)$/.test(obj.name) && !/Mesh/i.test(obj.name)) avatar++;
      });
    } catch (_) {
      return 0;
    }
    return mixamo * 10 + avatar * 10 + bones;
  }

  function collectSceneCandidates(modelViewer) {
    const out = [];
    function add(value) {
      if (value && typeof value.traverse === "function" && out.indexOf(value) === -1) {
        out.push(value);
      }
    }
    add(modelViewer.scene);
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
        try {
          const inner = Object.getOwnPropertySymbols(value);
          for (let j = 0; j < inner.length; j++) {
            add(value[inner[j]]);
          }
        } catch (_) {
          /* ignore */
        }
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

  function getGltfParser(modelViewer) {
    if (!modelViewer) return null;
    const symbols = Object.getOwnPropertySymbols(modelViewer);
    for (let i = 0; i < symbols.length; i++) {
      const desc = symbols[i].description || String(symbols[i]);
      const value = modelViewer[symbols[i]];
      if (/currentGLTF|gltf/i.test(desc) && value && value.parser) {
        return value.parser;
      }
      if (value && value.parser && typeof value.parser.getDependency === "function") {
        return value.parser;
      }
    }
    return null;
  }

  function specGlossExt(mat) {
    return (
      (mat &&
        mat.userData &&
        mat.userData.gltfExtensions &&
        mat.userData.gltfExtensions.KHR_materials_pbrSpecularGlossiness) ||
      null
    );
  }

  function boneAliases(name) {
    const aliases = [name];
    if (/[:.]/.test(name)) aliases.push(name.replace(/[:.]/g, ""));
    return aliases;
  }

  function stripBonePrefix(name) {
    return String(name || "")
      .replace(/^mixamorig\d*:/i, "")
      .replace(/^mixamorig\d*/i, "")
      .replace(/^Boy_/i, "")
      .replace(/_\d+$/, "");
  }

  const FINGER_FROM_MIXAMO = {
    Thumb: "Thumb",
    Index: "Index",
    Middle: "Middle",
    Ring: "Ring",
    Pinky: "Little",
  };

  function sideFromName(name) {
    return /^left/i.test(name) ? "Left" : "Right";
  }

  // model2.glb (Mixamo: RightArm, RightHandIndex1, …) es el modelo oficial de señas.
  // También se aceptan boy.glb, hip.glb, girl.glb, Arely y Boy.
  function catalogNameForBone(name) {
    const raw = String(name || "");
    if (!raw) return null;
    if (BONE_TO_CATALOG[raw]) return BONE_TO_CATALOG[raw];
    const stripped = stripBonePrefix(raw);
    if (BONE_TO_CATALOG[stripped]) return BONE_TO_CATALOG[stripped];
    const compact = raw.replace(/[.:]/g, "");
    if (BONE_TO_CATALOG[compact]) return BONE_TO_CATALOG[compact];

    const finger = stripped.match(
      /^(Left|Right)Hand(Thumb|Index|Middle|Ring|Pinky)(\d)$/i
    );
    if (finger) {
      const key =
        finger[2].charAt(0).toUpperCase() + finger[2].slice(1).toLowerCase();
      const mapped = FINGER_FROM_MIXAMO[key];
      if (mapped) return sideFromName(finger[1]) + "_" + mapped + "_" + finger[3];
    }
    if (/^(Left|Right)Arm$/i.test(stripped)) {
      return sideFromName(stripped) + "_UpperArm";
    }
    if (/^(Left|Right)ForeArm$/i.test(stripped)) {
      return sideFromName(stripped) + "_Forearm";
    }
    if (/^(Left|Right)Hand$/i.test(stripped)) {
      return sideFromName(stripped) + "_Wrist";
    }
    return null;
  }

  // Nombres del catálogo LSM ← Mixamo de model2.glb (RightArm, RightHandIndex1), boy.glb, hip.glb, girl.glb, Arely y Boy.
  const BONE_TO_CATALOG = {
    RightArm: "Right_UpperArm",
    RightForeArm: "Right_Forearm",
    RightHand: "Right_Wrist",
    LeftArm: "Left_UpperArm",
    LeftForeArm: "Left_Forearm",
    LeftHand: "Left_Wrist",
    RightHandThumb1: "Right_Thumb_1",
    RightHandThumb2: "Right_Thumb_2",
    RightHandThumb3: "Right_Thumb_3",
    RightHandIndex1: "Right_Index_1",
    RightHandIndex2: "Right_Index_2",
    RightHandIndex3: "Right_Index_3",
    RightHandMiddle1: "Right_Middle_1",
    RightHandMiddle2: "Right_Middle_2",
    RightHandMiddle3: "Right_Middle_3",
    RightHandRing1: "Right_Ring_1",
    RightHandRing2: "Right_Ring_2",
    RightHandRing3: "Right_Ring_3",
    RightHandPinky1: "Right_Little_1",
    RightHandPinky2: "Right_Little_2",
    RightHandPinky3: "Right_Little_3",
    "UpperArm.R": "Right_UpperArm",
    "LowerArm.R": "Right_Forearm",
    "Hand.R": "Right_Wrist",
    "UpperArm.L": "Left_UpperArm",
    "LowerArm.L": "Left_Forearm",
    "Hand.L": "Left_Wrist",
    "Thumb1.R": "Right_Thumb_1",
    "Thumb2.R": "Right_Thumb_2",
    "Thumb3.R": "Right_Thumb_3",
    "Index1.R": "Right_Index_1",
    "Index2.R": "Right_Index_2",
    "Index3.R": "Right_Index_3",
    "Middle1.R": "Right_Middle_1",
    "Middle2.R": "Right_Middle_2",
    "Middle3.R": "Right_Middle_3",
    "Ring1.R": "Right_Ring_1",
    "Ring2.R": "Right_Ring_2",
    "Ring3.R": "Right_Ring_3",
    "Little1.R": "Right_Little_1",
    "Little2.R": "Right_Little_2",
    "Little3.R": "Right_Little_3",
    UpperArmR: "Right_UpperArm",
    LowerArmR: "Right_Forearm",
    HandR: "Right_Wrist",
    UpperArmL: "Left_UpperArm",
    LowerArmL: "Left_Forearm",
    HandL: "Left_Wrist",
    Thumb1R: "Right_Thumb_1",
    Thumb2R: "Right_Thumb_2",
    Thumb3R: "Right_Thumb_3",
    Index1R: "Right_Index_1",
    Index2R: "Right_Index_2",
    Index3R: "Right_Index_3",
    Middle1R: "Right_Middle_1",
    Middle2R: "Right_Middle_2",
    Middle3R: "Right_Middle_3",
    Ring1R: "Right_Ring_1",
    Ring2R: "Right_Ring_2",
    Ring3R: "Right_Ring_3",
    Little1R: "Right_Little_1",
    Little2R: "Right_Little_2",
    Little3R: "Right_Little_3",
    // boy.glb — rig Mixamo mixamorig6 (compatibilidad)
    "mixamorig6:RightArm_033": "Right_UpperArm",
    "mixamorig6:RightForeArm_034": "Right_Forearm",
    "mixamorig6:RightHand_035": "Right_Wrist",
    "mixamorig6:LeftArm_09": "Left_UpperArm",
    "mixamorig6:LeftForeArm_010": "Left_Forearm",
    "mixamorig6:LeftHand_011": "Left_Wrist",
    "mixamorig6:RightHandThumb1_036": "Right_Thumb_1",
    RightHandThumb2_037: "Right_Thumb_2",
    RightHandThumb3_038: "Right_Thumb_3",
    "mixamorig6:RightHandIndex1_040": "Right_Index_1",
    "mixamorig6:RightHandIndex2_041": "Right_Index_2",
    "mixamorig6:RightHandIndex3_042": "Right_Index_3",
    "mixamorig6:RightHandMiddle1_044": "Right_Middle_1",
    "mixamorig6:RightHandMiddle2_045": "Right_Middle_2",
    "mixamorig6:RightHandMiddle3_046": "Right_Middle_3",
    "mixamorig6:RightHandRing1_048": "Right_Ring_1",
    "mixamorig6:RightHandRing2_049": "Right_Ring_2",
    "mixamorig6:RightHandRing3_050": "Right_Ring_3",
    "mixamorig6:RightHandPinky1_052": "Right_Little_1",
    "mixamorig6:RightHandPinky2_053": "Right_Little_2",
    "mixamorig6:RightHandPinky3_054": "Right_Little_3",
    "mixamorig6:LeftHandThumb1_012": "Left_Thumb_1",
    LeftHandThumb2_013: "Left_Thumb_2",
    LeftHandThumb3_014: "Left_Thumb_3",
    "mixamorig6:LeftHandIndex1_016": "Left_Index_1",
    "mixamorig6:LeftHandIndex2_017": "Left_Index_2",
    "mixamorig6:LeftHandIndex3_018": "Left_Index_3",
    "mixamorig6:LeftHandMiddle1_020": "Left_Middle_1",
    "mixamorig6:LeftHandMiddle2_021": "Left_Middle_2",
    "mixamorig6:LeftHandMiddle3_022": "Left_Middle_3",
    "mixamorig6:LeftHandRing1_024": "Left_Ring_1",
    "mixamorig6:LeftHandRing2_025": "Left_Ring_2",
    "mixamorig6:LeftHandRing3_026": "Left_Ring_3",
    "mixamorig6:LeftHandPinky1_028": "Left_Little_1",
    "mixamorig6:LeftHandPinky2_029": "Left_Little_2",
    "mixamorig6:LeftHandPinky3_030": "Left_Little_3",
    // hip.glb — rig Mixamo con sufijo numérico (compatibilidad)
    RightArm_044: "Right_UpperArm",
    RightForeArm_045: "Right_Forearm",
    RightHand_046: "Right_Wrist",
    LeftArm_024: "Left_UpperArm",
    LeftForeArm_025: "Left_Forearm",
    LeftHand_026: "Left_Wrist",
    RightHandThumb1_047: "Right_Thumb_1",
    RightHandThumb2_048: "Right_Thumb_2",
    RightHandThumb3_049: "Right_Thumb_3",
    RightHandIndex1_050: "Right_Index_1",
    RightHandIndex2_051: "Right_Index_2",
    RightHandIndex3_052: "Right_Index_3",
    RightHandMiddle1_00: "Right_Middle_1",
    RightHandMiddle2_053: "Right_Middle_2",
    RightHandMiddle3_054: "Right_Middle_3",
    RightHandRing1_055: "Right_Ring_1",
    RightHandRing2_056: "Right_Ring_2",
    RightHandRing3_057: "Right_Ring_3",
    RightHandPinky1_058: "Right_Little_1",
    RightHandPinky2_059: "Right_Little_2",
    RightHandPinky3_060: "Right_Little_3",
    LeftHandThumb1_027: "Left_Thumb_1",
    LeftHandThumb2_028: "Left_Thumb_2",
    LeftHandThumb3_029: "Left_Thumb_3",
    LeftHandIndex1_030: "Left_Index_1",
    LeftHandIndex2_031: "Left_Index_2",
    LeftHandIndex3_032: "Left_Index_3",
    LeftHandMiddle1_033: "Left_Middle_1",
    LeftHandMiddle2_034: "Left_Middle_2",
    LeftHandMiddle3_035: "Left_Middle_3",
    LeftHandRing1_036: "Left_Ring_1",
    LeftHandRing2_037: "Left_Ring_2",
    LeftHandRing3_038: "Left_Ring_3",
    LeftHandPinky1_039: "Left_Little_1",
    LeftHandPinky2_040: "Left_Little_2",
    LeftHandPinky3_041: "Left_Little_3",
    // girl.glb — rig Mixamo con sufijo numérico (compatibilidad)
    RightArm_39: "Right_UpperArm",
    RightForeArm_38: "Right_Forearm",
    RightHand_37: "Right_Wrist",
    LeftArm_20: "Left_UpperArm",
    LeftForeArm_19: "Left_Forearm",
    LeftHand_18: "Left_Wrist",
    RightHandThumb1_24: "Right_Thumb_1",
    RightHandThumb2_23: "Right_Thumb_2",
    RightHandThumb3_22: "Right_Thumb_3",
    RightHandIndex1_27: "Right_Index_1",
    RightHandIndex2_26: "Right_Index_2",
    RightHandIndex3_25: "Right_Index_3",
    RightHandMiddle1_30: "Right_Middle_1",
    RightHandMiddle2_29: "Right_Middle_2",
    RightHandMiddle3_28: "Right_Middle_3",
    RightHandRing1_33: "Right_Ring_1",
    RightHandRing2_32: "Right_Ring_2",
    RightHandRing3_31: "Right_Ring_3",
    RightHandPinky1_36: "Right_Little_1",
    RightHandPinky2_35: "Right_Little_2",
    RightHandPinky3_34: "Right_Little_3",
    LeftHandThumb1_5: "Left_Thumb_1",
    LeftHandThumb2_4: "Left_Thumb_2",
    LeftHandThumb3_3: "Left_Thumb_3",
    LeftHandIndex1_8: "Left_Index_1",
    LeftHandIndex2_7: "Left_Index_2",
    LeftHandIndex3_6: "Left_Index_3",
    LeftHandMiddle1_11: "Left_Middle_1",
    LeftHandMiddle2_10: "Left_Middle_2",
    LeftHandMiddle3_9: "Left_Middle_3",
    LeftHandRing1_14: "Left_Ring_1",
    LeftHandRing2_13: "Left_Ring_2",
    LeftHandRing3_12: "Left_Ring_3",
    LeftHandPinky1_17: "Left_Little_1",
    LeftHandPinky2_16: "Left_Little_2",
    LeftHandPinky3_15: "Left_Little_3",
    // kid.glb — rig Boy (compatibilidad)
    Boy_RightArm_024: "Right_UpperArm",
    Boy_RightForeArm_027: "Right_Forearm",
    Boy_RightHand_030: "Right_Wrist",
    Boy_LeftArm_0160: "Left_UpperArm",
    Boy_LeftForeArm_0163: "Left_Forearm",
    Boy_LeftHand_00: "Left_Wrist",
    Boy_RightHandThumb1_035: "Right_Thumb_1",
    Boy_RightHandThumb2_036: "Right_Thumb_2",
    Boy_RightHandThumb3_037: "Right_Thumb_3",
    Boy_RightHandIndex1_039: "Right_Index_1",
    Boy_RightHandIndex2_040: "Right_Index_2",
    Boy_RightHandIndex3_041: "Right_Index_3",
    Boy_RightHandMiddle1_031: "Right_Middle_1",
    Boy_RightHandMiddle2_032: "Right_Middle_2",
    Boy_RightHandMiddle3_033: "Right_Middle_3",
    Boy_RightHandRing1_048: "Right_Ring_1",
    Boy_RightHandRing2_049: "Right_Ring_2",
    Boy_RightHandRing3_050: "Right_Ring_3",
    Boy_RightHandPinky1_044: "Right_Little_1",
    Boy_RightHandPinky2_045: "Right_Little_2",
    Boy_RightHandPinky3_046: "Right_Little_3",
  };

  function indexBones(scene) {
    const map = Object.create(null);
    if (!scene) return map;

    function remember(obj) {
      if (!obj || !obj.name) return;
      boneAliases(obj.name).forEach(function (alias) {
        map[alias] = obj;
      });
      const stripped = stripBonePrefix(obj.name);
      if (stripped) map[stripped] = obj;
      const catalogName = catalogNameForBone(obj.name);
      if (catalogName) map[catalogName] = obj;
    }

    scene.traverse(function (obj) {
      if (isPoseNode(obj)) remember(obj);
    });
    if (Object.keys(map).length < 8) {
      scene.traverse(function (obj) {
        remember(obj);
      });
    }

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

  // model2.glb (Mixamo) flexiona los dedos en X. El pulgar trae los ejes
  // locales cruzados respecto al catálogo: X del catálogo es Z del modelo,
  // Y del catálogo es X, y Z del catálogo es Y.
  function modelAxis(boneName, axis) {
    if (boneName && /Thumb/i.test(boneName)) {
      if (axis === "x") return "z";
      if (axis === "y") return "x";
      if (axis === "z") return "y";
    }
    return axis;
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

    function hideNonAvatarProps(scene) {
      if (!scene || !scene.traverse) return;
      scene.traverse(function (obj) {
        if (!obj || !obj.name) return;
        if (/bluetooth|earpiece|headset/i.test(obj.name)) {
          obj.visible = false;
        }
      });
    }

    function prepareAvatarMeshes(scene) {
      if (!scene || !scene.traverse) return;
      hideNonAvatarProps(scene);
      scene.traverse(function (obj) {
        if (!obj) return;
        obj.frustumCulled = false;
        const mats = obj.material
          ? Array.isArray(obj.material)
            ? obj.material
            : [obj.material]
          : [];
        for (let i = 0; i < mats.length; i++) {
          const mat = mats[i];
          if (!mat) continue;
          const name = String(mat.name || "").toLowerCase();
          const meshName = String(obj.name || "").toLowerCase();
          const label = name + " " + meshName;
          const spec = specGlossExt(mat);
          const hasAlbedo = !!(mat.map || (spec && spec.diffuseTexture));
          const isSkin =
            !hasAlbedo && /skin|face|head|iris|lip|eyeball/.test(label);
          const isHair = /hair|lash/.test(label);
          const isCloth = /top|bottom|shoe|pant|jean|shirt|tshirt|cloth|short|socket/.test(
            label
          );

          // Mixamo / Sketchfab: quitar metal y bajar el entorno para que
          // se lea el albedo (si no, el personaje queda blanco).
          if ("metalness" in mat) mat.metalness = 0;
          if ("metalnessMap" in mat) mat.metalnessMap = null;
          if (hasAlbedo) {
            mat.roughness = 0.78;
            if ("envMapIntensity" in mat) mat.envMapIntensity = 0.22;
            if (mat.color && mat.color.setRGB) mat.color.setRGB(1, 1, 1);
          } else if (isSkin) {
            mat.roughness = 0.52;
            if ("envMapIntensity" in mat) mat.envMapIntensity = 0.58;
            if (mat.color && typeof mat.color.r === "number") {
              mat.color.r = Math.min(1, mat.color.r * 1.04 + 0.02);
              mat.color.g = Math.min(1, mat.color.g * 1.015);
              mat.color.b = Math.min(1, mat.color.b * 0.97);
            }
          } else if (isHair) {
            mat.roughness = 0.64;
            if ("envMapIntensity" in mat) mat.envMapIntensity = 0.42;
          } else if (isCloth) {
            mat.roughness = 0.86;
            if ("roughnessMap" in mat) mat.roughnessMap = null;
            if ("envMapIntensity" in mat) mat.envMapIntensity = 0.32;
          } else {
            mat.roughness = 0.72;
            if ("envMapIntensity" in mat) mat.envMapIntensity = 0.4;
          }
          // En personajes skinned el doble-cara aplana la iluminación.
          if (!obj.isSkinnedMesh) mat.side = 2;
          mat.needsUpdate = true;
        }
      });
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

    function restoreSpecGlossAlbedo() {
      const scene = getScene(mv);
      const parser = getGltfParser(mv);
      if (!scene || !parser || typeof parser.getDependency !== "function") {
        return Promise.resolve(false);
      }
      const jobs = [];
      const seen = [];
      scene.traverse(function (obj) {
        const mats = obj && obj.material
          ? Array.isArray(obj.material)
            ? obj.material
            : [obj.material]
          : [];
        for (let i = 0; i < mats.length; i++) {
          const mat = mats[i];
          if (!mat || seen.indexOf(mat) >= 0) continue;
          seen.push(mat);
          if (mat.map) continue;
          const spec = specGlossExt(mat);
          const index =
            spec && spec.diffuseTexture && spec.diffuseTexture.index;
          if (index == null) continue;
          jobs.push(
            parser.getDependency("texture", index).then(function (tex) {
              if (!tex || mat.map) return false;
              mat.map = tex;
              if (mat.color && mat.color.setRGB) mat.color.setRGB(1, 1, 1);
              if ("envMapIntensity" in mat) mat.envMapIntensity = 0.22;
              if ("metalness" in mat) mat.metalness = 0;
              mat.roughness = 0.78;
              mat.needsUpdate = true;
              return true;
            })
          );
        }
      });
      if (!jobs.length) return Promise.resolve(false);
      return Promise.all(jobs).then(function (results) {
        return results.some(Boolean);
      });
    }

    function refreshSkeleton() {
      const scene = getScene(mv);
      prepareAvatarMeshes(scene);
      restoreSpecGlossAlbedo().then(function (changed) {
        if (changed) forceRender({ aggressive: true });
      }).catch(function () {
        /* ignore */
      });
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

    function applyFingerCurl(finger, amount, twist, spread, aside) {
      const rig = catalog.rig || {};
      const chain = (rig.huesos && rig.huesos[finger]) || [];
      const curlMax = rig.curlMaxGrados || {};
      const thumbMax = rig.thumbCurlMaxGrados || {};
      const axis = rig.ejeCurl || "z";
      const curlSign = rig.curlSign == null ? 1 : Number(rig.curlSign);
      const curl = Math.max(-1, Math.min(1, amount == null ? 0 : amount));
      const jointOrderCfg = rig.jointOrder || {};
      const jointOrder = finger === "thumb"
        ? jointOrderCfg.thumb || DEFAULT_THUMB_JOINT_ORDER
        : jointOrderCfg.dedo || DEFAULT_FINGER_JOINT_ORDER;

      chain.forEach(function (boneName, i) {
        const bone = bones[boneName];
        const rest = restPose[boneName];
        if (!bone || !rest) return;

        setQuat(bone, rest);

        const joint = jointOrder[i];
        const deltaDeg =
          finger === "thumb"
            ? sumDeg(joint, curl, thumbMax, THUMB_CURL_DEFAULTS)
            : sumDeg(joint, curl, curlMax, FINGER_CURL_DEFAULTS);

        rotateLocal(bone, modelAxis(boneName, axis), curlSign * deltaDeg * DEG);

        if (typeof twist === "number" && hasKey(joint, "prox")) {
          rotateLocal(bone, modelAxis(boneName, "y"), twist * DEG);
        }
        if (typeof spread === "number" && hasKey(joint, "prox")) {
          rotateLocal(bone, modelAxis(boneName, "z"), spread * DEG);
        }
        if (finger === "thumb" && typeof aside === "number" && hasKey(joint, "trapez")) {
          rotateLocal(bone, modelAxis(boneName, "y"), aside * 32 * DEG);
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

      ["thumb", "index", "middle", "ring", "pinky"].forEach(function (finger) {
        const cfg = pose[finger] || { curl: 0 };
        applyFingerCurl(finger, cfg.curl, cfg.twist, cfg.spread, cfg.aside);
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
          if (rots.x) rotateLocal(bone, modelAxis(name, "x"), rots.x * DEG);
          if (rots.y) rotateLocal(bone, modelAxis(name, "y"), rots.y * DEG);
          if (rots.z) rotateLocal(bone, modelAxis(name, "z"), rots.z * DEG);
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
        applyCatalogCamera({ follow: true });

        if (raw >= 1) {
          const doneLabel = transition.label;
          const doneCycle = transition.cycle;
          holdTarget = transition.to;
          transition = null;
          applyQuats(holdTarget);
          forceRender({ aggressive: true });
          applyCatalogCamera({ follow: true });
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
        applyCatalogCamera({ follow: true });
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
      applyCatalogCamera({ frame: true });
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

    function getHandFocusPoint() {
      const rig = (catalog && catalog.rig) || {};
      const names = [];
      const wrist = getWristBoneName();
      if (wrist) names.push(wrist);
      if (rig.cameraKnuckle) names.push(rig.cameraKnuckle);
      const huesos = rig.huesos || {};
      ["thumb", "index", "middle", "ring", "little"].forEach(function (finger) {
        const chain = huesos[finger] || [];
        if (chain.length) {
          names.push(chain[0]);
          names.push(chain[chain.length - 1]);
        }
      });

      const scene = getScene(mv);
      const off =
        (scene && scene.target && scene.target.position) || { x: 0, y: 0, z: 0 };
      let sx = 0;
      let sy = 0;
      let sz = 0;
      let n = 0;
      for (let i = 0; i < names.length; i++) {
        const p = worldPos(bones[names[i]]);
        if (!p) continue;
        sx += p.x - (off.x || 0);
        sy += p.y - (off.y || 0);
        sz += p.z - (off.z || 0);
        n++;
      }
      if (!n) return null;
      return {
        x: sx / n + (rig.cameraOffsetX != null ? Number(rig.cameraOffsetX) : 0),
        y: sy / n + (rig.cameraOffsetY != null ? Number(rig.cameraOffsetY) : 0.02),
        z: sz / n + (rig.cameraOffsetZ != null ? Number(rig.cameraOffsetZ) : 0.04),
      };
    }

    function getPersonFocusPoint() {
      const rig = (catalog && catalog.rig) || {};
      const names = [
        "Hips_01",
        "Hips_54",
        "Hips",
        "mixamorig6:Hips_01",
        "Spine2_017",
        "Spine2_43",
        "Spine2",
        "mixamorig6:Spine2_04",
        "Spine1_016",
        "Spine1_44",
        "Spine1",
        "mixamorig6:Spine1_03",
        "Spine_015",
        "Spine_45",
        "Spine",
        "mixamorig6:Spine_02",
        "Neck_018",
        "Neck_2",
        "Neck",
        "mixamorig6:Neck_05",
        "Head_019",
        "Head_1",
        "Head",
        "mixamorig6:Head_06",
      ];
      const scene = getScene(mv);
      const off =
        (scene && scene.target && scene.target.position) || { x: 0, y: 0, z: 0 };
      let sx = 0;
      let sy = 0;
      let sz = 0;
      let n = 0;
      for (let i = 0; i < names.length; i++) {
        const p = worldPos(bones[names[i]]);
        if (!p) continue;
        sx += p.x - (off.x || 0);
        sy += p.y - (off.y || 0);
        sz += p.z - (off.z || 0);
        n++;
      }
      if (!n) return null;
      return {
        x: sx / n + (rig.cameraOffsetX != null ? Number(rig.cameraOffsetX) : 0),
        y: sy / n + (rig.cameraOffsetY != null ? Number(rig.cameraOffsetY) : 0.08),
        z: sz / n + (rig.cameraOffsetZ != null ? Number(rig.cameraOffsetZ) : 0.04),
      };
    }

    function applyCatalogCamera(opts) {
      const options = opts || {};
      const rig = (catalog && catalog.rig) || {};
      const scene = getScene(mv);
      if (scene && scene.updateMatrixWorld) scene.updateMatrixWorld(true);

      const trackHand = rig.framePerson !== true;
      const focus = trackHand ? getHandFocusPoint() : getPersonFocusPoint();
      if (focus) {
        mv.cameraTarget =
          focus.x.toFixed(3) +
          "m " +
          focus.y.toFixed(3) +
          "m " +
          focus.z.toFixed(3) +
          "m";
      } else if (rig.cameraTarget) {
        mv.cameraTarget = rig.cameraTarget;
      }

      if (!options.follow) {
        mv.cameraOrbit = rig.cameraOrbit || "12deg 78deg 1.15m";
        if (typeof mv.fieldOfView === "string" || mv.fieldOfView) {
          mv.fieldOfView = rig.fieldOfView || "30deg";
        }
      }

      const shouldJump = options.immediate || options.follow || options.frame;
      if (shouldJump && typeof mv.jumpCameraToGoal === "function") {
        try {
          mv.jumpCameraToGoal();
        } catch (_) {
          /* ignore */
        }
      }
    }

    function applyModelScale() {
      const escala =
        catalog && catalog.modelo && catalog.modelo.escala
          ? catalog.modelo.escala
          : null;
      if (!escala || !escala.length) return;
      const value = escala
        .map(function (n) {
          return String(n);
        })
        .join(" ");
      try {
        mv.scale = value;
        if (typeof mv.setAttribute === "function") {
          mv.setAttribute("scale", value);
        }
      } catch (_) {
        /* ignore */
      }
    }

    function onModelLoad() {
      availableAnimations = mv.availableAnimations
        ? mv.availableAnimations.slice()
        : [];
      pauseMixer();
      applyModelScale();
      const boneCount = refreshSkeleton();
      applyCatalogCamera({ frame: true, immediate: true });
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
