$ErrorActionPreference = "Stop"
$hosts = Join-Path $env:WINDIR "System32\drivers\etc\hosts"
$markerIni = "# === GUARDIAO ANTI-RIOT ==="
$markerFim = "# === FIM GUARDIAO ANTI-RIOT ==="

$dominios = @(
  "riotgames.com","www.riotgames.com","auth.riotgames.com","entitlements.auth.riotgames.com",
  "clientconfig.rpg.riotgames.com","l3cdn.riotgames.com","lvp.riotgames.com","acs.riotgames.com",
  "riotcdn.net","riotcdn.com","playvalorant.com","www.playvalorant.com","valorant.com","www.valorant.com",
  "leagueoflegends.com","www.leagueoflegends.com","ddragon.leagueoflegends.com","lol.qq.com",
  "riftcdn.com","rdatasystems.com","valorant.secure.dyn.riotcdn.net","riot-client.secure.dyn.riotcdn.net",
  "riotgames.co","leagueoflegends.co.kr","teemo.gg","tracker.gg","op.gg"
)

$conteudo = Get-Content -LiteralPath $hosts -ErrorAction SilentlyContinue
$novo = New-Object System.Collections.Generic.List[string]
$dentro = $false
foreach ($linha in $conteudo) {
  if ($linha.Trim() -eq $markerIni) { $dentro = $true; continue }
  if ($linha.Trim() -eq $markerFim) { $dentro = $false; continue }
  if (-not $dentro) { $novo.Add($linha) }
}

$novo.Add($markerIni)
foreach ($d in $dominios) { $novo.Add("0.0.0.0 $d") }
$novo.Add($markerFim)

Set-Content -LiteralPath $hosts -Value $novo -Encoding ASCII
ipconfig /flushdns | Out-Null
Write-Host "Bloqueio de rede da Riot ATIVADO."
Start-Sleep -Seconds 2
