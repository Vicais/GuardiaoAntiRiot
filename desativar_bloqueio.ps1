$ErrorActionPreference = "Stop"
$hosts = Join-Path $env:WINDIR "System32\drivers\etc\hosts"
$markerIni = "# === GUARDIAO ANTI-RIOT ==="
$markerFim = "# === FIM GUARDIAO ANTI-RIOT ==="

$conteudo = Get-Content -LiteralPath $hosts -ErrorAction SilentlyContinue
$novo = New-Object System.Collections.Generic.List[string]
$dentro = $false
foreach ($linha in $conteudo) {
  if ($linha.Trim() -eq $markerIni) { $dentro = $true; continue }
  if ($linha.Trim() -eq $markerFim) { $dentro = $false; continue }
  if (-not $dentro) { $novo.Add($linha) }
}

Set-Content -LiteralPath $hosts -Value $novo -Encoding ASCII
ipconfig /flushdns | Out-Null
Write-Host "Bloqueio de rede da Riot DESATIVADO."
Start-Sleep -Seconds 2
