# Escribe en el catalogo (JSON y JS) la O con la postura de la C y las yemas de indice y pulgar juntas.
$raiz = Split-Path $PSScriptRoot -Parent
$utf8 = New-Object System.Text.UTF8Encoding($false)

$i = [char]0x00ED
$desc = "Mano de perfil delante del pecho, palma hacia el costado, en la misma postura de la C: los cuatro dedos forman el arco de arriba y el pulgar lo cierra por abajo, pero aqu${i} la yema del pulgar sube hasta tocar la yema del ${i}ndice y el hueco queda como un c${i}rculo, la letra O."

$pose = @'
      "pose": {
        "thumb": {
          "curl": 0.4,
          "aside": 1
        },
        "index": {
          "curl": 0.19,
          "spread": 4
        },
        "middle": {
          "curl": 0.19,
          "spread": 1
        },
        "ring": {
          "curl": 0.19,
          "spread": -1
        },
        "pinky": {
          "curl": 0.19,
          "spread": -4
        },
        "muneca": {
          "y": 90
        },
        "extra": {
          "RightHandIndex1": {
            "x": 12
          },
          "RightHandMiddle1": {
            "x": 12
          },
          "RightHandRing1": {
            "x": 12
          },
          "RightHandPinky1": {
            "x": 12
          },
          "RightHandIndex2": {
            "x": 42
          },
          "RightHandMiddle2": {
            "x": 45.94
          },
          "RightHandRing2": {
            "x": 42
          },
          "RightHandPinky2": {
            "x": 42
          },
          "RightHandIndex3": {
            "x": 13.18
          },
          "RightHandMiddle3": {
            "x": 13.18
          },
          "RightHandRing3": {
            "x": 13.18
          },
          "RightHandPinky3": {
            "x": 13.18
          },
          "RightHandThumb1": {
            "x": -20,
            "y": 24,
            "z": 35
          },
          "RightHandThumb2": {
            "x": -40
          },
          "RightHandThumb3": {
            "x": -10
          },
          "RightHand": {
            "x": -24.11,
            "y": -1.88,
            "z": -19.39
          }
        }
      }
'@

foreach ($rel in @("data\catalogo-lsm.json", "js\catalogo-lsm.js")) {
  $ruta = Join-Path $raiz $rel
  $txt = [IO.File]::ReadAllText($ruta, $utf8)
  $crlf = $txt.Contains("`r`n")
  $t = $txt -replace "`r`n", "`n"
  $p = if ($crlf) { $pose -replace "`r`n", "`n" } else { $pose }
  $rx = '(?s)("letra": "O",\s*"nombre": "O",\s*"descripcion": ")[^"]*(",\s*"animacion": "Letra_O",\s*"aliases": \[[^\]]*\],\s*)"pose": \{.*?\n      \}\n(    \},\n    \{\n      "letra": "P")'
  if ($t -notmatch $rx) { throw "No encontre el bloque de la O en $rel" }
  $t = [regex]::Replace($t, $rx, { param($m) $m.Groups[1].Value + $desc + $m.Groups[2].Value + $p.TrimEnd("`n") + "`n" + $m.Groups[3].Value })
  if ($crlf) { $t = $t -replace "`n", "`r`n" }
  [IO.File]::WriteAllText($ruta, $t, $utf8)
  "actualizado $rel"
}
