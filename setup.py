import os
import subprocess

def main():
    print("==================================================")
    print("  Capstone Project I - Mutual Fund Analytics")
    print("  Day 1 Setup Script (Python)")
    print("==================================================")

    # 1. Create folders
    print("\n[1/5] Creating folder structure...")
    folders = ["data/raw", "data/processed", "notebooks", "sql", "dashboard", "reports"]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    print("  [OK] Folders created: " + ", ".join(folders))

    # 2. Create .gitignore
    print("\n[2/5] Creating .gitignore...")
    gitignore_content = """# Python
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

# Data - keep raw CSVs but ignore large processed files
data/processed/*.csv

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
"""
    with open(".gitignore", "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    print("  [OK] .gitignore created")

    # 3. Install dependencies
    print("\n[3/5] Installing Python dependencies...")
    if os.path.exists("requirements.txt"):
        try:
            subprocess.run(["pip", "install", "-r", "requirements.txt", "--quiet"], check=True)
            print("  [OK] All packages installed")
        except Exception as e:
            print(f"  [WARNING] Failed to install dependencies: {e}")
    else:
        print("  [WARNING] requirements.txt not found. Skipping dependency installation.")

    # 4. Initialize Git
    print("\n[4/5] Initializing Git repository...")
    if not os.path.exists(".git"):
        try:
            subprocess.run(["git", "init"], check=True)
            print("  [OK] Git initialized")
        except Exception as e:
            print(f"  [WARNING] Failed to initialize Git: {e}")
    else:
        print("  (Git already initialized, skipping)")

    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Day 1: Project structure and configuration"], check=True)
        print("  [OK] Initial commit made")
    except Exception as e:
        print(f"  [WARNING] Failed to commit: {e}")

    print("\n==================================================")
    print("  Setup complete! Next steps:")
    print("  1. Place your 10 CSV files inside data/raw/")
    print("  2. python data_ingestion.py")
    print("  3. python live_nav_fetch.py")
    print("  4. git add . && git commit -m 'Day 1: Data ingestion complete'")
    print("==================================================")

if __name__ == "__main__":
    main()
