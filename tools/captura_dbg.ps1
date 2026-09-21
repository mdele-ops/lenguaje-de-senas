param(
  [string]$Url = "http://127.0.0.1:8006/practica.html?letra=D&v=dbg1",
  [int]$Port = 9233
)
$ErrorActionPreference = "Stop"
$edge = @(
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
Write-Host "edge=$edge"
$userData = Join-Path $env:TEMP "lsm-cdp-$Port"
if (Test-Path $userData) { Remove-Item $userData -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Force -Path $userData | Out-Null
Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

$proc = Start-Process -FilePath $edge -PassThru -WindowStyle Hidden -ArgumentList @(
  "--headless=new",
  "--remote-debugging-port=$Port",
  "--user-data-dir=$userData",
  "--hide-scrollbars",
  "--window-size=1280,900",
  "--use-gl=angle",
  "--enable-webgl",
  "--ignore-gpu-blocklist",
  $Url
)
try {
  $ok = $false
  for ($i=0; $i -lt 25; $i++) {
    Start-Sleep -Milliseconds 400
    try {
      $tabs = Invoke-RestMethod "http://127.0.0.1:$Port/json"
      Write-Host ("try {0} tabs={1}" -f $i, @($tabs).Count)
      $tabs | ForEach-Object { Write-Host ("  type={0} url={1} title={2}" -f $_.type, $_.url, $_.title) }
      $ok = $true
      break
    } catch {
      Write-Host ("try {0} wait: {1}" -f $i, $_.Exception.Message)
    }
  }
  if (-not $ok) { throw "no cdp" }
  $page = @($tabs) | Where-Object { $_.type -eq "page" -and $_.webSocketDebuggerUrl } | Select-Object -First 1
  if (-not $page) { $page = @($tabs) | Where-Object { $_.webSocketDebuggerUrl } | Select-Object -First 1 }
  Write-Host ("ws={0}" -f $page.webSocketDebuggerUrl)

  $ws = [System.Net.WebSockets.ClientWebSocket]::new()
  $ws.ConnectAsync([Uri]$page.webSocketDebuggerUrl, [Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null
  $script:nextId = 1
  function Send-Cdp([string]$method, $params) {
    $id = $script:nextId; $script:nextId++
    $msg = @{ id = $id; method = $method }
    if ($null -ne $params) { $msg.params = $params }
    $json = ($msg | ConvertTo-Json -Depth 20 -Compress)
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)
    $ws.SendAsync([ArraySegment[byte]]::new($bytes), [Net.WebSockets.WebSocketMessageType]::Text, $true, [Threading.CancellationToken]::None).GetAwaiter().GetResult() | Out-Null
    return $id
  }
  function Recv-Cdp([int]$wantId, [int]$timeoutMs = 15000) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $buf = New-Object byte[] 65536
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
    throw "timeout id=$wantId"
  }
  Recv-Cdp (Send-Cdp "Runtime.enable" $null) | Out-Null
  Recv-Cdp (Send-Cdp "Page.enable" $null) | Out-Null
  $r = Recv-Cdp (Send-Cdp "Runtime.evaluate" @{ expression = "document.title + ' | ' + location.href + ' | ' + (document.body && document.body.innerText || '').slice(0,180)"; returnByValue = $true })
  Write-Host ("eval=" + ($r.result.result.value))
  $shot = Recv-Cdp (Send-Cdp "Page.captureScreenshot" @{ format = "png"; fromSurface = $true }) 30000
  $out = "c:\Users\KZTRDG\Documents\Lenguaje de señas\tools\screenshots\lab_d_close\dbg_page.png"
  New-Item -ItemType Directory -Force -Path (Split-Path $out) | Out-Null
  [IO.File]::WriteAllBytes($out, [Convert]::FromBase64String($shot.result.data))
  Write-Host ("shot " + (Get-Item $out).Length)
} finally {
  if ($ws) { try { $ws.Abort() } catch { } }
  if ($proc -and -not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
}
