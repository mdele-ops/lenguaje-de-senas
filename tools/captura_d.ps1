# Captura la letra D usando el websocket de la pagina (no el del browser).
param(
  [string]$Url = "http://127.0.0.1:8006/practica.html?letra=D&v=dclose2",
  [string]$Out = "c:\Users\KZTRDG\Documents\Lenguaje de señas\tools\screenshots\lab_d_close\D_yemas.png",
  [int]$Port = 9235,
  [int]$WaitSec = 90
)

$ErrorActionPreference = "Stop"
$edge = @(
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw "No se encontro msedge.exe" }

$userData = Join-Path $env:TEMP "lsm-cdp-$Port"
if (Test-Path $userData) { Remove-Item $userData -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Force -Path $userData | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $Out) | Out-Null

Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

$proc = Start-Process -FilePath $edge -PassThru -WindowStyle Hidden -ArgumentList @(
  "--headless=new",
  "--remote-debugging-port=$Port",
  "--user-data-dir=$userData",
  "--disable-gpu",
  "--hide-scrollbars",
  "--window-size=1280,900",
  "--use-gl=angle",
  "--enable-webgl",
  "--ignore-gpu-blocklist",
  $Url
)

$ws = $null
try {
  $ok = $false
  for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 400
    try { $null = Invoke-RestMethod "http://127.0.0.1:$Port/json/version"; $ok = $true; break } catch { }
  }
  if (-not $ok) { throw "CDP no arranco" }

  $page = $null
  for ($i = 0; $i -lt 25; $i++) {
    Start-Sleep -Milliseconds 400
    $pages = Invoke-RestMethod "http://127.0.0.1:$Port/json/list"
    $page = $pages | Where-Object { $_.type -eq "page" -and $_.url -like "*practica*" } | Select-Object -First 1
    if ($page -and $page.webSocketDebuggerUrl) { break }
  }
  if (-not $page) { throw "No page target" }

  $ws = [System.Net.WebSockets.ClientWebSocket]::new()
  $ws.ConnectAsync([Uri]$page.webSocketDebuggerUrl, [Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null

  $script:nextId = 1
  function Send-Cdp([string]$method, $params) {
    $id = $script:nextId
    $script:nextId++
    $msg = @{ id = $id; method = $method }
    if ($null -ne $params) { $msg.params = $params }
    $json = ($msg | ConvertTo-Json -Depth 30 -Compress)
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)
    $ws.SendAsync([ArraySegment[byte]]::new($bytes), [Net.WebSockets.WebSocketMessageType]::Text, $true, [Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null
    return $id
  }

  function Recv-Cdp([int]$wantId, [int]$timeoutMs = 20000) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $buf = New-Object byte[] 262144
    while ($sw.ElapsedMilliseconds -lt $timeoutMs) {
      $sb = New-Object Text.StringBuilder
      do {
        $seg = [ArraySegment[byte]]::new($buf)
        $r = $ws.ReceiveAsync($seg, [Threading.CancellationToken]::None).GetAwaiter().GetResult()
        [void]$sb.Append([Text.Encoding]::UTF8.GetString($buf, 0, $r.Count))
      } while (-not $r.EndOfMessage)
      $obj = $sb.ToString() | ConvertFrom-Json
      if ($obj.id -eq $wantId) { return $obj }
    }
    throw "Timeout esperando CDP id=$wantId"
  }

  function Eval-Js([string]$expression) {
    $id = Send-Cdp "Runtime.evaluate" @{
      expression = $expression
      returnByValue = $true
      awaitPromise = $true
    }
    return Recv-Cdp $id
  }

  Recv-Cdp (Send-Cdp "Runtime.enable" $null) | Out-Null
  Recv-Cdp (Send-Cdp "Page.enable" $null) | Out-Null

  $ready = $false
  $deadline = [datetime]::UtcNow.AddSeconds($WaitSec)
  while ([datetime]::UtcNow -lt $deadline) {
    try {
      $r = Eval-Js "!!(window.__LSM_CONTROLLER__ && window.__LSM_CONTROLLER__.isModelReady())"
      if ($r.result.result.value -eq $true) { $ready = $true; break }
    } catch { }
    Start-Sleep -Milliseconds 500
  }
  if (-not $ready) {
    $info = ""
    try { $info = (Eval-Js "(document.getElementById('anim-info')||{}).textContent||''").result.result.value } catch { }
    throw "El modelo 3D no cargo. Estado: $info"
  }

  Eval-Js @'
(() => {
  const c = window.__LSM_CONTROLLER__;
  const s = c.getSena("D");
  if (s && s.pose) c.applyTestPose(s.pose);
  return !!(s && s.pose);
})()
'@ | Out-Null
  Start-Sleep -Milliseconds 800

  $box = Eval-Js @'
(() => {
  const el = document.getElementById("handViewer");
  const r = el.getBoundingClientRect();
  return { x: r.x, y: r.y, w: r.width, h: r.height };
})()
'@
  $b = $box.result.result.value
  Write-Host ("viewer x={0:n0} y={1:n0} w={2:n0} h={3:n0}" -f $b.x, $b.y, $b.w, $b.h)

  $id = Send-Cdp "Page.captureScreenshot" @{
    format = "png"
    fromSurface = $true
    clip = @{
      x = [double]$b.x
      y = [double]$b.y
      width = [double]$b.w
      height = [double]$b.h
      scale = 1
    }
  }
  $shot = Recv-Cdp $id 30000
  $b64 = $shot.result.data
  if (-not $b64) { throw "Screenshot vacio" }
  [IO.File]::WriteAllBytes($Out, [Convert]::FromBase64String($b64))
  Write-Host ("ok {0} bytes={1}" -f $Out, (Get-Item -LiteralPath $Out).Length)
}
finally {
  if ($ws) { try { $ws.Abort() } catch { } }
  if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
}
