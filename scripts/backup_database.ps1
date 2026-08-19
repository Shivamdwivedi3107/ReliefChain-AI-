# ==============================================================================
# ReliefChain AI — Windows PowerShell Database Backup Script
# ==============================================================================
# Safe database backup script supporting PowerShell environments.
# Never automatically overwrites existing production backups.
# ==============================================================================

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = Join-Path $PSScriptRoot "..\backups"

if (-not (Test-Path $backupDir)) {
    New-Item -ItemType Directory -Path $backupDir | Out-Null
}

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "🛡️ ReliefChain AI Database Backup System (Windows PowerShell)" -ForegroundColor Cyan
Write-Host "Timestamp: $timestamp" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan

$dbPath = Join-Path $PSScriptRoot "..\reliefchain.db"

if (Test-Path $dbPath) {
    $backupFile = Join-Path $backupDir "reliefchain_sqlite_$timestamp.db"
    Write-Host "📦 Copying SQLite database to $backupFile..." -ForegroundColor Yellow
    Copy-Item -Path $dbPath -Destination $backupFile -Force
    
    $hash = (Get-FileHash -Path $backupFile -Algorithm SHA256).Hash
    $hashFile = "$backupFile.sha256"
    "$hash  $(Split-Path $backupFile -Leaf)" | Out-File -FilePath $hashFile -Encoding utf8
    
    Write-Host "✅ Backup completed successfully: $backupFile" -ForegroundColor Green
    Write-Host "🔒 SHA-256 Hash: $hash" -ForegroundColor Green
} else {
    Write-Host "⚠️ Notice: Running python backup script fallback..." -ForegroundColor Yellow
    py -3 (Join-Path $PSScriptRoot "..\backups\backup.py")
}
