"""
Script to launch the Streamlit EduHyperRAG Web Application.
"""

import os
import sys
from pathlib import Path
from app.views.auth_view import render_auth_view

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def main():
    app_path = project_root / "app" / "main.py"
    print(f"Launching Streamlit EduHyperRAG UI from {app_path}...")
    os.system(f"streamlit run {app_path}")

if __name__ == "__main__":
    main()
