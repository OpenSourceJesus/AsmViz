# Assembly & Call Graph Visualizer

A PyQt5-based application for visualizing call graphs and assembly code of C source files. Supports single files, multi-file projects, and assembly files.

## Features

### Core Functionality
- **Call Graph Extraction**: Parse C source files and extract function definitions and calls using pycparser
- **Assembly Code Extraction**: Automatically extract assembly code for each function using `gcc -S`
- **Multi-File Support**: Process entire directories or multiple files at once
- **Assembly File Support**: Direct parsing of `.s` and `.S` assembly files
- **Linker Script Detection**: Automatically finds and recognizes `.ld` linker scripts

### Visualization
- **Interactive Graph**: Draggable function nodes with automatic circular layout
- **Assembly Display**: View assembly code for each function with syntax highlighting
- **Code Toggle**: Click on function nodes to toggle between assembly and C code views
- **Register Analysis**: Automatically extracts and displays register usage information
- **Color-Coded Assembly**: Syntax highlighting for assembly instructions, registers, and labels
- **Visual Call Relationships**: Arrows showing function call relationships (caller → callee)

### User Interface
- **Pan & Zoom**: Pan with left/right/middle mouse button, zoom with mouse wheel
- **Auto Layout**: Automatically organize nodes in a circular layout with optimal spacing
- **Manual Positioning**: Drag nodes to manually reposition them
- **File Browser**: Open single files or entire directories through the GUI

## Requirements

- Python 3.6+
- pycparser >= 2.21
- PyQt5 >= 5.15.0
- GCC or Clang (for assembly extraction and C preprocessing)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: pycparser requires a C preprocessor. On Linux, you typically need `gcc` or `clang` installed. On Windows, you may need to install MinGW or use the `cpp` argument.

## Usage

### Command-Line Usage

Run the application with a C file:
```bash
python main.py example.c
```

Run with a directory (processes all C and assembly files):
```bash
python main.py /path/to/project/
```

Run without arguments and use the GUI:
```bash
python main.py
```

Or run the visualizer directly:
```bash
python call_graph_visualizer.py [filename.c|directory]
```

### Using the Application

1. **Opening Files/Directories**:
   - **Command-line**: Pass a C file or directory as an argument to automatically load and visualize it
   - **GUI**: Click "Open File/Directory" button, then choose:
     - "Select File" to open a single C or assembly file
     - "Select Directory" to process all source files in a directory

2. **Viewing the Graph**:
   - Function nodes are displayed with:
     - **Top section**: Function signature
     - **Middle sections**: Register usage information
     - **Bottom section**: Assembly code (click to toggle to C code view)
   - **Arrows**: Show function call relationships (from caller to callee)

3. **Interacting with the Graph**:
   - **Pan**: Click and drag with left, right, or middle mouse button
   - **Zoom**: Use mouse wheel to zoom in/out
   - **Move Nodes**: Click and drag function nodes to reposition them
   - **Toggle Code View**: Click on the code section of a function node to switch between assembly and C code
   - **Auto Layout**: Use "Auto Layout" button (if available) to reorganize nodes in a circular layout

4. **Clear**: Remove the current graph to load a new one

## Project Structure

- **`main.py`**: Entry point for the application
- **`call_graph_visualizer.py`**: PyQt5 GUI application with interactive visualization
- **`call_graph_extractor.py`**: Extracts call graph from C source files using pycparser
- **`assembly_extractor.py`**: Extracts assembly code for functions using `gcc -S`
- **`file_finder.py`**: Utility to find C files, assembly files, and linker scripts in directories

## How It Works

1. **File Discovery** (`file_finder.py`):
   - Recursively searches directories for `.c`, `.s`, `.S`, and `.ld` files
   - Handles both single files and directory structures

2. **Call Graph Extraction** (`call_graph_extractor.py`):
   - Uses pycparser to parse C files and extract:
     - Function definitions
     - Function calls within each function
     - Builds a call graph data structure mapping callers to callees

3. **Assembly Extraction** (`assembly_extractor.py`):
   - Compiles C files with `gcc -S` to generate assembly
   - Parses assembly files to extract function definitions and their code
   - Maps assembly code to corresponding C functions

4. **Visualization** (`call_graph_visualizer.py`):
   - Creates interactive PyQt5 graphics scene
   - Displays functions as nodes with signature, registers, and code
   - Draws edges (arrows) between functions showing call relationships
   - Provides pan, zoom, and drag interactions

## Example Output

The visualizer displays:
- **Function Nodes**: Rectangular nodes showing:
  - Function signature (top, orange/blue)
  - Register usage from call graph (middle section)
  - Function-specific register usage (middle section)
  - Assembly code or C code (bottom, clickable to toggle)
- **Arrows**: Dashed lines with arrowheads showing function calls (caller → callee)
- **Color Coding**: Assembly instructions are color-coded for better readability

## Supported File Types

- **`.c`**: C source files (parsed for call graph and assembly extraction)
- **`.s`**: Assembly files (lowercase, raw assembly)
- **`.S`**: Assembly files (uppercase, preprocessed assembly)
- **`.ld`**: Linker scripts (detected but not processed)

## Limitations

- Function pointer calls may not be fully resolved in the call graph
- Recursive calls are shown but may create visual clutter in large graphs
- Assembly extraction requires GCC/Clang to be available in PATH
- Very large projects may have performance issues
- Assembly-only files (without corresponding C source) won't have call graph information

## Troubleshooting

### Parsing Errors
- Ensure your C file is valid C code
- Make sure a C preprocessor (`cpp`) is available
- Check that all necessary headers are accessible
- For multi-file projects, ensure all dependencies are in the same directory or accessible

### Assembly Extraction Issues
- Verify that `gcc` or `clang` is installed and in your PATH
- Check that the C files compile successfully
- Assembly extraction may fail for files with compilation errors

### Display Issues
- Large graphs may be slow to render - try using "Auto Layout" to optimize
- If nodes overlap, use "Auto Layout" or manually drag them apart
- Zoom out if the graph appears too large

## Test Files

The `Tests/` directory contains various test cases:
- **`comprehensive_test/`**: Multi-file test suite with various C features
- **`bare_metal_os_test/`**: Bare metal OS example with C, assembly, and linker script
- Individual test files for specific features
