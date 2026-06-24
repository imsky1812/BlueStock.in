#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# setup.sh — Capstone Project I: Mutual Fund Analytics (Day 1)
# Run this ONCE to initialize the project and git repository.
# Usage: bash setup.sh
# ─────────────────────────────────────────────────────────────────

set -e   # exit on first error

PROJECT_NAME="mutual-fund-analytics"
GITHUB_USER="your-github-username"   # ← change this

echo "=================================================="
echo "  Capstone Project I — Mutual Fund Analytics"
echo "  Day 1 Setup Script"
echo "=================================================="

# 1. Create folder structure
echo ""
echo "[1/5] Creating folder structure…"
mkdir -p data/raw data/processed notebooks sql dashboard reports
echo "  ✓ Folders created: data/raw  data/processed  notebooks  sql  dashboard  reports"

# 2. Create .gitignore
echo ""
echo "[2/5] Creating .gitignore…"
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
env/
venv/
.venv/
pip-log.txt
.eggs/
*.egg-info/

# Jupyter
.ipynb_checkpoints/
*.ipynb_checkpoints

# Data — keep raw CSVs but ignore large processed files
data/processed/*.csv

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
EOF
echo "  ✓ .gitignore created"

# 3. Install dependencies
echo ""
echo "[3/5] Installing Python dependencies…"
pip install -r requirements.txt --quiet
echo "  ✓ All packages installed"

# 4. Initialize Git
echo ""
echo "[4/5] Initializing Git repository…"
if [ ! -d ".git" ]; then
    git init
    echo "  ✓ Git initialized"
else
    echo "  (Git already initialized, skipping)"
fi

git add .
git commit -m "Day 1: Project structure and configuration"
echo "  ✓ Initial commit made"

# 5. Remote setup instructions
echo ""
echo "[5/5] Push to GitHub (run these manually):"
echo "  git remote add origin https://github.com/${GITHUB_USER}/${PROJECT_NAME}.git"
echo "  git branch -M main"
echo "  git push -u origin main"

echo ""
echo "=================================================="
echo "  Setup complete! Next steps:"
echo "  1. Place your 10 CSV files inside  data/raw/"
echo "  2. python data_ingestion.py"
echo "  3. python live_nav_fetch.py"
echo "  4. git add . && git commit -m 'Day 1: Data ingestion complete'"
echo "=================================================="
