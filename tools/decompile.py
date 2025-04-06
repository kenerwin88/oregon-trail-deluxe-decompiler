#!/usr/bin/env python3
"""
DOS Executable Decompiler

A tool for decompiling DOS executables.
"""

import sys
import os

# Add the parent directory to the path so we can import the decompiler package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.decompiler.main import main

if __name__ == "__main__":
    main()
