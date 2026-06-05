#!/usr/bin/env python3
"""
Main entry point for the Call Graph Visualizer application.

Usage:
    python main.py [filename.c|directory]
    python main.py [filename.c|directory] -pdf
    python main.py binary1.so binary2.so -pdf

If a filename or directory is provided, it will be automatically loaded and visualized.
Use -pdf to generate a side-by-side assembly PDF instead of the GUI:
  one path compares GCC vs the c-compiler for C sources;
  two paths compare objdump disassembly for ELF binaries (e.g. shared libraries).
Otherwise, use the "Open File/Directory" button to select a file or directory.
"""

import sys


def _parse_args(argv):
    pdf_mode = '-pdf' in argv
    positional = [arg for arg in argv if arg != '-pdf']
    return positional, pdf_mode


def main():
    positional, pdf_mode = _parse_args(sys.argv[1:])

    if pdf_mode:
        if not positional:
            print(
                'Usage:\n'
                '  python main.py [filename.c|directory] -pdf\n'
                '  python main.py binary1.so binary2.so -pdf',
                file=sys.stderr,
            )
            sys.exit(1)
        if len(positional) > 2:
            print(
                'Usage:\n'
                '  python main.py [filename.c|directory] -pdf\n'
                '  python main.py binary1.so binary2.so -pdf',
                file=sys.stderr,
            )
            sys.exit(1)

        from assembly_pdf import main_pdf_cli

        try:
            main_pdf_cli(*positional)
        except ValueError as exc:
            print(f'Error: {exc}', file=sys.stderr)
            sys.exit(1)
        except (FileNotFoundError, RuntimeError) as exc:
            print(f'Error: {exc}', file=sys.stderr)
            sys.exit(1)
        return

    from call_graph_visualizer import main as gui_main

    if positional:
        sys.argv = [sys.argv[0], positional[0]]
    else:
        sys.argv = [sys.argv[0]]
    gui_main()


if __name__ == '__main__':
    main()
