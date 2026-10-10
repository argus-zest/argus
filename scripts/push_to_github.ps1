<#
.SYNOPSIS
    Push both Argus (Backend + Desktop) and Argus Mobile to your GitHub Organization.
.PARAMETER OrgName
    The name of your GitHub Organization (e.g. argus-zest).
#>
param (
    [Parameter(Mandatory = $true)]
    [string]$OrgName
)

$ErrorActionPreference = "Continue"

function Configure-And-Push ($repoDir, $repoName) {
    Write-Host "`nConfiguring and pushing $repoName..." -ForegroundColor Yellow
    Set-Location $repoDir

    # Ensure on main branch
    git branch -M main

    # Set or update remote origin
    $remoteUrl = "https://github.com/$OrgName/$repoName.git"
    $remotes = git remote
    if ($remotes -contains "origin") {
        git remote set-url origin $remoteUrl
    } else {
        git remote add origin $remoteUrl
    }

    Write-Host "Pushing main branch to $remoteUrl..." -ForegroundColor Green
    git push -u origin main
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Pushing Argus Spaces to GitHub Organization: $OrgName" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Push Core Argus (Backend + Desktop)
Configure-And-Push "c:\Users\Dell\Downloads\argus" "argus"

# 2. Push Argus Mobile
Configure-And-Push "c:\Users\Dell\Downloads\argus-mobile" "argus-mobile"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  SUCCESS! Both repositories are live in your GitHub Org:" -ForegroundColor Green
Write-Host "  1. https://github.com/$OrgName/argus" -ForegroundColor Green
Write-Host "  2. https://github.com/$OrgName/argus-mobile" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
