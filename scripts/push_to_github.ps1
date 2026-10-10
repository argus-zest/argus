<#
.SYNOPSIS
    Push both Argus (Backend + Desktop) and Argus Mobile to your GitHub Organization.
.PARAMETER OrgName
    The name of your GitHub Organization (e.g. argus-delhi or argus-intelligence).
#>
param (
    [Parameter(Mandatory = $true)]
    [string]$OrgName
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Pushing Argus Spaces to GitHub Organization: $OrgName" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Push Core Argus (Backend + Desktop)
Write-Host "`n[1/2] Configuring and pushing Core Argus (Backend & Desktop)..." -ForegroundColor Yellow
$coreDir = "c:\Users\Dell\Downloads\argus"
Set-Location $coreDir
git branch -M main

$coreRemote = "https://github.com/$OrgName/argus.git"
git remote remove origin 2>$null
git remote add origin $coreRemote
Write-Host "Pushing main branch to $coreRemote..." -ForegroundColor Green
git push -u origin main

# 2. Push Argus Mobile
Write-Host "`n[2/2] Configuring and pushing Argus Mobile..." -ForegroundColor Yellow
$mobileDir = "c:\Users\Dell\Downloads\argus-mobile"
Set-Location $mobileDir
git branch -M main

$mobileRemote = "https://github.com/$OrgName/argus-mobile.git"
git remote remove origin 2>$null
git remote add origin $mobileRemote
Write-Host "Pushing main branch to $mobileRemote..." -ForegroundColor Green
git push -u origin main

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  SUCCESS! Both repositories are live in your GitHub Org:" -ForegroundColor Green
Write-Host "  1. https://github.com/$OrgName/argus" -ForegroundColor Green
Write-Host "  2. https://github.com/$OrgName/argus-mobile" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
