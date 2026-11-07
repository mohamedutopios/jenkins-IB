#Requires -Version 5.1
# Genere la paire de cles SSH controller -> agent et la reporte dans .env
# Usage : powershell -ExecutionPolicy Bypass -File .\scripts\gen-agent-key-v1.ps1
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Get-Command 'ssh-keygen' -ErrorAction SilentlyContinue)) {
    throw "ssh-keygen introuvable dans le PATH (Windows : Parametres > Applications > Fonctionnalites facultatives > Client OpenSSH)"
}

$KitRoot = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $KitRoot
try {
    $keysDir = Join-Path $KitRoot 'keys'
    $priv    = Join-Path $keysDir 'jenkins_agent'
    $pubFile = "$priv.pub"
    $envFile = Join-Path $KitRoot '.env'
    $envTmp  = "$envFile.tmp"

    if (-not (Test-Path -LiteralPath $envFile)) { throw "Fichier .env introuvable : $envFile" }

    if (-not (Test-Path -LiteralPath $priv)) {
        New-Item -ItemType Directory -Path $keysDir -Force | Out-Null
        # Start-Process transmet la ligne de commande brute : -N "" (passphrase vide) passe
        # correctement sous PowerShell 5.1 comme 7.x
        $out = [IO.Path]::GetTempFileName()
        try {
            $proc = Start-Process -FilePath 'ssh-keygen' -NoNewWindow -Wait -PassThru `
                -RedirectStandardOutput $out `
                -ArgumentList "-q -t ed25519 -N `"`" -C `"jenkins-controller`" -f `"$priv`""
            if ($proc.ExitCode -ne 0) { throw "Echec ssh-keygen (code $($proc.ExitCode))" }
        } finally {
            Remove-Item -LiteralPath $out -Force -ErrorAction SilentlyContinue
        }
        Write-Host "Cle generee : keys/jenkins_agent (privee) et keys/jenkins_agent.pub"
    }

    if (-not (Test-Path -LiteralPath $pubFile)) { throw "Cle publique introuvable : $pubFile" }
    $pub = ([IO.File]::ReadAllText($pubFile)).Trim()

    # Remplace la ligne JENKINS_AGENT_SSH_PUBKEY= ; .env reecrit en UTF-8 sans BOM, fins de ligne LF
    $lines = @([IO.File]::ReadAllLines($envFile) | Where-Object { $_ -notmatch '^JENKINS_AGENT_SSH_PUBKEY=' })
    $lines += "JENKINS_AGENT_SSH_PUBKEY=`"$pub`""
    [IO.File]::WriteAllText($envTmp, (($lines -join "`n") + "`n"), (New-Object Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $envTmp -Destination $envFile -Force
    Write-Host "Cle publique reportee dans .env"
} finally {
    Pop-Location
}
