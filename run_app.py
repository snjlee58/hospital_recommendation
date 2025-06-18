#!/usr/bin/env python3
"""
Hospital Recommendation AI Service Runner
"""
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.main import main

if __name__ == "__main__":
    main() 