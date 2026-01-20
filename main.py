#!/usr/bin/env python3
"""
Main entry point for the Call Graph Visualizer application.

Usage:
    python main.py [filename.c]
    
If a filename is provided, it will be automatically loaded and visualized.
Otherwise, use the "Open C File" button to select a file.
"""

import sys
from call_graph_visualizer import main

if __name__ == "__main__":
    main()
