"""
Call Graph Visualizer using PyQt5
Displays a call graph as an interactive graph visualization.
"""

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,
                             QGraphicsView, QGraphicsScene, QGraphicsRectItem,
                             QGraphicsTextItem, QGraphicsLineItem, QMessageBox)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QFont, QPen, QBrush, QColor, QPainter, QPainterPath, QMouseEvent, QWheelEvent
import sys
import math
from collections import defaultdict


class PanGraphicsView(QGraphicsView):
    """Custom QGraphicsView that supports panning with left, right, or middle mouse button."""
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.panning = False
        self.pan_button_pressed = False
        self.last_pan_point = QPointF()
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
    
    def mousePressEvent(self, event):
        """Handle mouse press events for panning."""
        # Check if left, right, or middle mouse button is pressed
        if event.button() in (Qt.LeftButton, Qt.RightButton, Qt.MiddleButton):
            # Store the button press but don't start panning yet
            # Panning will start when the mouse actually moves
            self.pan_button_pressed = True
            self.last_pan_point = event.pos()
            # Don't call super() to prevent default behavior
        else:
            # Let the parent handle other buttons
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for panning."""
        if self.pan_button_pressed:
            # Start panning if we haven't already and mouse has moved
            if not self.panning:
                # Check if mouse has moved enough to start panning (threshold of 3 pixels)
                delta = event.pos() - self.last_pan_point
                if abs(delta.x()) > 3 or abs(delta.y()) > 3:
                    self.panning = True
                    self.setCursor(Qt.ClosedHandCursor)
                    # Disable rubber band drag when panning
                    self.setDragMode(QGraphicsView.NoDrag)
            
            if self.panning:
                # Calculate the delta movement
                delta = event.pos() - self.last_pan_point
                self.last_pan_point = event.pos()
                
                # Scroll the view
                h_bar = self.horizontalScrollBar()
                v_bar = self.verticalScrollBar()
                h_bar.setValue(h_bar.value() - delta.x())
                v_bar.setValue(v_bar.value() - delta.y())
            else:
                # Mouse hasn't moved enough yet, let parent handle it
                super().mouseMoveEvent(event)
        else:
            # Let the parent handle normal mouse moves
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events to stop panning."""
        if event.button() in (Qt.LeftButton, Qt.RightButton, Qt.MiddleButton):
            if self.panning:
                # Restore rubber band drag mode
                self.setDragMode(QGraphicsView.RubberBandDrag)
            self.panning = False
            self.pan_button_pressed = False
            self.setCursor(Qt.ArrowCursor)
        else:
            # Let the parent handle other buttons
            super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Handle wheel events for zooming."""
        # Determine zoom factor based on scroll direction
        delta = event.angleDelta().y()
        if delta > 0:
            # Zoom in
            zoom_factor = 1.15
        else:
            # Zoom out
            zoom_factor = 1.0 / 1.15
        
        # Set transformation anchor to zoom towards the cursor position
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Apply zoom
        self.scale(zoom_factor, zoom_factor)
        
        # Reset transformation anchor to default
        self.setTransformationAnchor(QGraphicsView.AnchorViewCenter)


class FunctionNode(QGraphicsRectItem):
    """Represents a function node with signature and assembly body."""
    
    def __init__(self, name, signature, assembly, x, y, width=None, min_height=60, calls=None, function_info=None):
        # Calculate required width based on content
        if width is None:
            width = self.calculate_required_width(signature, assembly)
        
        # Extract registers
        self.calls = calls if calls is not None else {}
        self.function_info = function_info if function_info is not None else {}
        
        # Get registers used in this function
        func_registers = self.extract_registers_from_assembly(assembly)
        
        # Get registers used in function and its call graph (function's own + all callees)
        call_graph_registers = self.extract_registers_from_call_graph(name, assembly)
        # Include the function's own registers in the call graph list
        call_graph_registers.update(func_registers)
        
        # Format register displays with color-coding
        func_registers_text = self.format_registers(func_registers)
        call_graph_registers_text = self.format_registers(call_graph_registers)
        
        # Calculate required heights
        signature_height = self.calculate_text_height(signature, width - 10, 7, bold=True, is_html=False)
        
        # Calculate label heights
        label_height = self.calculate_text_height("Registers (function + call graph):", width - 10, 7, bold=True, is_html=False)
        label_height2 = self.calculate_text_height("Registers (function only):", width - 10, 7, bold=True, is_html=False)
        
        call_graph_registers_height = self.calculate_text_height(call_graph_registers_text, width - 10, 7, bold=False, is_html=True)
        func_registers_height = self.calculate_text_height(func_registers_text, width - 10, 7, bold=False, is_html=True)
        formatted_asm = self.format_assembly(assembly)
        assembly_height = self.calculate_text_height(formatted_asm, width - 10, 7, bold=False, is_html=True)
        
        # Set heights with more generous padding to prevent cutoff
        signature_rect_height = max(40, signature_height + 15)  # Min 40, or content + padding
        call_graph_registers_rect_height = max(50, label_height + call_graph_registers_height + 20)  # Min 50, or label + content + padding
        func_registers_rect_height = max(50, label_height2 + func_registers_height + 20)  # Min 50, or label + content + padding
        assembly_rect_height = max(60, assembly_height + 20)  # Min 60, or content + more padding
        
        total_height = signature_rect_height + call_graph_registers_rect_height + func_registers_rect_height + assembly_rect_height
        
        super().__init__(0, 0, width, total_height)
        self.name = name
        self.signature = signature
        self.assembly = assembly
        self.setPos(x, y)
        self.setPen(QPen(QColor(50, 100, 200), 2))
        self.setFlag(QGraphicsRectItem.ItemIsMovable, False)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        
        # Set rounded rectangle appearance
        self.setBrush(QBrush(QColor(100, 150, 255)))
        
        # Create four rectangles stacked vertically
        corner_radius = 10
        
        # Rectangle 1: Top rectangle (signature)
        y_offset = 0
        self.signature_rect = QRectF(0, y_offset, width, signature_rect_height)
        self.signature_brush = QBrush(QColor(80, 130, 235))
        
        # Rectangle 2: Registers in function + call graph
        y_offset += signature_rect_height
        self.call_graph_registers_rect = QRectF(0, y_offset, width, call_graph_registers_rect_height)
        self.call_graph_registers_brush = QBrush(QColor(90, 140, 245))
        
        # Rectangle 3: Registers in function only
        y_offset += call_graph_registers_rect_height
        self.func_registers_rect = QRectF(0, y_offset, width, func_registers_rect_height)
        self.func_registers_brush = QBrush(QColor(95, 145, 250))
        
        # Rectangle 4: Bottom rectangle (assembly) - dynamically sized
        y_offset += func_registers_rect_height
        self.body_rect = QRectF(0, y_offset, width, assembly_rect_height)
        self.body_brush = QBrush(QColor(100, 150, 255))
        
        # Add signature text
        self.signature_text = QGraphicsTextItem(self.format_signature(signature), self)
        self.signature_text.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Courier", 7)
        font.setBold(True)
        self.signature_text.setFont(font)
        self.signature_text.setPos(5, 5)
        self.signature_text.setTextWidth(width - 10)
        
        # Add call graph registers text with label
        y_offset = signature_rect_height
        label_text = QGraphicsTextItem("Registers (function + call graph):", self)
        label_text.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Courier", 7)
        font.setBold(True)
        label_text.setFont(font)
        label_text.setPos(5, y_offset + 5)
        label_text.setTextWidth(width - 10)
        
        self.call_graph_registers_text = QGraphicsTextItem(self)
        self.call_graph_registers_text.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Courier", 7)
        font.setBold(False)
        self.call_graph_registers_text.setFont(font)
        label_height = label_text.boundingRect().height()
        self.call_graph_registers_text.setPos(5, y_offset + 5 + label_height + 2)
        self.call_graph_registers_text.setTextWidth(width - 10)
        self.call_graph_registers_text.setHtml(call_graph_registers_text)
        self.call_graph_registers_text.setOpenExternalLinks(False)
        
        # Add function registers text with label
        y_offset += call_graph_registers_rect_height
        label_text2 = QGraphicsTextItem("Registers (function only):", self)
        label_text2.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Courier", 7)
        font.setBold(True)
        label_text2.setFont(font)
        label_text2.setPos(5, y_offset + 5)
        label_text2.setTextWidth(width - 10)
        
        self.func_registers_text = QGraphicsTextItem(self)
        self.func_registers_text.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Courier", 7)
        font.setBold(False)
        self.func_registers_text.setFont(font)
        label_height2 = label_text2.boundingRect().height()
        self.func_registers_text.setPos(5, y_offset + 5 + label_height2 + 2)
        self.func_registers_text.setTextWidth(width - 10)
        self.func_registers_text.setHtml(func_registers_text)
        self.func_registers_text.setOpenExternalLinks(False)
        
        # Add assembly text (using HTML for color-coding)
        y_offset += func_registers_rect_height
        self.assembly_text = QGraphicsTextItem(self)
        # Set default text color for non-register text
        self.assembly_text.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Courier", 7)
        self.assembly_text.setFont(font)
        self.assembly_text.setPos(5, y_offset + 5)
        self.assembly_text.setTextWidth(width - 10)
        
        # Set HTML content for color-coded assembly
        self.assembly_text.setHtml(formatted_asm)
        
        # Enable text wrapping and ensure it's visible
        self.assembly_text.setOpenExternalLinks(False)
        
        # After creating text items, check actual heights and adjust if needed
        # Use the text document's size which is more accurate for wrapped text
        assembly_doc = self.assembly_text.document()
        assembly_doc.setTextWidth(width - 10)
        actual_assembly_height = assembly_doc.size().height()
        
        # Calculate required height with padding
        required_assembly_height = actual_assembly_height + 25  # Add generous padding
        
        # If the actual required height is greater than what we allocated, adjust the rectangle
        if required_assembly_height > assembly_rect_height:
            # Update assembly rectangle height
            new_assembly_rect_height = required_assembly_height
            self.body_rect = QRectF(0, signature_rect_height + call_graph_registers_rect_height + func_registers_rect_height, width, new_assembly_rect_height)
            
            # Update total height and main rectangle
            new_total_height = signature_rect_height + call_graph_registers_rect_height + func_registers_rect_height + new_assembly_rect_height
            self.setRect(0, 0, width, new_total_height)
    
    def extract_registers_from_assembly(self, assembly):
        """Extract unique registers from assembly text."""
        import re
        
        if not assembly or assembly.strip() == "":
            return set()
        
        # Define register patterns (x86-64 registers)
        reg64 = r'\b(r8|r9|r10|r11|r12|r13|r14|r15|rax|rbx|rcx|rdx|rsi|rdi|rbp|rsp|rip)\b'
        reg32 = r'\b(eax|ebx|ecx|edx|esi|edi|ebp|esp|eip)\b'
        reg16 = r'\b(ax|bx|cx|dx|si|di|bp|sp|ip)\b'
        reg8 = r'\b(al|bl|cl|dl|ah|bh|ch|dh|sil|dil|bpl|spl|r8b|r9b|r10b|r11b|r12b|r13b|r14b|r15b)\b'
        reg_seg = r'\b(cs|ds|es|fs|gs|ss)\b'
        reg_simd = r'\b(xmm[0-9]+|ymm[0-9]+|zmm[0-9]+|mm[0-7])\b'
        reg_ctrl = r'\b(cr[0-9]+|dr[0-9]+)\b'
        
        all_regs = f'({reg64}|{reg32}|{reg16}|{reg8}|{reg_seg}|{reg_simd}|{reg_ctrl})'
        
        # Find all registers (case-insensitive)
        registers = set()
        for match in re.finditer(all_regs, assembly, re.IGNORECASE):
            reg = match.group(0).lower()
            registers.add(reg)
        
        return registers
    
    def extract_registers_from_call_graph(self, func_name, assembly):
        """Extract registers from all functions in the call graph (transitively)."""
        registers = set()
        
        # Recursively get all functions in the call graph (transitive closure)
        # Use a set to track visited functions to avoid infinite loops in cycles
        visited = set()
        
        def get_all_callees(func):
            """Recursively get all callees of a function."""
            if func in visited:
                return set()  # Already visited, avoid cycles
            visited.add(func)
            
            all_callees = set()
            called_functions = self.calls.get(func, set())
            for callee_name in called_functions:
                # Only include callees that are defined in our function_info
                if callee_name in self.function_info:
                    all_callees.add(callee_name)
                    # Recursively get callees of callees
                    recursive_callees = get_all_callees(callee_name)
                    all_callees.update(recursive_callees)
            
            return all_callees
        
        # Get all transitive callees
        all_callees = get_all_callees(func_name)
        
        # Extract registers from each called function's assembly
        for callee_name in all_callees:
            if callee_name in self.function_info:
                callee_assembly = self.function_info[callee_name].get('assembly', '')
                if callee_assembly and callee_assembly.strip():
                    callee_registers = self.extract_registers_from_assembly(callee_assembly)
                    registers.update(callee_registers)
        
        return registers
    
    def format_registers(self, registers):
        """Format registers with color-coding for display."""
        if not registers:
            return "No registers"
        
        # Sort registers for consistent display
        sorted_regs = sorted(registers)
        
        # Get color for each register using the same color scheme as assembly
        register_colors = {
            'a': '#FFFF00',      # Yellow for A registers
            'b': '#00FF00',      # Green for B registers
            'c': '#00FFFF',      # Cyan for C registers
            'd': '#FF00FF',      # Magenta for D registers
            'si': '#FF8000',     # Orange for SI registers
            'di': '#FF0080',     # Pink for DI registers
            'bp': '#80FF00',     # Lime for BP registers
            'sp': '#0080FF',     # Light blue for SP registers
            'ip': '#80FFFF',     # Light cyan for IP registers
            'r8': '#FF8080',     # Light red for R8 registers
            'r9': '#80FF80',     # Light green for R9 registers
            'r10': '#8080FF',    # Light blue for R10 registers
            'r11': '#FFFF80',    # Light yellow for R11 registers
            'r12': '#FF80FF',    # Light magenta for R12 registers
            'r13': '#80FFFF',    # Light cyan for R13 registers
            'r14': '#FFC080',    # Peach for R14 registers
            'r15': '#C0FF80',    # Light lime for R15 registers
            'seg': '#FF4040',    # Red-orange for segment registers
            'simd': '#40FF40',   # Bright green for SIMD registers
            'ctrl': '#4040FF',   # Blue for control/debug registers
        }
        
        def get_base_register(reg_name):
            """Get the base register name for color grouping."""
            reg_lower = reg_name.lower()
            
            if reg_lower in ['rax', 'eax', 'ax', 'al', 'ah']:
                return 'a'
            elif reg_lower in ['rbx', 'ebx', 'bx', 'bl', 'bh']:
                return 'b'
            elif reg_lower in ['rcx', 'ecx', 'cx', 'cl', 'ch']:
                return 'c'
            elif reg_lower in ['rdx', 'edx', 'dx', 'dl', 'dh']:
                return 'd'
            elif reg_lower in ['rsi', 'esi', 'si', 'sil']:
                return 'si'
            elif reg_lower in ['rdi', 'edi', 'di', 'dil']:
                return 'di'
            elif reg_lower in ['rbp', 'ebp', 'bp', 'bpl']:
                return 'bp'
            elif reg_lower in ['rsp', 'esp', 'sp', 'spl']:
                return 'sp'
            elif reg_lower in ['rip', 'eip', 'ip']:
                return 'ip'
            elif reg_lower in ['r8', 'r8b']:
                return 'r8'
            elif reg_lower in ['r9', 'r9b']:
                return 'r9'
            elif reg_lower in ['r10', 'r10b']:
                return 'r10'
            elif reg_lower in ['r11', 'r11b']:
                return 'r11'
            elif reg_lower in ['r12', 'r12b']:
                return 'r12'
            elif reg_lower in ['r13', 'r13b']:
                return 'r13'
            elif reg_lower in ['r14', 'r14b']:
                return 'r14'
            elif reg_lower in ['r15', 'r15b']:
                return 'r15'
            elif reg_lower in ['cs', 'ds', 'es', 'fs', 'gs', 'ss']:
                return 'seg'
            elif 'xmm' in reg_lower or 'ymm' in reg_lower or 'zmm' in reg_lower or 'mm' in reg_lower:
                return 'simd'
            elif reg_lower.startswith('cr') or reg_lower.startswith('dr'):
                return 'ctrl'
            else:
                return reg_lower
        
        # Format registers with color-coding
        formatted_regs = []
        for reg in sorted_regs:
            base_reg = get_base_register(reg)
            color = register_colors.get(base_reg, '#FFFF00')  # Default to yellow
            formatted_regs.append(f'<span style="color: {color}; font-weight: bold;">{reg}</span>')
        
        # Join with commas and spaces
        return ', '.join(formatted_regs)
    
    def calculate_required_width(self, signature, assembly):
        """Calculate the minimum width needed to fit signature and assembly without wrapping."""
        from PyQt5.QtGui import QFontMetrics
        
        # Use Courier font with size 7 to match the display font
        font = QFont("Courier", 7)
        font.setBold(True)
        metrics_bold = QFontMetrics(font)
        
        font.setBold(False)
        metrics_normal = QFontMetrics(font)
        
        max_width = 0
        
        # Check signature width (using bold metrics)
        signature_width = metrics_bold.width(signature)
        max_width = max(max_width, signature_width)
        
        # Check assembly width (using normal metrics)
        if assembly and assembly.strip():
            lines = assembly.split('\n')
            for line in lines:
                line_width = metrics_normal.width(line)
                max_width = max(max_width, line_width)
        else:
            # "No assembly available" text
            no_asm_width = metrics_normal.width("No assembly available")
            max_width = max(max_width, no_asm_width)
        
        # Add padding (10 pixels on each side = 20 total, plus a bit more for safety)
        return max_width + 30
    
    def calculate_text_height(self, text, text_width, font_size, bold=False, is_html=False):
        """Calculate the height needed to display text using QTextDocument for accuracy."""
        from PyQt5.QtGui import QTextDocument
        from PyQt5.QtCore import QSizeF
        
        # Use QTextDocument for accurate text measurement
        doc = QTextDocument()
        font = QFont("Courier", font_size)
        if bold:
            font.setBold(True)
        doc.setDefaultFont(font)
        
        # Check if text contains HTML tags or use the is_html flag
        if is_html or ('<' in text and '>' in text):
            doc.setHtml(text)
        else:
            doc.setPlainText(text)
        
        doc.setTextWidth(text_width)
        
        # Get the document size which accounts for wrapping
        doc_size = doc.size()
        return doc_size.height()
    
    def format_signature(self, signature):
        """Format signature text to fit in rectangle."""
        # No truncation needed - width is calculated dynamically
        return signature
    
    def format_assembly(self, assembly):
        """Format assembly text with color-coded instructions and registers."""
        if not assembly or assembly.strip() == "":
            return "No assembly available"
        
        # Color-code instructions and registers in the assembly text
        return self.color_code_assembly(assembly)
    
    def color_code_assembly(self, assembly):
        """Color-code registers in assembly text using HTML formatting.
        Related registers (e.g., rax, eax, ax, al) use the same color."""
        import re
        
        # Clean up assembly: remove function name, initial local labels, and file location annotations
        lines = assembly.split('\n')
        cleaned_lines = []
        skip_initial_labels = True  # Flag to skip initial local labels like .LFB
        function_name_removed = False  # Track if we've removed the function name
        
        for line in lines:
            stripped = line.strip()
            
            # Remove file location annotations (e.g., '@test_deep_call.s (7-8) ')
            if re.match(r'^@[^\s]+\.s\s+\(\d+-\d+\)', stripped):
                continue
            
            # Remove function name lines (e.g., 'func8:' or '    func8:') - only first occurrence
            if not function_name_removed and re.match(r'^\s*\w+\s*:', stripped):
                # Check if it's likely a function name (not a local label starting with .)
                label_name = stripped.split(':')[0].strip()
                if not label_name.startswith('.'):
                    # This is a function name, skip it
                    function_name_removed = True
                    continue
            
            # Remove initial local labels like .LFB0: (only at the beginning, before first non-label line)
            if skip_initial_labels:
                if re.match(r'^\s*\.LFB\d+\s*:', stripped):
                    continue
                # Once we've hit a non-empty line that's not a .LFB label, stop skipping .LFB labels
                if stripped and not re.match(r'^\s*\.LFB\d+\s*:', stripped):
                    skip_initial_labels = False
            
            # Keep all other lines (including .cfi directives and everything else)
            cleaned_lines.append(line)
        
        assembly = '\n'.join(cleaned_lines)
        
        # Map registers to their base register name for color grouping
        def get_base_register(reg_name):
            """Get the base register name for color grouping."""
            reg_lower = reg_name.lower()
            
            # General purpose registers - A register family
            if reg_lower in ['rax', 'eax', 'ax', 'al', 'ah']:
                return 'a'
            # General purpose registers - B register family
            elif reg_lower in ['rbx', 'ebx', 'bx', 'bl', 'bh']:
                return 'b'
            # General purpose registers - C register family
            elif reg_lower in ['rcx', 'ecx', 'cx', 'cl', 'ch']:
                return 'c'
            # General purpose registers - D register family
            elif reg_lower in ['rdx', 'edx', 'dx', 'dl', 'dh']:
                return 'd'
            # SI register family
            elif reg_lower in ['rsi', 'esi', 'si', 'sil']:
                return 'si'
            # DI register family
            elif reg_lower in ['rdi', 'edi', 'di', 'dil']:
                return 'di'
            # BP register family
            elif reg_lower in ['rbp', 'ebp', 'bp', 'bpl']:
                return 'bp'
            # SP register family
            elif reg_lower in ['rsp', 'esp', 'sp', 'spl']:
                return 'sp'
            # IP register family
            elif reg_lower in ['rip', 'eip', 'ip']:
                return 'ip'
            # R8 register family
            elif reg_lower in ['r8', 'r8b']:
                return 'r8'
            # R9 register family
            elif reg_lower in ['r9', 'r9b']:
                return 'r9'
            # R10 register family
            elif reg_lower in ['r10', 'r10b']:
                return 'r10'
            # R11 register family
            elif reg_lower in ['r11', 'r11b']:
                return 'r11'
            # R12 register family
            elif reg_lower in ['r12', 'r12b']:
                return 'r12'
            # R13 register family
            elif reg_lower in ['r13', 'r13b']:
                return 'r13'
            # R14 register family
            elif reg_lower in ['r14', 'r14b']:
                return 'r14'
            # R15 register family
            elif reg_lower in ['r15', 'r15b']:
                return 'r15'
            # Segment registers
            elif reg_lower in ['cs', 'ds', 'es', 'fs', 'gs', 'ss']:
                return 'seg'
            # SIMD registers (xmm, ymm, zmm, mm)
            elif re.match(r'^(xmm|ymm|zmm|mm)', reg_lower):
                return 'simd'
            # Control/debug registers
            elif re.match(r'^(cr|dr)', reg_lower):
                return 'ctrl'
            else:
                return reg_lower
        
        # Color palette for different register families (bright colors for visibility on blue background)
        register_colors = {
            'a': '#FFFF00',      # Yellow for A registers (rax, eax, ax, al, ah)
            'b': '#00FF00',      # Green for B registers (rbx, ebx, bx, bl, bh)
            'c': '#00FFFF',      # Cyan for C registers (rcx, ecx, cx, cl, ch)
            'd': '#FF00FF',      # Magenta for D registers (rdx, edx, dx, dl, dh)
            'si': '#FF8000',     # Orange for SI registers (rsi, esi, si, sil)
            'di': '#FF0080',     # Pink for DI registers (rdi, edi, di, dil)
            'bp': '#80FF00',     # Lime for BP registers (rbp, ebp, bp, bpl)
            'sp': '#0080FF',     # Light blue for SP registers (rsp, esp, sp, spl)
            'ip': '#80FFFF',     # Light cyan for IP registers (rip, eip, ip)
            'r8': '#FF8080',     # Light red for R8 registers
            'r9': '#80FF80',     # Light green for R9 registers
            'r10': '#8080FF',    # Light blue for R10 registers
            'r11': '#FFFF80',    # Light yellow for R11 registers
            'r12': '#FF80FF',    # Light magenta for R12 registers
            'r13': '#80FFFF',    # Light cyan for R13 registers
            'r14': '#FFC080',    # Peach for R14 registers
            'r15': '#C0FF80',    # Light lime for R15 registers
            'seg': '#FF4040',    # Red-orange for segment registers
            'simd': '#40FF40',   # Bright green for SIMD registers
            'ctrl': '#4040FF',   # Blue for control/debug registers
        }
        
        # Define register patterns (x86-64 registers)
        # General purpose 64-bit
        reg64 = r'\b(r8|r9|r10|r11|r12|r13|r14|r15|rax|rbx|rcx|rdx|rsi|rdi|rbp|rsp|rip)\b'
        # General purpose 32-bit
        reg32 = r'\b(eax|ebx|ecx|edx|esi|edi|ebp|esp|eip)\b'
        # General purpose 16-bit
        reg16 = r'\b(ax|bx|cx|dx|si|di|bp|sp|ip)\b'
        # General purpose 8-bit
        reg8 = r'\b(al|bl|cl|dl|ah|bh|ch|dh|sil|dil|bpl|spl|r8b|r9b|r10b|r11b|r12b|r13b|r14b|r15b)\b'
        # Segment registers
        reg_seg = r'\b(cs|ds|es|fs|gs|ss)\b'
        # MMX/SSE/AVX registers
        reg_simd = r'\b(xmm[0-9]+|ymm[0-9]+|zmm[0-9]+|mm[0-7])\b'
        # Control and debug registers
        reg_ctrl = r'\b(cr[0-9]+|dr[0-9]+)\b'
        
        # Combine all patterns
        all_regs = f'({reg64}|{reg32}|{reg16}|{reg8}|{reg_seg}|{reg_simd}|{reg_ctrl})'
        
        # Define instruction categories and colors
        instruction_categories = {
            # Data movement instructions
            'mov': ['mov', 'movq', 'movl', 'movw', 'movb', 'movsx', 'movzx', 'movsb', 'movsw', 'movsd', 'movsq', 'movss', 'movapd', 'movaps', 'movdqa', 'movdqu'],
            # Arithmetic instructions
            'arith': ['add', 'sub', 'mul', 'div', 'imul', 'idiv', 'inc', 'dec', 'neg', 'adc', 'sbb', 'addq', 'addl', 'addw', 'addb', 'subq', 'subl', 'subw', 'subb'],
            # Logical/bitwise instructions
            'logic': ['and', 'or', 'xor', 'not', 'test', 'andq', 'andl', 'andw', 'andb', 'orq', 'orl', 'orw', 'orb', 'xorq', 'xorl', 'xorw', 'xorb'],
            # Shift/rotate instructions
            'shift': ['shl', 'shr', 'sal', 'sar', 'rol', 'ror', 'rcl', 'rcr', 'shld', 'shrd', 'shlq', 'shlw', 'shlb', 'shrq', 'shrw', 'shrb'],
            # Comparison instructions
            'cmp': ['cmp', 'cmps', 'cmpsb', 'cmpsw', 'cmpsd', 'cmpsq', 'test', 'cmpq', 'cmpl', 'cmpw', 'cmpb'],
            # Control flow instructions
            'control': ['jmp', 'je', 'jz', 'jne', 'jnz', 'ja', 'jae', 'jb', 'jbe', 'jg', 'jge', 'jl', 'jle', 'jc', 'jnc', 'jo', 'jno', 'js', 'jns', 'jp', 'jnp', 'call', 'ret', 'retq', 'retl', 'retw', 'retb', 'iret', 'syscall', 'sysret'],
            # Stack instructions
            'stack': ['push', 'pop', 'pushq', 'pushl', 'pushw', 'pushb', 'popq', 'popl', 'popw', 'popb', 'pushf', 'popf', 'pusha', 'popa'],
            # String instructions
            'string': ['movs', 'movsb', 'movsw', 'movsd', 'movsq', 'lods', 'lodsb', 'lodsw', 'lodsd', 'lodsq', 'stos', 'stosb', 'stosw', 'stosd', 'stosq', 'scas', 'scasb', 'scasw', 'scasd', 'scasq', 'rep', 'repe', 'repz', 'repne', 'repnz'],
            # Flag instructions
            'flags': ['clc', 'stc', 'cmc', 'cld', 'std', 'cli', 'sti', 'lahf', 'sahf'],
            # Other common instructions
            'other': ['lea', 'nop', 'hlt', 'int', 'into', 'bound', 'ud2', 'cpuid', 'rdtsc', 'rdtscp', 'pause', 'lfence', 'mfence', 'sfence', 'lock', 'xchg', 'xadd', 'cmpxchg', 'cmpxchg8b', 'cmpxchg16b', 'bswap', 'bsf', 'bsr', 'popcnt', 'tzcnt', 'lzcnt'],
        }
        
        # Color palette for instruction categories
        instruction_colors = {
            'mov': '#FF6B6B',      # Red for data movement
            'arith': '#4ECDC4',    # Teal for arithmetic
            'logic': '#95E1D3',    # Light teal for logical
            'shift': '#F38181',    # Light red for shift/rotate
            'cmp': '#AA96DA',      # Purple for comparison
            'control': '#FCBAD3',  # Pink for control flow
            'stack': '#FFD93D',     # Yellow for stack operations
            'string': '#6BCB77',   # Green for string operations
            'flags': '#FF9F43',    # Orange for flag operations
            'other': '#A8E6CF',    # Light green for other instructions
        }
        
        # Build instruction pattern (must be at start of line or after whitespace)
        all_instructions = []
        instruction_to_category = {}
        for category, inst_list in instruction_categories.items():
            for inst in inst_list:
                all_instructions.append(inst)
                instruction_to_category[inst.lower()] = category
        
        # Create pattern for instructions (word boundary, case insensitive)
        inst_pattern = r'\b(' + '|'.join(re.escape(inst) for inst in all_instructions) + r')\b'
        
        # Escape HTML special characters first
        html_assembly = assembly.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # First, color-code instructions (before registers to avoid conflicts)
        def replace_instruction(match):
            inst = match.group(0)
            inst_lower = inst.lower()
            category = instruction_to_category.get(inst_lower, 'other')
            color = instruction_colors.get(category, '#FFFFFF')
            return f'<span style="color: {color}; font-weight: bold;">{inst}</span>'
        
        # Apply instruction color-coding (case-insensitive)
        html_assembly = re.sub(inst_pattern, replace_instruction, html_assembly, flags=re.IGNORECASE)
        
        # Then, replace registers with colored versions
        def replace_register(match):
            reg = match.group(0)
            base_reg = get_base_register(reg)
            # Get color for this register family, default to yellow if not found
            color = register_colors.get(base_reg, '#FFFF00')
            return f'<span style="color: {color}; font-weight: bold;">{reg}</span>'
        
        # Apply register color-coding (case-insensitive)
        html_assembly = re.sub(all_regs, replace_register, html_assembly, flags=re.IGNORECASE)
        
        # Preserve line breaks by converting newlines to <br>
        html_assembly = html_assembly.replace('\n', '<br>')
        
        return html_assembly
    
    def paint(self, painter, option, widget=None):
        """Custom paint to draw rounded rectangles."""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw rectangle 1: signature
        path1 = QPainterPath()
        path1.addRoundedRect(self.signature_rect, 10, 10)
        painter.fillPath(path1, self.signature_brush)
        painter.strokePath(path1, self.pen())
        
        # Draw rectangle 2: call graph registers
        path2 = QPainterPath()
        path2.addRoundedRect(self.call_graph_registers_rect, 10, 10)
        painter.fillPath(path2, self.call_graph_registers_brush)
        painter.strokePath(path2, self.pen())
        
        # Draw rectangle 3: function registers
        path3 = QPainterPath()
        path3.addRoundedRect(self.func_registers_rect, 10, 10)
        painter.fillPath(path3, self.func_registers_brush)
        painter.strokePath(path3, self.pen())
        
        # Draw rectangle 4: assembly body
        path4 = QPainterPath()
        path4.addRoundedRect(self.body_rect, 10, 10)
        painter.fillPath(path4, self.body_brush)
        painter.strokePath(path4, self.pen())
        
        # Draw separator lines between rectangles
        painter.setPen(QPen(QColor(50, 100, 200), 1))
        separator_y1 = self.signature_rect.height()
        painter.drawLine(QPointF(0, separator_y1), 
                        QPointF(self.rect().width(), separator_y1))
        
        separator_y2 = separator_y1 + self.call_graph_registers_rect.height()
        painter.drawLine(QPointF(0, separator_y2), 
                        QPointF(self.rect().width(), separator_y2))
        
        separator_y3 = separator_y2 + self.func_registers_rect.height()
        painter.drawLine(QPointF(0, separator_y3), 
                        QPointF(self.rect().width(), separator_y3))
    
    def set_highlighted(self, highlighted):
        """Highlight or unhighlight the node."""
        if highlighted:
            self.signature_brush = QBrush(QColor(255, 150, 100))
            self.call_graph_registers_brush = QBrush(QColor(255, 140, 90))
            self.func_registers_brush = QBrush(QColor(255, 135, 85))
            self.body_brush = QBrush(QColor(255, 130, 80))
            self.setPen(QPen(QColor(255, 100, 50), 3))
        else:
            self.signature_brush = QBrush(QColor(80, 130, 235))
            self.call_graph_registers_brush = QBrush(QColor(90, 140, 245))
            self.func_registers_brush = QBrush(QColor(95, 145, 250))
            self.body_brush = QBrush(QColor(100, 150, 255))
            self.setPen(QPen(QColor(50, 100, 200), 2))
        self.update()


class CallGraphVisualizer(QMainWindow):
    """Main window for the call graph visualizer."""
    
    def __init__(self, filename=None):
        super().__init__()
        self.functions = {}
        self.calls = defaultdict(set)
        self.function_info = {}  # function_name -> {'signature': str, 'assembly': str}
        self.nodes = {}  # function_name -> FunctionNode
        self.edges = []  # List of (caller, callee) tuples
        self.edge_items = []  # List of QGraphicsItem for edges (lines and arrows)
        self.current_filename = None
        self.init_ui()
        
        # Load file if provided
        if filename:
            self.load_file(filename)
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Call Graph Visualizer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        self.open_button = QPushButton("Open C File")
        self.open_button.clicked.connect(self.open_file)
        control_layout.addWidget(self.open_button)
        
        control_layout.addStretch()
        
        self.status_label = QLabel("No file loaded")
        control_layout.addWidget(self.status_label)
        
        main_layout.addLayout(control_layout)
        
        # Graphics view
        self.scene = QGraphicsScene()
        self.view = PanGraphicsView(self.scene)
        main_layout.addWidget(self.view)
    
    def load_file(self, filename):
        """Load a C file and extract the call graph."""
        try:
            from call_graph_extractor import extract_call_graph
            from assembly_extractor import get_function_info
            
            self.current_filename = filename
            self.functions, self.calls = extract_call_graph(filename)
            
            # Extract function signatures and assembly
            self.function_info = get_function_info(filename, self.functions)
            
            self.status_label.setText(f"Loaded: {filename} ({len(self.functions)} functions)")
            self.draw_graph()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse file:\n{str(e)}")
    
    def open_file(self):
        """Open a C file dialog and load the selected file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open C File", "", "C Files (*.c);;All Files (*)"
        )
        
        if filename:
            self.load_file(filename)
    
    def clear_graph(self):
        """Clear the current graph."""
        self.scene.clear()
        self.nodes = {}
        self.edges = []
        self.edge_items = []
        self.functions = {}
        self.calls = defaultdict(set)
        self.function_info = {}
        self.current_filename = None
        self.status_label.setText("No file loaded")
    
    def draw_graph(self):
        """Draw the call graph."""
        self.scene.clear()
        self.nodes = {}
        self.edges = []
        self.edge_items = []
        
        if not self.functions:
            return
        
        # Create nodes for all functions with signature and assembly
        for func_name in self.functions.keys():
            info = self.function_info.get(func_name, {})
            signature = info.get('signature', f"{func_name}()")
            assembly = info.get('assembly', "Assembly unavailable")
            
            # Pass call graph information to the node
            node = FunctionNode(func_name, signature, assembly, 0, 0, 
                              calls=self.calls, function_info=self.function_info)
            self.nodes[func_name] = node
            self.scene.addItem(node)
        
        # Create edges for function calls
        for caller, callees in self.calls.items():
            if caller in self.nodes:
                for callee in callees:
                    if callee in self.nodes:
                        self.edges.append((caller, callee))
        
        # Auto layout first to position nodes
        self.auto_layout()
        
        # Then draw edges
        for caller, callee in self.edges:
            self.draw_edge(caller, callee)
    
    def draw_edge(self, caller, callee):
        """Draw an edge between two nodes."""
        if caller not in self.nodes or callee not in self.nodes:
            return
            
        caller_node = self.nodes[caller]
        callee_node = self.nodes[callee]
        
        # Calculate line endpoints (on the edges of rectangles)
        caller_rect = caller_node.rect()
        callee_rect = callee_node.rect()
        
        # Use center of the entire rectangle for edge connections
        caller_center = caller_node.scenePos() + QPointF(caller_rect.width() / 2, caller_rect.height() / 2)
        callee_center = callee_node.scenePos() + QPointF(callee_rect.width() / 2, callee_rect.height() / 2)
        
        # Calculate direction vector
        dx = callee_center.x() - caller_center.x()
        dy = callee_center.y() - caller_center.y()
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        # Normalize
        dx /= length
        dy /= length
        
        # Calculate rectangle half dimensions
        caller_half_w = caller_rect.width() / 2
        caller_half_h = caller_rect.height() / 2
        callee_half_w = callee_rect.width() / 2
        callee_half_h = callee_rect.height() / 2
        
        # Find intersection point on caller rectangle edge
        # Use line-rectangle intersection algorithm
        if abs(dx) > 1e-6:
            t1 = caller_half_w / abs(dx)
            t2 = caller_half_h / abs(dy) if abs(dy) > 1e-6 else float('inf')
            t_caller = min(t1, t2)
        else:
            t_caller = caller_half_h / abs(dy) if abs(dy) > 1e-6 else 0
        
        start_point = caller_center + QPointF(dx * t_caller, dy * t_caller)
        
        # Find intersection point on callee rectangle edge
        if abs(dx) > 1e-6:
            t1 = callee_half_w / abs(dx)
            t2 = callee_half_h / abs(dy) if abs(dy) > 1e-6 else float('inf')
            t_callee = min(t1, t2)
        else:
            t_callee = callee_half_h / abs(dy) if abs(dy) > 1e-6 else 0
        
        end_point = callee_center - QPointF(dx * t_callee, dy * t_callee)
        
        # Create arrow line
        line = QGraphicsLineItem(
            start_point.x(), start_point.y(),
            end_point.x(), end_point.y()
        )
        pen = QPen(QColor(100, 100, 100), 2)
        pen.setStyle(Qt.DashLine)
        line.setPen(pen)
        self.scene.addItem(line)
        self.edge_items.append(line)
        
        # Add arrowhead
        arrow_size = 10
        angle = math.atan2(dy, dx)
        arrow_p1 = end_point - QPointF(
            arrow_size * math.cos(angle - math.pi / 6),
            arrow_size * math.sin(angle - math.pi / 6)
        )
        arrow_p2 = end_point - QPointF(
            arrow_size * math.cos(angle + math.pi / 6),
            arrow_size * math.sin(angle + math.pi / 6)
        )
        
        arrow1 = QGraphicsLineItem(
            end_point.x(), end_point.y(),
            arrow_p1.x(), arrow_p1.y()
        )
        arrow1.setPen(pen)
        self.scene.addItem(arrow1)
        self.edge_items.append(arrow1)
        
        arrow2 = QGraphicsLineItem(
            end_point.x(), end_point.y(),
            arrow_p2.x(), arrow_p2.y()
        )
        arrow2.setPen(pen)
        self.scene.addItem(arrow2)
        self.edge_items.append(arrow2)
    
    def auto_layout(self):
        """Automatically layout nodes in a circular or force-directed manner."""
        if not self.nodes:
            return
        
        node_list = list(self.nodes.keys())
        n = len(node_list)
        
        if n == 0:
            return
        
        # Remove old edges before repositioning
        for edge_item in self.edge_items:
            self.scene.removeItem(edge_item)
        self.edge_items = []
        
        # Calculate maximum node dimensions
        max_width = 0
        max_height = 0
        for func_name in node_list:
            node = self.nodes[func_name]
            node_rect = node.rect()
            max_width = max(max_width, node_rect.width())
            max_height = max(max_height, node_rect.height())
        
        # Calculate minimum spacing needed to prevent overlaps
        # When nodes are placed in a circle, we need to ensure the arc distance
        # between adjacent nodes is sufficient. The chord length between adjacent
        # nodes should be at least the diagonal of the largest node plus padding.
        max_diagonal = math.sqrt(max_width * max_width + max_height * max_height)
        
        # Add generous padding between nodes (minimum 80 pixels)
        padding = 80
        min_chord_length = max_diagonal + padding
        
        # Calculate radius based on chord length formula:
        # chord_length = 2 * radius * sin(angle/2)
        # For n nodes evenly spaced: angle = 2*pi/n
        # So: chord_length = 2 * radius * sin(pi/n)
        # Therefore: radius = chord_length / (2 * sin(pi/n))
        if n > 1:
            angle_per_node = 2 * math.pi / n
            min_radius = min_chord_length / (2 * math.sin(angle_per_node / 2))
        else:
            min_radius = 200
        
        # Use a minimum radius and scale up if needed
        center_x, center_y = 600, 500
        radius = max(min_radius, 350)
        
        # For very few nodes, use a larger radius for better visual spacing
        if n <= 3:
            radius = max(radius, 450)
        elif n <= 6:
            radius = max(radius, 400)
        
        # Place nodes in a circle with proper spacing
        for i, func_name in enumerate(node_list):
            angle = 2 * math.pi * i / n
            node = self.nodes[func_name]
            node_rect = node.rect()
            # Center the rectangle based on its actual size
            x = center_x + radius * math.cos(angle) - node_rect.width() / 2
            y = center_y + radius * math.sin(angle) - node_rect.height() / 2
            node.setPos(x, y)
        
        # Redraw edges with new positions
        for caller, callee in self.edges:
            self.draw_edge(caller, callee)


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Get filename from command-line arguments if provided
    filename = None
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
    visualizer = CallGraphVisualizer(filename)
    visualizer.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
