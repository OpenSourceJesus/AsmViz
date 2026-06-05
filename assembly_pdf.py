"""
Generate side-by-side assembly comparison PDFs.
"""

import os
import subprocess
import sys
import tempfile
from itertools import zip_longest
from pathlib import Path

from fpdf import FPDF

from assembly_extractor import (
    compile_c_to_assembly_text,
    disassemble_binary_to_file,
    get_all_subdirectories,
    is_elf_binary,
)
from file_finder import find_source_files

MAX_INCLUDE_DIRS = 256
FONT = 'Courier'
FONT_SIZE = 6
LINE_HEIGHT = 2.8
MARGIN = 8
HEADER_HEIGHT = 14
COL_GAP = 2


class AssemblyComparisonPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L', unit='mm', format='A4')
        self.set_auto_page_break(auto=False)
        self.set_margins(MARGIN, MARGIN, MARGIN)


def _sanitize_line(line, max_chars):
    if line is None:
        return ''
    line = line.replace('\t', '    ')
    line = line.rstrip('\r\n')
    if len(line) > max_chars:
        return line[: max_chars - 3] + '...'
    return line


def _split_lines(text):
    if not text:
        return ['']
    return text.replace('\r\n', '\n').replace('\r', '\n').split('\n')


def _column_width(pdf):
    usable = pdf.w - 2 * MARGIN - COL_GAP
    return usable / 2


def _content_bottom(pdf):
    return pdf.h - MARGIN


def _chars_per_column(pdf):
    col_w = _column_width(pdf)
    return max(32, int(col_w / (FONT_SIZE * 0.45)))


def _start_page(pdf, title, left_header, right_header):
    pdf.add_page()
    pdf.set_font(FONT, 'B', 9)
    pdf.set_xy(MARGIN, MARGIN)
    pdf.cell(0, 5, title, ln=True)

    col_w = _column_width(pdf)
    y = MARGIN + HEADER_HEIGHT - 4
    pdf.set_font(FONT, 'B', 7)
    pdf.set_xy(MARGIN, y)
    pdf.cell(col_w, 4, left_header, border=0)
    pdf.set_xy(MARGIN + col_w + COL_GAP, y)
    pdf.cell(col_w, 4, right_header, border=0)
    return y + 5


def _write_two_column_lines(pdf, y_start, left_lines, right_lines):
    col_w = _column_width(pdf)
    bottom = _content_bottom(pdf)
    max_lines = max(len(left_lines), len(right_lines))
    y = y_start
    pdf.set_font(FONT, '', FONT_SIZE)

    for i in range(max_lines):
        if y + LINE_HEIGHT > bottom:
            y = _start_page(
                pdf,
                pdf._continued_title,
                pdf._left_header,
                pdf._right_header,
            )

        left = left_lines[i] if i < len(left_lines) else ''
        right = right_lines[i] if i < len(right_lines) else ''

        pdf.set_xy(MARGIN, y)
        pdf.cell(col_w, LINE_HEIGHT, left, border=0)
        pdf.set_xy(MARGIN + col_w + COL_GAP, y)
        pdf.cell(col_w, LINE_HEIGHT, right, border=0)
        y += LINE_HEIGHT

    return y + 4


def _write_two_column_streams(pdf, y_start, left_path, right_path, max_chars):
    col_w = _column_width(pdf)
    bottom = _content_bottom(pdf)
    y = y_start
    pdf.set_font(FONT, '', FONT_SIZE)

    with open(left_path, 'r', encoding='utf-8', errors='replace') as left_file, open(
        right_path, 'r', encoding='utf-8', errors='replace'
    ) as right_file:
        for left_line, right_line in zip_longest(left_file, right_file, fillvalue=''):
            if y + LINE_HEIGHT > bottom:
                y = _start_page(
                    pdf,
                    pdf._continued_title,
                    pdf._left_header,
                    pdf._right_header,
                )

            left = _sanitize_line(left_line, max_chars)
            right = _sanitize_line(right_line, max_chars)

            pdf.set_xy(MARGIN, y)
            pdf.cell(col_w, LINE_HEIGHT, left, border=0)
            pdf.set_xy(MARGIN + col_w + COL_GAP, y)
            pdf.cell(col_w, LINE_HEIGHT, right, border=0)
            y += LINE_HEIGHT

    return y + 4


def _resolve_c_input(path):
    """Resolve CLI path to C files and include directories."""
    path = os.path.abspath(path)
    include_dirs = []

    if os.path.isdir(path):
        c_files, _, _ = find_source_files(path)
        include_dirs = get_all_subdirectories(path)[:MAX_INCLUDE_DIRS]
        display_name = os.path.basename(path)
    elif path.endswith('.c') and os.path.isfile(path):
        c_files = [path]
        file_dir = os.path.dirname(path)
        if file_dir:
            include_dirs = [file_dir]
        display_name = os.path.basename(path)
    else:
        raise ValueError(f"Expected a .c file or directory, got: {path}")

    if not c_files:
        raise ValueError(f"No C files found in: {path}")

    return sorted(c_files), include_dirs, display_name


def _resolve_binary_paths(left_path, right_path):
    left_path = os.path.abspath(os.path.expanduser(left_path))
    right_path = os.path.abspath(os.path.expanduser(right_path))

    for path in (left_path, right_path):
        if not os.path.isfile(path):
            raise ValueError(f"File not found: {path}")
        if not is_elf_binary(path):
            raise ValueError(f"Expected an ELF binary (.so, .o, executable): {path}")

    return left_path, right_path


def _default_output_path(input_path, suffix='_assembly.pdf'):
    abs_input = os.path.abspath(os.path.expanduser(input_path))
    if os.path.isdir(input_path):
        return abs_input.rstrip(os.sep) + suffix
    return os.path.join(os.path.dirname(abs_input), Path(input_path).stem + suffix)


def generate_assembly_comparison_pdf(input_path, output_path=None, optimization='O0'):
    """
    Build a PDF comparing GCC and c-compiler assembly for each C source file.

    Returns:
        str: Path to the generated PDF
    """
    c_files, include_dirs, _display_name = _resolve_c_input(input_path)

    if output_path is None:
        output_path = _default_output_path(input_path)

    output_path = os.path.abspath(output_path)
    pdf = AssemblyComparisonPDF()
    pdf._continued_title = ''
    pdf._left_header = 'GCC'
    pdf._right_header = 'c-compiler'
    max_chars = _chars_per_column(pdf)

    for c_file in c_files:
        rel_name = os.path.relpath(c_file, os.path.dirname(c_files[0]))
        if len(c_files) == 1:
            section_title = f'Assembly comparison: {os.path.basename(c_file)}'
        else:
            section_title = f'Assembly comparison: {rel_name}'

        gcc_asm = compile_c_to_assembly_text(
            c_file, compiler='gcc', optimization=optimization, include_dirs=include_dirs
        )
        custom_asm = compile_c_to_assembly_text(
            c_file, compiler='@c-compiler', include_dirs=include_dirs
        )

        left_lines = [_sanitize_line(line, max_chars) for line in _split_lines(gcc_asm)]
        right_lines = [_sanitize_line(line, max_chars) for line in _split_lines(custom_asm)]

        left_header = f'GCC (-{optimization})'
        right_header = 'c-compiler'

        pdf._continued_title = section_title + ' (continued)'
        pdf._left_header = left_header
        pdf._right_header = right_header

        y = _start_page(pdf, section_title, left_header, right_header)
        y = _write_two_column_lines(pdf, y, left_lines, right_lines)

        if c_file != c_files[-1] and y + 10 > _content_bottom(pdf):
            pdf.add_page()

    pdf.output(output_path)
    return output_path


def generate_binary_comparison_pdf(left_path, right_path, output_path=None):
    """
    Build a PDF comparing objdump disassembly for two ELF binaries side by side.

    Returns:
        str: Path to the generated PDF
    """
    left_path, right_path = _resolve_binary_paths(left_path, right_path)
    left_name = os.path.basename(left_path)
    right_name = os.path.basename(right_path)

    if output_path is None:
        left_stem = Path(left_path).stem
        right_stem = Path(right_path).stem
        output_path = os.path.join(
            os.path.dirname(left_path),
            f'{left_stem}_vs_{right_stem}_assembly.pdf',
        )

    output_path = os.path.abspath(output_path)
    temp_dir = tempfile.mkdtemp(prefix='asmviz_pdf_')
    left_dump = os.path.join(temp_dir, 'left.objdump')
    right_dump = os.path.join(temp_dir, 'right.objdump')

    try:
        print(f'Disassembling {left_name}...', file=sys.stderr)
        disassemble_binary_to_file(left_path, left_dump)
        print(f'Disassembling {right_name}...', file=sys.stderr)
        disassemble_binary_to_file(right_path, right_dump)

        pdf = AssemblyComparisonPDF()
        section_title = f'Assembly comparison: {left_name} vs {right_name}'
        left_header = left_path
        right_header = right_path
        pdf._continued_title = section_title + ' (continued)'
        pdf._left_header = left_header
        pdf._right_header = right_header

        max_chars = _chars_per_column(pdf)
        y = _start_page(pdf, section_title, left_header, right_header)
        print('Writing PDF...', file=sys.stderr)
        _write_two_column_streams(pdf, y, left_dump, right_dump, max_chars)
        pdf.output(output_path)
        return output_path
    finally:
        for path in (left_dump, right_dump):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                pass
        try:
            os.rmdir(temp_dir)
        except OSError:
            pass


def open_pdf(path):
    """Open a PDF with the system default viewer."""
    path = os.path.abspath(path)
    if sys.platform.startswith('linux'):
        subprocess.Popen(
            ['xdg-open', path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    elif sys.platform == 'darwin':
        subprocess.Popen(
            ['open', path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    elif sys.platform == 'win32':
        os.startfile(path)  # noqa: S606
    else:
        print(f"Generated PDF: {path}", file=sys.stderr)


def main_pdf_cli(*input_paths, output_path=None):
    """Generate and open an assembly comparison PDF."""
    if len(input_paths) == 2:
        pdf_path = generate_binary_comparison_pdf(
            input_paths[0], input_paths[1], output_path=output_path
        )
    elif len(input_paths) == 1:
        pdf_path = generate_assembly_comparison_pdf(
            input_paths[0], output_path=output_path
        )
    else:
        raise ValueError(
            'Expected one C source path or two ELF binary paths with -pdf'
        )

    print(f'Wrote {pdf_path}')
    open_pdf(pdf_path)
    return pdf_path
