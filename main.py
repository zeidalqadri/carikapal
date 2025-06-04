#!/usr/bin/env python3
"""
Main entry point for Carikapal OSV Discovery System
Railway deployment optimized
"""

import os
import sys
from pathlib import Path

# Add sckr directory to Python path
sys.path.append(str(Path(__file__).parent / "sckr"))

from production_server import main

if __name__ == "__main__":
    main()