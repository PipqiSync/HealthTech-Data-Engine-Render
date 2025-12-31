#!/bin/bash
git init
git add .
git commit -m "Deploy Build v0.1"
git branch -M main
# Run the line below once manually before running this script:
# git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main