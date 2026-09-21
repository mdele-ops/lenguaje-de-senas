# Servidor estatico local (reemplazo de tools/servidor.py cuando no hay Python).
param(
  [int]$Port = 8006,
  [string]$Root = ""
)

if (-not $Root) {
  $Root = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}

$ErrorActionPreference = "Stop"
$prefix = "http://127.0.0.1:$Port/"
$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add($prefix)
try {
  $listener.Start()
} catch {
  throw "No se pudo abrir $prefix : $($_.Exception.Message)"
}
Write-Host "sirviendo $Root"
Write-Host "  local:   $prefix"

$mime = @{
  ".html" = "text/html; charset=utf-8"
  ".js"   = "text/javascript"
  ".mjs"  = "text/javascript"
  ".css"  = "text/css"
  ".json" = "application/json"
  ".glb"  = "model/gltf-binary"
  ".gltf" = "model/gltf+json"
  ".wasm" = "application/wasm"
  ".hdr"  = "image/vnd.radiance"
  ".png"  = "image/png"
  ".jpg"  = "image/jpeg"
  ".jpeg" = "image/jpeg"
  ".webp" = "image/webp"
  ".svg"  = "image/svg+xml"
  ".woff2"= "font/woff2"
}

function Send-Bytes($res, [byte[]]$data, $status, $contentType, $extraHeaders) {
  $res.StatusCode = $status
  $res.ContentType = $contentType
  $res.Headers["Accept-Ranges"] = "bytes"
  $res.Headers["Access-Control-Allow-Origin"] = "*"
  if ($extraHeaders) {
    foreach ($k in $extraHeaders.Keys) { $res.Headers[$k] = $extraHeaders[$k] }
  }
  $res.ContentLength64 = $data.Length
  $res.OutputStream.Write($data, 0, $data.Length)
  $res.OutputStream.Close()
}

try {
  while ($listener.IsListening) {
    $ctx = $listener.GetContext()
    $req = $ctx.Request
    $res = $ctx.Response
    try {
      $rel = [Uri]::UnescapeDataString($req.Url.AbsolutePath.TrimStart("/"))
      if ([string]::IsNullOrWhiteSpace($rel)) { $rel = "index.html" }
      $full = [IO.Path]::GetFullPath((Join-Path $Root $rel))
      $rootFull = [IO.Path]::GetFullPath($Root)
      if (-not $full.StartsWith($rootFull, [StringComparison]::OrdinalIgnoreCase)) {
        Send-Bytes $res ([Text.Encoding]::UTF8.GetBytes("forbidden")) 403 "text/plain" $null
        continue
      }
      if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
        Send-Bytes $res ([Text.Encoding]::UTF8.GetBytes("not found")) 404 "text/plain" $null
        continue
      }
      $ext = [IO.Path]::GetExtension($full).ToLowerInvariant()
      $ctype = $mime[$ext]
      if (-not $ctype) { $ctype = "application/octet-stream" }
      $fs = [IO.File]::Open($full, "Open", "Read", "Read")
      try {
        $len = $fs.Length
        $start = [int64]0
        $end = $len - 1
        $status = 200
        $extra = @{}
        $range = $req.Headers["Range"]
        if ($range -and $range -match "bytes=(\d*)-(\d*)") {
          if ($Matches[1] -ne "") { $start = [int64]$Matches[1] }
          if ($Matches[2] -ne "") { $end = [int64]$Matches[2] }
          if ($end -ge $len) { $end = $len - 1 }
          if ($start -gt $end) {
            $res.StatusCode = 416
            $res.Headers["Content-Range"] = "bytes */$len"
            $res.Close()
            continue
          }
          $status = 206
          $extra["Content-Range"] = "bytes $start-$end/$len"
        }
        $count = $end - $start + 1
        $res.StatusCode = $status
        $res.ContentType = $ctype
        $res.Headers["Accept-Ranges"] = "bytes"
        $res.Headers["Access-Control-Allow-Origin"] = "*"
        foreach ($k in $extra.Keys) { $res.Headers[$k] = $extra[$k] }
        $res.ContentLength64 = $count
        $fs.Position = $start
        $buf = New-Object byte[] (256 * 1024)
        $left = $count
        while ($left -gt 0) {
          $n = $fs.Read($buf, 0, [Math]::Min($buf.Length, $left))
          if ($n -le 0) { break }
          $res.OutputStream.Write($buf, 0, $n)
          $left -= $n
        }
        $res.OutputStream.Close()
      } finally {
        $fs.Dispose()
      }
    } catch {
      try {
        $res.StatusCode = 500
        $bytes = [Text.Encoding]::UTF8.GetBytes("$($_.Exception.Message)")
        $res.OutputStream.Write($bytes, 0, $bytes.Length)
        $res.Close()
      } catch { }
    }
  }
} finally {
  $listener.Stop()
  $listener.Close()
}
