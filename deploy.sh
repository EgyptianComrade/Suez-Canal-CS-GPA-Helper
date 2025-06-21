#!/bin/bash

# Suez University GPA Calculator - Deployment Script
echo "🚀 Deploying Suez University GPA Calculator to GitHub..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not found. Please initialize git first:"
    echo "   git init"
    echo "   git remote add origin https://github.com/EgyptianComrade/Suez-Canal-CS-GPA-Helper.git"
    exit 1
fi

# Add all files
echo "📁 Adding files to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "🚀 Deploy GPA Calculator with GitHub Actions and Pages

- Added GitHub Action for easy online usage
- Created beautiful GitHub Pages website
- Added data validation script
- Improved documentation and user experience
- Added MIT License
- Enhanced README with clear instructions"

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin main

echo "✅ Deployment complete!"
echo ""
echo "🎉 Your GPA Calculator is now live at:"
echo "   Repository: https://github.com/EgyptianComrade/Suez-Canal-CS-GPA-Helper"
echo "   Website: https://egyptiancomrade.github.io/Suez-Canal-CS-GPA-Helper/"
echo "   Actions: https://github.com/EgyptianComrade/Suez-Canal-CS-GPA-Helper/actions"
echo ""
echo "📋 Next steps:"
echo "   1. Enable GitHub Pages in repository settings (Source: GitHub Actions)"
echo "   2. Test the GitHub Action by running it manually"
echo "   3. Share the repository with other students!" 