# Capture Wireshark screenshots: open PCAP, type display filter, screenshot.
$ErrorActionPreference = "Continue"
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinApi {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
}
"@
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms

$wireshark = "C:\Program Files\Wireshark\Wireshark.exe"
$pcaps = "c:\Users\Admin\projects\NetworkLabs\lab4\evidence\pcaps"
$shots = "c:\Users\Admin\projects\NetworkLabs\lab4\evidence\shots"

function Stop-Wireshark {
  Get-Process Wireshark -ErrorAction SilentlyContinue | ForEach-Object {
    try { $_.CloseMainWindow() | Out-Null } catch {}
  }
  Start-Sleep -Seconds 1
  Get-Process Wireshark -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 2
}

function Get-WiresharkProcess {
  $deadline = (Get-Date).AddSeconds(40)
  while ((Get-Date) -lt $deadline) {
    $p = Get-Process Wireshark -ErrorAction SilentlyContinue |
      Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero -and $_.MainWindowTitle -match '\.pcap' } |
      Select-Object -First 1
    if ($p) { return $p }
    $p = Get-Process Wireshark -ErrorAction SilentlyContinue |
      Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero } |
      Select-Object -First 1
    if ($p) { return $p }
    Start-Sleep -Milliseconds 400
  }
  return $null
}

function Capture-ProcessWindow($p, [string]$outPath) {
  [WinApi]::ShowWindow($p.MainWindowHandle, 3) | Out-Null
  Start-Sleep -Milliseconds 500
  [WinApi]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
  Start-Sleep -Milliseconds 700

  $r = New-Object WinApi+RECT
  [WinApi]::GetWindowRect($p.MainWindowHandle, [ref]$r) | Out-Null
  $w = $r.Right - $r.Left
  $h = $r.Bottom - $r.Top
  if ($w -lt 100 -or $h -lt 100) { throw "Bad size ${w}x${h}" }

  $bmp = New-Object System.Drawing.Bitmap $w, $h
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($r.Left, $r.Top, 0, 0, (New-Object System.Drawing.Size($w, $h)))
  $bmp.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose()
  $bmp.Dispose()
  Write-Host "Saved $outPath (${w}x${h}) title=$($p.MainWindowTitle)"
}

function Apply-Filter([string]$filter) {
  # Focus display filter (Wireshark 4: Ctrl+/), clear, type, apply
  [System.Windows.Forms.SendKeys]::SendWait("^/")
  Start-Sleep -Milliseconds 300
  [System.Windows.Forms.SendKeys]::SendWait("^a")
  Start-Sleep -Milliseconds 150
  [System.Windows.Forms.SendKeys]::SendWait("{BACKSPACE}")
  Start-Sleep -Milliseconds 150
  # Escape special SendKeys chars in filter: + ^ % ~ ( ) { } [ ]
  $escaped = $filter.Replace("{", "{{").Replace("}", "}}").Replace("+", "{+}").Replace("^", "{^}").Replace("%", "{%}").Replace("~", "{~}").Replace("(", "{(}").Replace(")", "{)}")
  [System.Windows.Forms.SendKeys]::SendWait($escaped)
  Start-Sleep -Milliseconds 250
  [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
  Start-Sleep -Seconds 1
}

function Shot([string]$pcapName, [string]$filter, [string]$outName) {
  try {
    Stop-Wireshark
    $pcap = Join-Path $pcaps $pcapName
    $out = Join-Path $shots $outName
    Write-Host "=== $pcapName | $filter -> $outName ==="
    Start-Process -FilePath $wireshark -ArgumentList @("-r", $pcap) | Out-Null
    Start-Sleep -Seconds 6
    $p = Get-WiresharkProcess
    if (-not $p) { throw "no window" }
    [WinApi]::ShowWindow($p.MainWindowHandle, 3) | Out-Null
    [WinApi]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
    Start-Sleep -Milliseconds 800
    # dismiss dialogs
    [System.Windows.Forms.SendKeys]::SendWait("{ESC}")
    Start-Sleep -Milliseconds 300
    if ($filter) { Apply-Filter $filter }
    # refresh process handle/title
    $p = Get-WiresharkProcess
    Capture-ProcessWindow $p $out
  } catch {
    Write-Host "FAILED $outName : $($_.Exception.Message)"
  }
}

Shot "normal.pcap" "dns" "03-dns-query.png"
Shot "normal.pcap" "dns" "04-dns-answer.png"
Shot "normal.pcap" "tcp.stream eq 0" "05-tcp-client-proxy.png"
Shot "normal.pcap" "tcp.stream eq 1" "06-tcp-proxy-app.png"
Shot "database.pcap" "tcp.port == 6379" "07-tcp-app-db.png"
Shot "normal.pcap" "http and tcp.stream eq 0" "08-http-client-proxy.png"
Shot "normal.pcap" "http and tcp.stream eq 1" "09-http-proxy-app.png"
Shot "database.pcap" "tcp.port == 6379" "10-redis-stream.png"
Shot "failure.pcap" "http.response.code == 502" "11-failure-502.png"
Shot "failure.pcap" "tcp.flags.reset == 1" "12-failure-rst.png"
Shot "recovered.pcap" "http or tcp.flags.syn == 1" "14-recovered-ok.png"

Stop-Wireshark
Write-Host "ALL_SHOTS_DONE"
Get-ChildItem $shots -Filter "*.png" | Select-Object Name, Length | Format-Table -AutoSize
