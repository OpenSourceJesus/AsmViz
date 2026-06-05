# Assembly & Call Graph Visualizer

A PyQt5-based application for visualizing call graphs and assembly code of C source files. Supports single files, multi-file projects, assembly files, and side-by-side assembly PDF export.

## Features

### Core Functionality
- **Call Graph Extraction**: Parse C source files and extract function definitions and calls using pycparser
- **Assembly Code Extraction**: Automatically extract assembly code for each function using `gcc -S`, `clang -S`, or the custom c-compiler
- **Multi-File Support**: Process entire directories or multiple files at once
- **Assembly File Support**: Direct parsing of `.s` and `.S` assembly files
- **Linker Script Detection**: Automatically finds and recognizes `.ld` linker scripts
- **PDF Export**: Generate side-by-side assembly comparison PDFs from the command line

### Visualization
- **Interactive Graph**: Draggable function nodes with automatic circular layout
- **Assembly Display**: View assembly code for each function with syntax highlighting
- **Code Toggle**: Click on function nodes to toggle between assembly and C code views
- **Compiler Selection**: Compare assembly from GCC, Clang, or the custom c-compiler in the GUI
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
- fpdf2 >= 2.7.0 (for `-pdf` export)
- GCC or Clang (for assembly extraction and C preprocessing)
- binutils (`objdump`) for binary library PDF comparison
- Custom c-compiler (optional; required for `@c-compiler` assembly and the right column of C-source PDFs)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: pycparser requires a C preprocessor. On Linux, you typically need `gcc` or `clang` installed. On Windows, you may need to install MinGW or use the `cpp` argument.

### Custom c-compiler

AsmViz looks for the custom c-compiler automatically in this order:

1. `C_COMPILER` or `ASMVIZ_C_COMPILER` environment variable
2. `AsmViz/c-compiler/compiler.py`
3. `~/C-Compiler/compiler.py`
4. `../C-Compiler/compiler.py` (sibling of AsmViz)

Example:

```bash
export C_COMPILER=~/C-Compiler
```

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

### PDF Export

Pass `-pdf` to generate a landscape PDF and open it in your default viewer instead of launching the GUI. The `-pdf` flag can appear before or after the file paths.

Compare GCC and the custom c-compiler assembly for a C file or directory:
```bash
python main.py example.c -pdf
python main.py /path/to/project/ -pdf
```

Compare disassembly of two ELF binaries side by side (shared libraries, executables, object files):
```bash
python main.py /tmp/musl.so ~/musl/lib/libc.so -pdf
python main.py -pdf binary1.so binary2.so
```

**Output files:**
- Single C file: `example_assembly.pdf` next to the source file
- Directory: `project_assembly.pdf` next to the directory
- Two binaries: `left_vs_right_assembly.pdf` next to the first binary

For large binaries such as full `libc.so` files, PDF generation can take several minutes and produce a very large file.

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
   - **Compiler Selection**: Use the compiler dropdown to switch between GCC, Clang, and `@c-compiler`
   - **Auto Layout**: Use "Auto Layout" button (if available) to reorganize nodes in a circular layout

4. **Clear**: Remove the current graph to load a new one

## Project Structure

- **`main.py`**: Entry point for the application and `-pdf` export
- **`call_graph_visualizer.py`**: PyQt5 GUI application with interactive visualization
- **`call_graph_extractor.py`**: Extracts call graph from C source files using pycparser
- **`assembly_extractor.py`**: Extracts assembly from C sources, locates the c-compiler, and disassembles ELF binaries
- **`assembly_pdf.py`**: Generates side-by-side assembly comparison PDFs
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
   - Compiles C files with `gcc -S`, `clang -S`, or the custom c-compiler to generate assembly
   - Parses assembly files to extract function definitions and their code
   - Maps assembly code to corresponding C functions
   - Disassembles ELF binaries with `objdump -d` for PDF comparison

4. **Visualization** (`call_graph_visualizer.py`):
   - Creates interactive PyQt5 graphics scene
   - Displays functions as nodes with signature, registers, and code
   - Draws edges (arrows) between functions showing call relationships
   - Provides pan, zoom, and drag interactions

5. **PDF Export** (`assembly_pdf.py`):
   - C source mode: places GCC assembly in the left column and c-compiler assembly in the right column
   - Binary mode: places `objdump` output for the first file in the left column and the second file in the right column
   - Opens the finished PDF with the system default viewer

## Example Output

The visualizer displays:
- **Function Nodes**: Rectangular nodes showing:
  - Function signature (top, orange/blue)
  - Register usage from call graph (middle section)
  - Function-specific register usage (middle section)
  - Assembly code or C code (bottom, clickable to toggle)
- **Arrows**: Dashed lines with arrowheads showing function calls (caller → callee)
- **Color Coding**: Assembly instructions are color-coded for better readability

PDF export produces a landscape two-column document with monospace assembly text.

## Supported File Types

- **`.c`**: C source files (parsed for call graph and assembly extraction)
- **`.s`**: Assembly files (lowercase, raw assembly)
- **`.S`**: Assembly files (uppercase, preprocessed assembly)
- **`.ld`**: Linker scripts (detected but not processed)
- **ELF binaries**: Shared libraries (`.so`), executables, and object files (`.o`) for `-pdf` binary comparison

## Limitations

- Function pointer calls may not be fully resolved in the call graph
- Recursive calls are shown but may create visual clutter in large graphs
- Assembly extraction requires GCC/Clang to be available in PATH
- Very large projects may have performance issues
- Assembly-only files (without corresponding C source) won't have call graph information
- Binary PDF comparison aligns disassembly line-by-line, not by function name
- Large shared libraries can produce very large PDFs and take a long time to generate

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
- If the c-compiler column shows `; c-compiler not found`, set `C_COMPILER` or install the compiler at `~/C-Compiler`

### PDF Export Issues
- Ensure `fpdf2` is installed: `pip install -r requirements.txt`
- Binary comparison requires `objdump` from binutils
- Both paths in binary mode must be existing ELF files
- PDF output is written next to the input file(s); make sure that directory is writable
- For very large binaries, expect long runtimes and large output files

### Display Issues
- Large graphs may be slow to render - try using "Auto Layout" to optimize
- If nodes overlap, use "Auto Layout" or manually drag them apart
- Zoom out if the graph appears too large

## Test Files

The `Tests/` directory contains various test cases:
- **`comprehensive_test/`**: Multi-file test suite with various C features
- **`bare_metal_os_test/`**: Bare metal OS example with C, assembly, and linker script
- Individual test files for specific features
