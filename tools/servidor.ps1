# Servidor estatico para abrir practica.html / index.html cuando no hay python
# ni node en el equipo: model-viewer pide el .glb con fetch y file:// lo bloquea.
#
#   powershell -ExecutionPolicy Bypass -File tools/servidor.ps1 [-Port 8123]
param([int]$Port = 8123)

$ErrorActionPreference = "Stop"
$raiz = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$tipos = @{
  ".html" = "text/html; charset=utf-8"
  ".js"   = "application/javascript; charset=utf-8"
  ".css"  = "text/css; charset=utf-8"
  ".json" = "application/json; charset=utf-8"
  ".glb"  = "model/gltf-binary"
  ".png"  = "image/png"
  ".jpg"  = "image/jpeg"
  ".svg"  = "image/svg+xml"
  ".ico"  = "image/x-icon"
}

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Prefixes.Add("http://127.0.0.1:$Port/")
$listener.Start()
Write-Host "sirviendo $raiz en http://localhost:$Port/"

try {
  while ($listener.IsListening) {
    $ctx = $listener.GetContext()
    $ruta = [System.Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath).TrimStart('/')
    if ([string]::IsNullOrWhiteSpace($ruta)) { $ruta = "index.html" }
    $archivo = Join-Path $raiz ($ruta -replace '/', '\')

    # No salir de la carpeta del proyecto.
    $dentro = $archivo.StartsWith($raiz, [System.StringComparison]::OrdinalIgnoreCase)
    if ($dentro -and (Test-Path -LiteralPath $archivo -PathType Leaf)) {
      $ext = [System.IO.Path]::GetExtension($archivo).ToLowerInvariant()
      $ctx.Response.ContentType = if ($tipos.ContainsKey($ext)) { $tipos[$ext] } else { "application/octet-stream" }
      $ctx.Response.Headers.Add("Cache-Control", "no-store")
      $bytes = [System.IO.File]::ReadAllBytes($archivo)
      $ctx.Response.ContentLength64 = $bytes.Length
      $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    } else {
      $ctx.Response.StatusCode = 404
    }
    $ctx.Response.OutputStream.Close()
  }
} finally {
  $listener.Stop()
}
