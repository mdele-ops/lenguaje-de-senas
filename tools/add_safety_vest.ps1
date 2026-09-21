# Recolorea la playera de Remy como chaleco de seguridad naranja
# con franjas reflectantes, y la reincrusta en avatar_3d.glb.
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing

Add-Type -ReferencedAssemblies @("System.Drawing") -TypeDefinition @"
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public static class VestPaint {
    static int Clamp(int v) {
        if (v < 0) return 0;
        if (v > 255) return 255;
        return v;
    }

    static bool InStripe(int y, out float edge) {
        int[][] bands = new int[][] {
            new int[] { 336, 384 },
            new int[] { 596, 644 },
            new int[] { 846, 892 }
        };
        edge = 1f;
        for (int i = 0; i < bands.Length; i++) {
            int a = bands[i][0], b = bands[i][1];
            if (y >= a && y <= b) {
                int dist = Math.Min(y - a, b - y);
                edge = dist < 4 ? dist / 4f : 1f;
                return true;
            }
        }
        return false;
    }

    public static void Paint(string srcPath, string dstPath) {
        using (var src = new Bitmap(srcPath)) {
            var rect = new Rectangle(0, 0, src.Width, src.Height);
            using (var bmp = src.Clone(rect, PixelFormat.Format24bppRgb)) {
                var data = bmp.LockBits(rect, ImageLockMode.ReadWrite, PixelFormat.Format24bppRgb);
                int stride = data.Stride;
                int h = bmp.Height, w = bmp.Width;
                byte[] buf = new byte[stride * h];
                Marshal.Copy(data.Scan0, buf, 0, buf.Length);

                for (int y = 0; y < h; y++) {
                    int row = y * stride;
                    float stripeEdge;
                    bool stripe = InStripe(y, out stripeEdge);
                    for (int x = 0; x < w; x++) {
                        int i = row + x * 3;
                        byte B = buf[i], G = buf[i + 1], R = buf[i + 2];
                        float luma = 0.299f * R + 0.587f * G + 0.114f * B;
                        if (luma < 10f) continue;

                        if (luma < 50f) {
                            // Ribete oscuro del cuello y dobladillo: se conserva.
                            continue;
                        }

                        float shade = luma / 82f;
                        int nr, ng, nb;
                        if (stripe) {
                            // Cinta reflectante amarilla, con borde un poco mas oscuro.
                            float e = 0.55f + 0.45f * stripeEdge;
                            nr = Clamp((int)(255f * shade * e));
                            ng = Clamp((int)(214f * shade * e));
                            nb = Clamp((int)(48f * shade * e));
                        } else {
                            // Naranja de seguridad, conservando el tejido.
                            nr = Clamp((int)(255f * shade));
                            ng = Clamp((int)(102f * shade));
                            nb = Clamp((int)(18f * shade));
                        }
                        buf[i] = (byte)nb;
                        buf[i + 1] = (byte)ng;
                        buf[i + 2] = (byte)nr;
                    }
                }

                Marshal.Copy(buf, 0, data.Scan0, buf.Length);
                bmp.UnlockBits(data);
                bmp.Save(dstPath, ImageFormat.Png);
            }
        }
    }
}
"@

$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $root "avatar_3d.glb"))) {
    $root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

$inspect = Join-Path $root "tools\_inspect"
New-Item -ItemType Directory -Force -Path $inspect | Out-Null
$srcPng = Join-Path $inspect "remy_top_diffuse.png"
$dstPng = Join-Path $inspect "remy_top_vest.png"
$glbPath = Join-Path $root "avatar_3d.glb"
$bakPath = Join-Path $root "avatar_3d.original.glb"

if (-not (Test-Path -LiteralPath $srcPng)) {
    throw "Falta $srcPng"
}

[VestPaint]::Paint($srcPng, $dstPng)
Write-Host "Preview: $dstPng size=$((Get-Item -LiteralPath $dstPng).Length)"

if (-not (Test-Path -LiteralPath $bakPath)) {
    Copy-Item -LiteralPath $glbPath -Destination $bakPath
    Write-Host "Backup: $bakPath"
}

function Read-Glb([string]$path) {
    $bytes = [System.IO.File]::ReadAllBytes($path)
    $jsonChunkLen = [BitConverter]::ToUInt32($bytes, 12)
    $jsonText = [System.Text.Encoding]::UTF8.GetString($bytes, 20, $jsonChunkLen).Trim([char]0)
    $binStart = 12 + 8 + $jsonChunkLen
    $binLen = [BitConverter]::ToUInt32($bytes, $binStart)
    $binOffset = $binStart + 8
    $bin = New-Object byte[] $binLen
    [Array]::Copy($bytes, $binOffset, $bin, 0, $binLen)
    return @{ Json = $jsonText; Bin = $bin }
}

$glb = Read-Glb $glbPath
$png = [System.IO.File]::ReadAllBytes($dstPng)

$oldBin = $glb.Bin
$align = (4 - ($oldBin.Length % 4)) % 4
$newOffset = $oldBin.Length + $align
$pngPad = (4 - ($png.Length % 4)) % 4
$newBinLen = $newOffset + $png.Length + $pngPad

$newBin = New-Object byte[] $newBinLen
[Array]::Copy($oldBin, 0, $newBin, 0, $oldBin.Length)
[Array]::Copy($png, 0, $newBin, $newOffset, $png.Length)

$json = $glb.Json
if ($json -notmatch '"buffers":\[\{"byteLength":(\d+)\}\]') {
    throw "No se encontro buffers.byteLength"
}
$json = $json -replace '"buffers":\[\{"byteLength":\d+\}\]', ('"buffers":[{"byteLength":' + $newBinLen + '}]')

$oldImg = '"bufferView":57,"mimeType":"image/png","name":"Remy_Top_Diffuse"'
$newImg = '"bufferView":59,"mimeType":"image/png","name":"Remy_Top_Diffuse"'
if ($json.IndexOf($oldImg) -lt 0) {
    throw "No se encontro Remy_Top_Diffuse bufferView 57"
}
$json = $json.Replace($oldImg, $newImg)

$oldTail = '{"buffer":0,"byteLength":590842,"byteOffset":30654916}],"samplers":'
$newView = '{"buffer":0,"byteLength":590842,"byteOffset":30654916},{"buffer":0,"byteLength":' + $png.Length + ',"byteOffset":' + $newOffset + '}],"samplers":'
if ($json.IndexOf($oldTail) -lt 0) {
    throw "No se encontro el final de bufferViews"
}
$json = $json.Replace($oldTail, $newView)

$jsonBytes = [System.Text.Encoding]::UTF8.GetBytes($json)
$jsonPad = (4 - ($jsonBytes.Length % 4)) % 4
$jsonChunkLen = $jsonBytes.Length + $jsonPad
$jsonChunk = New-Object byte[] $jsonChunkLen
[Array]::Copy($jsonBytes, 0, $jsonChunk, 0, $jsonBytes.Length)
for ($i = $jsonBytes.Length; $i -lt $jsonChunkLen; $i++) { $jsonChunk[$i] = 0x20 }

$binChunkLen = $newBin.Length
$totalLen = 12 + 8 + $jsonChunkLen + 8 + $binChunkLen
$out = New-Object byte[] $totalLen
$enc = [System.Text.Encoding]::ASCII
[Array]::Copy($enc.GetBytes("glTF"), 0, $out, 0, 4)
[BitConverter]::GetBytes([uint32]2).CopyTo($out, 4)
[BitConverter]::GetBytes([uint32]$totalLen).CopyTo($out, 8)
[BitConverter]::GetBytes([uint32]$jsonChunkLen).CopyTo($out, 12)
[Array]::Copy($enc.GetBytes("JSON"), 0, $out, 16, 4)
[Array]::Copy($jsonChunk, 0, $out, 20, $jsonChunkLen)
$binHdr = 20 + $jsonChunkLen
[BitConverter]::GetBytes([uint32]$binChunkLen).CopyTo($out, $binHdr)
[Array]::Copy($enc.GetBytes("BIN`0"), 0, $out, $binHdr + 4, 4)
[Array]::Copy($newBin, 0, $out, $binHdr + 8, $binChunkLen)

[System.IO.File]::WriteAllBytes($glbPath, $out)
Write-Host ("GLB actualizado: {0} bytes (antes {1})" -f $out.Length, (Get-Item -LiteralPath $bakPath).Length)
