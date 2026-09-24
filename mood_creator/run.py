#!/usr/bin/env python3
"""
Root entry point for launching Windows 11 Automation Hub.
"""
import sys
from pathlib import Path

# Ensure root directory is on python path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.main import main

if __name__ == "__main__":
    main()
