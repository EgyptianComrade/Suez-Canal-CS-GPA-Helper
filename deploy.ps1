# Suez University GPA Calculator - Deployment Script (PowerShell)
Write-Host "🚀 Deploying Suez University GPA Calculator to GitHub..." -ForegroundColor Green

# Check if git is initialized
if (-not (Test-Path ".git")) {
    Write-Host "❌ Git repository not found. Please initialize git first:" -ForegroundColor Red
    Write-Host "   git init" -ForegroundColor Yellow
    Write-Host "   git remote add origin https://github.com/EgyptianComrade/Suez-Canal-CS-GPA-Helper.git" -ForegroundColor Yellow
    exit 1
}

# Add all files
Write-Host "📁 Adding files to git..." -ForegroundColor Blue
git add .

# Commit changes
Write-Host "💾 Committing changes..." -ForegroundColor Blue
git commit -m "🚀 Deploy GPA Calculator with GitHub Actions and Pages

- Added GitHub Action for easy online usage
- Created beautiful GitHub Pages website
- Added data validation script
- Improved documentation and user experience
- Added MIT License
- Enhanced README with clear instructions"

# Push to GitHub
Write-Host "📤 Pushing to GitHub..." -ForegroundColor Blue
git push origin main

Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🎉 Your GPA Calculator is now live at:" -ForegroundColor Cyan
Write-Host "   Repository: https://github.com/EgyptianComrade/Suez-Canal-CS-GPA-Helper" -ForegroundColor Yellow
Write-Host "   Website: https://egyptiancomrade.github.io/Suez-Canal-CS-GPA-Helper/" -ForegroundColor Yellow
Write-Host "   Actions: https://github.com/EgyptianComrade/Suez-Canal-CS-GPA-Helper/actions" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Enable GitHub Pages in repository settings (Source: GitHub Actions)" -ForegroundColor White
Write-Host "   2. Test the GitHub Action by running it manually" -ForegroundColor White
Write-Host "   3. Share the repository with other students!" -ForegroundColor White 