#Requires -Version 5.1
# Cree le depot prive formation/inventaire-api dans Gitea et y pousse le projet du TP.
# Le compte Gitea est celui du kit (cree par ..\scripts\init-gitea.ps1 a la demo 0).
# Usage : powershell -ExecutionPolicy Bypass -File .\init-inventaire-api.ps1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

function Invoke-Native {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$Description
    )
    $eap = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $FilePath @ArgumentList } finally { $ErrorActionPreference = $eap }
    if ($LASTEXITCODE -ne 0) { throw "Echec ($LASTEXITCODE) : $Description" }
}

function Test-GiteaUrl {
    param([Parameter(Mandatory)][string]$Uri)
    try {
        Invoke-WebRequest -Uri $Uri -Headers $script:Headers -UseBasicParsing -TimeoutSec 10 | Out-Null
        return $true
    } catch {
        return $false
    }
}

if (-not (Get-Command 'git' -ErrorAction SilentlyContinue)) { throw "Commande introuvable dans le PATH : git" }

$TpRoot  = $PSScriptRoot
$envFile = Join-Path (Split-Path -Parent $TpRoot) '.env'
if (-not (Test-Path -LiteralPath $envFile)) { throw "Fichier .env du kit introuvable : $envFile" }

# Chargement du .env du kit (GITEA_PORT, GITEA_ADMIN_USER...)
$vars = @{}
foreach ($line in Get-Content -LiteralPath $envFile) {
    $l = $line.Trim()
    if ($l -eq '' -or $l.StartsWith('#')) { continue }
    if ($l -match '^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"?([^"]*)"?\s*$') { $vars[$Matches[1]] = $Matches[2] }
}

$Port  = $vars['GITEA_PORT']
$User  = $vars['GITEA_ADMIN_USER']
$Pass  = $vars['GITEA_ADMIN_PASSWORD']
$Email = $vars['GITEA_ADMIN_EMAIL']
$Gitea = if ($env:GITEA_URL) { $env:GITEA_URL } else { "http://localhost:$Port" }
$HostPort = $Gitea -replace '^http://', ''

$basic = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${User}:${Pass}"))
$script:Headers = @{ Authorization = "Basic $basic" }

if (-not (Test-GiteaUrl -Uri "$Gitea/api/v1/user")) {
    throw "Compte $User refuse par $Gitea : lancer d'abord ..\scripts\init-gitea.ps1"
}

if (-not (Test-GiteaUrl -Uri "$Gitea/api/v1/repos/$User/inventaire-api")) {
    $body = @{ name = 'inventaire-api'; private = $true; default_branch = 'main'; description = 'API de gestion de stock (TP Jenkins Maven)' }
    $bytes = [Text.Encoding]::UTF8.GetBytes(($body | ConvertTo-Json -Compress))
    Invoke-RestMethod -Uri "$Gitea/api/v1/user/repos" -Method Post -Headers $script:Headers `
        -ContentType 'application/json; charset=utf-8' -Body $bytes -UseBasicParsing | Out-Null
    Write-Host "Depot $User/inventaire-api cree (prive)"
}

# Copie de travail temporaire : le dossier inventaire-api\ du kit reste intact
$Work = Join-Path ([IO.Path]::GetTempPath()) ('inventaire-api-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Work | Out-Null
try {
    Get-ChildItem -LiteralPath (Join-Path $TpRoot 'inventaire-api') -Force | Copy-Item -Destination $Work -Recurse -Force
    Push-Location -LiteralPath $Work
    try {
        $gitId = @('-c', 'user.name=Formation', '-c', "user.email=$Email", '-c', 'core.autocrlf=false')
        Invoke-Native -FilePath 'git' -Description 'git init' -ArgumentList @('init', '-q', '-b', 'main')
        Invoke-Native -FilePath 'git' -Description 'git add' -ArgumentList ($gitId + @('add', '.'))
        # Windows ne conserve pas le bit executable : mvnw doit l'avoir sur l'agent Linux
        Invoke-Native -FilePath 'git' -Description 'git update-index --chmod=+x mvnw' `
            -ArgumentList @('update-index', '--chmod=+x', '--', 'mvnw')
        Invoke-Native -FilePath 'git' -Description 'git commit' `
            -ArgumentList ($gitId + @('commit', '-q', '-m', 'inventaire-api : version initiale'))
        $pushUrl = 'http://{0}:{1}@{2}/{3}/inventaire-api.git' -f `
            [uri]::EscapeDataString($User), [uri]::EscapeDataString($Pass), $HostPort, $User
        Invoke-Native -FilePath 'git' -Description "git push vers $Gitea/$User/inventaire-api.git" `
            -ArgumentList @('push', '-q', '--force', $pushUrl, 'main')
    } finally {
        Pop-Location
    }
    Write-Host "Projet pousse : $Gitea/$User/inventaire-api"
} finally {
    Remove-Item -LiteralPath $Work -Recurse -Force -ErrorAction SilentlyContinue
}
