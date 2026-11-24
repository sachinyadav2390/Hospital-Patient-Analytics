# ==============================================================================
# Hospital Patient Analytics - GitHub & Cloud Deployment Automation Script
# ==============================================================================

param (
    [string]$RepoUrl = ""
)

Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host "   HOSPITAL PATIENT ANALYTICS — GITHUB & CLOUD DEPLOYMENT WIZARD" -ForegroundColor Cyan
Write-Host "==========================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verify Git Status
$currentBranch = git branch --show-current
Write-Host "[1/4] Current active Git branch: $currentBranch" -ForegroundColor Green

# 2. Check Remote
$existingRemote = git remote get-url origin 2>$null

if (-not [string]::IsNullOrWhiteSpace($existingRemote)) {
    Write-Host "[2/4] Remote 'origin' detected: $existingRemote" -ForegroundColor Green
    $remoteToUse = $existingRemote
} elseif (-not [string]::IsNullOrWhiteSpace($RepoUrl)) {
    Write-Host "[2/4] Setting remote 'origin' to: $RepoUrl" -ForegroundColor Green
    git remote add origin $RepoUrl
    $remoteToUse = $RepoUrl
} else {
    Write-Host "[2/4] No remote 'origin' configured yet." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Please create a new repository on GitHub (https://github.com/new) named:" -ForegroundColor White
    Write-Host "  Hospital-Patient-Analytics" -ForegroundColor Cyan
    Write-Host ""
    $inputUrl = Read-Host "Paste your GitHub Repository URL (e.g. https://github.com/USERNAME/Hospital-Patient-Analytics.git)"
    if ([string]::IsNullOrWhiteSpace($inputUrl)) {
        Write-Host "Aborted: No repository URL provided." -ForegroundColor Red
        exit 1
    }
    git remote add origin $inputUrl
    $remoteToUse = $inputUrl
}

# 3. Push to GitHub
Write-Host ""
Write-Host "[3/4] Pushing code to GitHub ($remoteToUse)..." -ForegroundColor Cyan
git push -u origin $currentBranch

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "==========================================================================" -ForegroundColor Green
    Write-Host "SUCCESSFULLY UPLOADED TO GITHUB!" -ForegroundColor Green
    Write-Host "==========================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "[4/4] Next Deployment Steps:" -ForegroundColor White
    Write-Host ""
    Write-Host "A. Streamlit Community Cloud (Interactive App):" -ForegroundColor Cyan
    Write-Host "   1. Visit https://share.streamlit.io"
    Write-Host "   2. Click 'New App' and select your GitHub repository."
    Write-Host "   3. Main file path: app.py"
    Write-Host "   4. Click 'Deploy' -> Your interactive dashboard is live online!"
    Write-Host ""
    Write-Host "B. GitHub Pages (Static Showcase Report):" -ForegroundColor Cyan
    Write-Host "   1. Go to your repo on GitHub: Settings -> Pages"
    Write-Host "   2. Under 'Build and deployment', set Source to 'Deploy from a branch'"
    Write-Host "   3. Branch: $currentBranch, Folder: /docs -> Click Save"
    Write-Host "   4. Your site will be live at: https://<username>.github.io/<repo-name>/"
    Write-Host ""
    Write-Host "C. GitHub Actions CI/CD:" -ForegroundColor Cyan
    Write-Host "   - Automated tests are already running in the 'Actions' tab."
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "Push failed. If you need authentication, you can run:" -ForegroundColor Yellow
    Write-Host "  git push -u origin $currentBranch" -ForegroundColor White
    Write-Host "and sign in when prompted by the GitHub Credential Manager." -ForegroundColor Yellow
}
