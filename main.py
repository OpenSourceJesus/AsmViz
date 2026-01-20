#!/usr/bin/env python3
"""
Main entry point for the Call Graph Visualizer application.

Usage:
    python main.py [filename.c|directory]
    
If a filename or directory is provided, it will be automatically loaded and visualized.
Otherwise, use the "Open File/Directory" button to select a file or directory.
"""

import sys
from call_graph_visualizer import main

if __name__ == "__main__":
    main()
