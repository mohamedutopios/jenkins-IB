#Requires -Version 5.1
# Cree dans le Gitea de la partie 1 le depot prive formation/library-api-devsecops et y pousse
# le projet library-api/ du kit (sans Jenkinsfile). Push force : ne pas relancer en cours de session.
# Usage : powershell -ExecutionPolicy Bypass -File .\scripts\init-depot.ps1
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
    param([Parameter(Mandatory)][string]$Uri, [switch]$Auth)
    try {
        $p = @{ Uri = $Uri; Method = 'Get'; UseBasicParsing = $true; TimeoutSec = 10 }
        if ($Auth) { $p.Headers = $script:Headers }
        Invoke-WebRequest @p | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Invoke-GiteaApi {
    param(
        [Parameter(Mandatory)][string]$Method,
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][hashtable]$Body
    )
    $bytes = [Text.Encoding]::UTF8.GetBytes(($Body | ConvertTo-Json -Compress))
    Invoke-RestMethod -Uri "$script:Gitea$Path" -Method $Method -Headers $script:Headers `
        -ContentType 'application/json; charset=utf-8' -Body $bytes -UseBasicParsing | Out-Null
}

foreach ($cmd in 'docker', 'git') {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { throw "Commande introuvable dans le PATH : $cmd" }
}

$KitRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $KitRoot
$Work = $null
try {
    # Chargement du .env (equivalent de : set -a; . ./.env; set +a)
    $envFile = Join-Path (Split-Path -Parent $KitRoot) '1-demos-jenkins-ci/.env'
    if (-not (Test-Path -LiteralPath $envFile)) { throw "Fichier .env introuvable : $envFile" }
    foreach ($line in Get-Content -LiteralPath $envFile) {
        $l = $line.Trim()
        if ($l -eq '' -or $l.StartsWith('#')) { continue }
        if ($l -match '^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            $name = $Matches[1]
            $value = $Matches[2].Trim()
            if ($value -match '^"([^"]*)"\s*(#.*)?$' -or $value -match "^'([^']*)'\s*(#.*)?$") { $value = $Matches[1] }
            else { $value = $value -replace '\s+#.*$', '' }
            Set-Item -Path "Env:$name" -Value $value
        }
    }
    foreach ($v in 'GITEA_PORT', 'GITEA_ADMIN_USER', 'GITEA_ADMIN_PASSWORD', 'GITEA_ADMIN_EMAIL') {
        if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($v))) { throw "Variable absente du .env : $v" }
    }

    $Port  = $env:GITEA_PORT
    $User  = $env:GITEA_ADMIN_USER
    $Pass  = $env:GITEA_ADMIN_PASSWORD
    $Email = $env:GITEA_ADMIN_EMAIL
    $Depot = 'library-api-devsecops'

    $script:Gitea   = "http://localhost:$Port"
    $basic          = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("${User}:${Pass}"))
    $script:Headers = @{ Authorization = "Basic $basic" }

    Write-Host "Attente de Gitea sur $script:Gitea..."
    $deadline = (Get-Date).AddMinutes(5)
    while (-not (Test-GiteaUrl -Uri "$script:Gitea/api/healthz")) {
        if ((Get-Date) -gt $deadline) { throw "Gitea ne repond pas sur $script:Gitea apres 5 minutes" }
        Start-Sleep -Seconds 2
    }

    if (-not (Test-GiteaUrl -Uri "$script:Gitea/api/v1/user" -Auth)) {
        throw "Gitea ne repond pas sur $script:Gitea avec le compte $User : la stack de la partie 1 tourne-t-elle ?"
    }

    if (-not (Test-GiteaUrl -Uri "$script:Gitea/api/v1/repos/$User/$Depot" -Auth)) {
        Invoke-GiteaApi -Method Post -Path '/api/v1/user/repos' -Body @{
            name           = $Depot
            private        = $true
            default_branch = 'main'
            description    = 'library-api : demos Jenkinsfile DevSecOps'
        }
        Write-Host "Depot $User/$Depot cree (prive)"
    }

    # Copie de travail temporaire : le dossier library-api/ du kit reste intact
    $src = Join-Path $KitRoot 'library-api'
    if (-not (Test-Path -LiteralPath $src -PathType Container)) { throw "Dossier introuvable : $src" }
    $Work = Join-Path ([IO.Path]::GetTempPath()) ('library-api-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $Work | Out-Null
    Get-ChildItem -LiteralPath $src -Force | Copy-Item -Destination $Work -Recurse -Force

    Push-Location -LiteralPath $Work
    try {
        $gitId = @('-c', 'user.name=Formation', '-c', "user.email=$Email", '-c', 'core.autocrlf=false')
        Invoke-Native -FilePath 'git' -Description 'git init' -ArgumentList @('init', '-q', '-b', 'main')
        Invoke-Native -FilePath 'git' -Description 'git add' -ArgumentList ($gitId + @('add', '.'))

        # Windows ne conserve pas le bit executable : on le force dans l'index pour mvnw et *.sh
        $execFiles = @(git ls-files | Where-Object { $_ -match '(^|/)(mvnw|gradlew)$' -or $_ -like '*.sh' })
        if ($execFiles.Count -gt 0) {
            Invoke-Native -FilePath 'git' -Description 'git update-index --chmod=+x' `
                -ArgumentList (@('update-index', '--chmod=+x', '--') + $execFiles)
        }

        Invoke-Native -FilePath 'git' -Description 'git commit' `
            -ArgumentList ($gitId + @('commit', '-q', '-m', 'library-api : version initiale (demos DevSecOps)'))

        $pushUrl = 'http://{0}:{1}@localhost:{2}/{3}/{4}.git' -f `
            [uri]::EscapeDataString($User), [uri]::EscapeDataString($Pass), $Port, $User, $Depot
        Invoke-Native -FilePath 'git' -Description "git push vers $script:Gitea/$User/$Depot.git" `
            -ArgumentList @('push', '-q', '--force', $pushUrl, 'main')
    } finally {
        Pop-Location
    }

    Write-Host "Projet pousse : $script:Gitea/$User/$Depot"
} finally {
    if ($Work -and (Test-Path -LiteralPath $Work)) { Remove-Item -LiteralPath $Work -Recurse -Force }
    Pop-Location
}
