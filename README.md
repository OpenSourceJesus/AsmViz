# Call Graph Visualizer

A PyQt5-based application for visualizing call graphs of C source files using pycparser.

## Features

- Parse C source files and extract function definitions and calls
- Interactive graph visualization with draggable nodes
- Automatic circular layout of function nodes
- Visual representation of function call relationships with arrows

## Requirements

- Python 3.6+
- pycparser
- PyQt5

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

Note: pycparser requires a C preprocessor. On Linux, you typically need `gcc` or `clang` installed. On Windows, you may need to install MinGW or use the `cpp` argument.

## Usage

Run the application with a C file:
```bash
python main.py example.c
```

Or run without arguments and use the GUI:
```bash
python main.py
```

Or directly:
```bash
python call_graph_visualizer.py [filename.c]
```

### Using the Application

1. **Command-line**: Pass a C file as an argument to automatically load and visualize it
   ```bash
   python main.py your_file.c
   ```

2. **GUI**: Click "Open C File" to select a C source file
3. The call graph will be automatically extracted and displayed
4. Use "Auto Layout" to reorganize the graph in a circular layout
5. Drag nodes to manually reposition them
6. Click "Clear" to remove the current graph

## Example

The visualizer will show:
- **Blue circles**: Function definitions
- **Dashed arrows**: Function calls (from caller to callee)
- **Node labels**: Function names

## How It Works

1. **call_graph_extractor.py**: Uses pycparser to parse C files and extract:
   - Function definitions
   - Function calls within each function
   - Builds a call graph data structure

2. **call_graph_visualizer.py**: PyQt5 GUI that:
   - Loads C files and extracts call graphs
   - Displays functions as nodes and calls as edges
   - Provides interactive visualization

## Limitations

- Only processes single C files (not multi-file projects)
- Requires C preprocessor for pycparser
- Function pointer calls may not be fully resolved
- Recursive calls are shown but may create visual clutter

## Troubleshooting

If you encounter parsing errors:
- Ensure your C file is valid C code
- Make sure a C preprocessor (cpp) is available
- Check that all necessary headers are accessible
