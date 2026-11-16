$ErrorActionPreference = "SilentlyContinue"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logPath = Join-Path $scriptDir "guardiao.log"
$configPath = Join-Path $scriptDir "config.json"
$port = 51337

$fileActionText = @'
$path = $Event.SourceEventArgs.FullPath
if (-not $path) { return }
$exts = @(".exe", ".msi", ".msix", ".zip", ".rar", ".7z", ".iso")
$keywords = @("riot", "valorant", "vanguard", "leagueoflegends", "league of legends", "teamfight tactics")
$logPath = "__LOGPATH__"
$port = __PORT__
$nome = [System.IO.Path]::GetFileName($path).ToLower()
$ext = [System.IO.Path]::GetExtension($nome)
if ($exts -notcontains $ext) { return }
$match = $false
foreach ($k in $keywords) { if ($nome.Contains($k)) { $match = $true; break } }
if (-not $match) { return }
Start-Sleep -Seconds 2
try {
    Remove-Item -LiteralPath $path -Force -ErrorAction Stop
    Add-Content -LiteralPath $logPath -Value ("[{0}] instalador removido: {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $path)
    try {
        $c = New-Object System.Net.Sockets.TcpClient
        $c.Connect("127.0.0.1", $port)
        $b = [Text.Encoding]::UTF8.GetBytes("event:Instalador da Riot removido: $nome")
        $c.GetStream().Write($b, 0, $b.Length)
        $c.Close()
    } catch { }
} catch { }
'@
$fileActionText = $fileActionText.Replace("__LOGPATH__", $logPath).Replace("__PORT__", "$port")
$fileAction = [scriptblock]::Create($fileActionText)

$installDirs = New-Object System.Collections.Generic.List[string]
foreach ($dr in (Get-PSDrive -PSProvider FileSystem | Select-Object -ExpandProperty Root)) {
    $installDirs.Add((Join-Path $dr "Riot Games"))
}
$installDirs.Add((Join-Path $env:ProgramData "Riot Games"))
$installDirs.Add((Join-Path $env:LOCALAPPDATA "Riot Games"))
$installDirs.Add((Join-Path $env:APPDATA "Riot Games"))
$installDirs.Add((Join-Path $env:APPDATA "riot-client-ux"))
$installDirsLiteral = "@(" + (($installDirs | ForEach-Object { "'" + ($_ -replace "'", "''") + "'" }) -join ", ") + ")"

$procActionText = @'
$nome = $Event.SourceEventArgs.NewEvent.TargetInstance.Name
$procs = @("RiotClientServices.exe", "RiotClientUx.exe", "RiotClientCrashHandler.exe",
    "VALORANT.exe", "VALORANT-Win64-Shipping.exe", "vgtray.exe", "vgc.exe",
    "LeagueClient.exe", "LeagueClientUx.exe", "League of Legends.exe", "LoLPatcher.exe")
$installDirs = __INSTALLDIRS__
$logPath = "__LOGPATH__"
$port = __PORT__
foreach ($p in $procs) {
    if ($p -ieq $nome) {
        & taskkill /F /IM $nome | Out-Null
        Add-Content -LiteralPath $logPath -Value ("[{0}] processo encerrado: {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $nome)
        foreach ($dir in $installDirs) {
            if (Test-Path -LiteralPath $dir) { Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction SilentlyContinue }
        }
        try {
            $c = New-Object System.Net.Sockets.TcpClient
            $c.Connect("127.0.0.1", $port)
            $b = [Text.Encoding]::UTF8.GetBytes("event:Processo da Riot encerrado: $nome")
            $c.GetStream().Write($b, 0, $b.Length)
            $c.Close()
        } catch { }
        break
    }
}
'@
$procActionText = $procActionText.Replace("__INSTALLDIRS__", $installDirsLiteral).Replace("__LOGPATH__", $logPath).Replace("__PORT__", "$port")
$procAction = [scriptblock]::Create($procActionText)

$dirs = New-Object System.Collections.Generic.List[string]
$dirs.Add((Join-Path $env:USERPROFILE "Downloads"))
$dirs.Add((Join-Path $env:USERPROFILE "Desktop"))
$dirs.Add((Join-Path $env:USERPROFILE "OneDrive\Desktop"))
if ($env:TEMP) { $dirs.Add($env:TEMP) }
if (Test-Path -LiteralPath $configPath) {
    try {
        $cfg = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
        if ($cfg.watch_dirs) { foreach ($d in $cfg.watch_dirs) { $dirs.Add($d) } }
    } catch { }
}
$dirs = $dirs | Select-Object -Unique

$global:watchers = @()
foreach ($dir in $dirs) {
    if (Test-Path -LiteralPath $dir) {
        $w = New-Object System.IO.FileSystemWatcher
        $w.Path = $dir
        $w.IncludeSubdirectories = $true
        $w.NotifyFilter = [System.IO.NotifyFilters]::FileName
        $w.EnableRaisingEvents = $true
        Register-ObjectEvent -InputObject $w -EventName Created -Action $fileAction | Out-Null
        Register-ObjectEvent -InputObject $w -EventName Renamed -Action $fileAction | Out-Null
        $global:watchers += $w
    }
}

Register-WmiEvent -Query "SELECT * FROM __InstanceCreationEvent WITHIN 2 WHERE TargetInstance ISA 'Win32_Process'" -SourceIdentifier "RiotProcMon" -Action $procAction | Out-Null

Add-Content -LiteralPath $logPath -Value ("[{0}] monitor iniciado (vigilancia por eventos) - pastas vigiadas: {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $global:watchers.Count)

function Test-AppVivo {
    try { $c = New-Object System.Net.Sockets.TcpClient; $c.Connect("127.0.0.1", $port); $c.Close(); return $true } catch { return $false }
}

while ($true) {
    Start-Sleep -Seconds 5
    if (-not (Test-AppVivo)) { break }
}

Add-Content -LiteralPath $logPath -Value ("[{0}] monitor encerrado" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
