# PowerShell script to push Suntech project to GitHub
# Make sure you have created the repository on GitHub first at: https://github.com/new
# Repository name should be: Suntech

Write-Host "Pushing Suntech project to GitHub..." -ForegroundColor Green

# Check if remote already exists
$remoteExists = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Remote 'origin' already exists. Removing it..." -ForegroundColor Yellow
    git remote remove origin
}

# Add remote (replace 'shafiqnik' with your GitHub username if different)
Write-Host "Adding remote repository..." -ForegroundColor Cyan
git remote add origin https://github.com/shafiqnik/Suntech.git

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
git branch -M main
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSuccessfully pushed to GitHub!" -ForegroundColor Green
    Write-Host "Repository URL: https://github.com/shafiqnik/Suntech" -ForegroundColor Cyan
} else {
    Write-Host "`nError: Failed to push. Make sure:" -ForegroundColor Red
    Write-Host "1. The repository 'Suntech' exists on GitHub" -ForegroundColor Yellow
    Write-Host "2. You have push access to the repository" -ForegroundColor Yellow
    Write-Host "3. You are authenticated (use: git config credential.helper store)" -ForegroundColor Yellow
}



