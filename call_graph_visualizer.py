"""
Call Graph Visualizer using PyQt5
Displays a call graph as an interactive graph visualization.
"""

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,
                             QGraphicsView, QGraphicsScene, QGraphicsRectItem,
                             QGraphicsTextItem, QGraphicsLineItem, QGraphicsPathItem, QMessageBox,
                             QScrollArea, QTextEdit, QTabWidget, QTabBar, QListWidget, QStackedWidget,
                             QComboBox)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QEvent
from PyQt5.QtGui import QFont, QPen, QBrush, QColor, QPainter, QPainterPath, QMouseEvent, QWheelEvent
from PyQt5.QtWidgets import QGraphicsSceneMouseEvent
import sys
import os
import math
from pathlib import Path
from collections import defaultdict


class PanGraphicsView(QGraphicsView):
    """Custom QGraphicsView that supports panning with right or middle mouse button only.
    Left click on a node selects it for the overlay; left click on background clears overlay.
    Left drag does not pan."""
    
    node_left_clicked = pyqtSignal(object)   # emits FunctionNode when left-clicked
    background_left_clicked = pyqtSignal()   # when left-click on scene background
    
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.panning = False
        self.pan_button_pressed = False
        self.last_pan_point = QPointF()
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
    
    def _find_function_node_at(self, view_pos):
        """Return the FunctionNode under view_pos, or None. Traverses parent if item is a child."""
        item = self.itemAt(view_pos)
        while item is not None:
            if isinstance(item, FunctionNode):
                return item
            item = item.parentItem()
        return None
    
    def mousePressEvent(self, event):
        """Handle mouse press: only right/middle can start panning."""
        if event.button() in (Qt.RightButton, Qt.MiddleButton):
            self.pan_button_pressed = True
            self.last_pan_point = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move: pan only when right/middle was used and drag threshold exceeded."""
        if self.pan_button_pressed:
            if not self.panning:
                delta = event.pos() - self.last_pan_point
                if abs(delta.x()) > 3 or abs(delta.y()) > 3:
                    self.panning = True
                    self.setCursor(Qt.ClosedHandCursor)
            
            if self.panning:
                delta = event.pos() - self.last_pan_point
                self.last_pan_point = event.pos()
                h_bar = self.horizontalScrollBar()
                v_bar = self.verticalScrollBar()
                h_bar.setValue(h_bar.value() - delta.x())
                v_bar.setValue(v_bar.value() - delta.y())
            else:
                super().mouseMoveEvent(event)
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Stop panning on right/middle release. On left release (no pan), emit node or background click."""
        if event.button() in (Qt.RightButton, Qt.MiddleButton):
            was_panning = self.panning
            self.panning = False
            self.pan_button_pressed = False
            self.setCursor(Qt.ArrowCursor)
            if not was_panning:
                super().mouseReleaseEvent(event)
            return
        
        if event.button() == Qt.LeftButton and not self.panning:
            node = self._find_function_node_at(event.pos())
            if node is not None:
                self.node_left_clicked.emit(node)
            else:
                self.background_left_clicked.emit()
        
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


class FunctionCallRectangle(QGraphicsRectItem):
    """Represents a function call with arguments in a rounded rectangle."""
    
    def __init__(self, caller_name, callee_name, args_list, x, y):
        """
        Args:
            caller_name: Name of the function making the call
            callee_name: Name of the function being called
            args_list: List of argument strings (one per call site)
            x, y: Position coordinates
        """
        # Calculate required dimensions
        font = QFont("Courier", 7)
        font.setBold(True)
        from PyQt5.QtGui import QFontMetrics
        metrics = QFontMetrics(font)
        
        # Calculate width needed
        max_width = 0
        header_text = f"{caller_name} → {callee_name}"
        header_width = metrics.width(header_text)
        max_width = max(max_width, header_width)
        
        # Calculate width for arguments
        for args in args_list:
            args_text = f"  args: {args}" if args else "  args: (none)"
            args_width = metrics.width(args_text)
            max_width = max(max_width, args_width)
        
        # Add padding
        width = max_width + 20
        min_width = 200
        
        # Calculate height
        line_height = metrics.height()
        header_height = line_height + 10
        args_height = len(args_list) * (line_height + 5) + 10
        total_height = header_height + args_height
        
        super().__init__(0, 0, max(width, min_width), total_height)
        self.caller_name = caller_name
        self.callee_name = callee_name
        self.args_list = args_list
        self.setPos(x, y)
        self.setPen(QPen(QColor(150, 200, 100), 2))
        self.setFlag(QGraphicsRectItem.ItemIsMovable, False)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        
        # Set rounded rectangle appearance
        self.setBrush(QBrush(QColor(120, 180, 80)))
        
        # Create text items
        # Header: caller → callee
        self.header_text = QGraphicsTextItem(header_text, self)
        self.header_text.setDefaultTextColor(QColor(255, 255, 255))
        header_font = QFont("Courier", 7)
        header_font.setBold(True)
        self.header_text.setFont(header_font)
        self.header_text.setPos(5, 5)
        self.header_text.setTextWidth(self.rect().width() - 10)
        
        # Arguments list
        y_offset = header_height
        for i, args in enumerate(args_list):
            args_text = f"  args: {args}" if args else "  args: (none)"
            args_item = QGraphicsTextItem(args_text, self)
            args_item.setDefaultTextColor(QColor(255, 255, 255))
            args_font = QFont("Courier", 6)
            args_font.setBold(False)
            args_item.setFont(args_font)
            args_item.setPos(5, y_offset + i * (line_height + 5))
            args_item.setTextWidth(self.rect().width() - 10)
    
    def paint(self, painter, option, widget=None):
        """Custom paint to draw rounded rectangle."""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw drop shadow
        shadow_path = QPainterPath()
        shadow_offset = 28  # 7 times bigger than original 4
        shadow_rect = self.rect().translated(shadow_offset, shadow_offset)
        shadow_path.addRoundedRect(shadow_rect, 10, 10)
        painter.fillPath(shadow_path, QBrush(QColor(0, 0, 0, 80)))  # Semi-transparent black shadow
        
        # Draw rounded rectangle
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 10, 10)
        painter.fillPath(path, self.brush())
        painter.strokePath(path, self.pen())


class FunctionNode(QGraphicsRectItem):
    """Represents a function node with signature and assembly body."""
    
    def __init__(self, name, signature, assembly, x, y, width=None, min_height=60, calls=None, function_info=None, on_toggle_cb=None):
        # Calculate required width based on content (including function name)
        if width is None:
            width = self.calculate_required_width(name, signature, assembly)
        
        # Extract registers
        self.calls = calls if calls is not None else {}
        self.function_info = function_info if function_info is not None else {}
        self.on_toggle_cb = on_toggle_cb
        
        # Get registers used in this function
        func_registers = self.extract_registers_from_assembly(assembly)
        
        # Get registers used in function and its call graph (function's own + all callees)
        call_graph_registers = self.extract_registers_from_call_graph(name, assembly)
        # Include the function's own registers in the call graph list
        call_graph_registers.update(func_registers)
        
        # Store call_graph_registers for later use (e.g., sorting in layout)
        self.call_graph_registers = call_graph_registers
        
        # Format register displays with color-coding
        func_registers_text = self.format_registers(func_registers)
        call_graph_registers_text = self.format_registers(call_graph_registers)
        
        # Calculate required heights
        # Calculate function name height (larger font, size 10)
        function_name_height = self.calculate_text_height(name, width - 10, 10, bold=True, is_html=False)
        signature_height = self.calculate_text_height(signature, width - 10, 7, bold=True, is_html=False)
        
        # Calculate label heights
        label_height = self.calculate_text_height("Registers (function + call graph):", width - 10, 7, bold=True, is_html=False)
        label_height2 = self.calculate_text_height("Registers (function only):", width - 10, 7, bold=True, is_html=False)
        
        call_graph_registers_height = self.calculate_text_height(call_graph_registers_text, width - 10, 7, bold=False, is_html=True)
        func_registers_height = self.calculate_text_height(func_registers_text, width - 10, 7, bold=False, is_html=True)
        formatted_asm = self.format_assembly(assembly)
        assembly_height = self.calculate_text_height(formatted_asm, width - 10, 7, bold=False, is_html=True)
        
        # Set heights with more generous padding to prevent cutoff
        # Signature rect now needs to accommodate both function name and signature
        # Add some spacing between function name and signature (5 pixels)
        signature_rect_height = max(50, function_name_height + signature_height + 20)  # Min 50, or content + padding
        call_graph_registers_rect_height = max(50, label_height + call_graph_registers_height + 20)  # Min 50, or label + content + padding
        func_registers_rect_height = max(50, label_height2 + func_registers_height + 20)  # Min 50, or label + content + padding
        assembly_rect_height = max(60, assembly_height + 20)  # Min 60, or content + more padding
        
        total_height = signature_rect_height + call_graph_registers_rect_height + func_registers_rect_height + assembly_rect_height
        
        super().__init__(0, 0, width, total_height)
        self.name = name
        self.signature = signature
        self.assembly = assembly
        # Get C code from function_info if available
        self.c_code = function_info.get(name, {}).get('c_code', '') if function_info else ''
        # Toggle state: True = showing assembly, False = showing C code
        self.showing_assembly = True
        self.setPos(x, y)
        self.setPen(QPen(QColor(50, 100, 200), 2))
        self.setFlag(QGraphicsRectItem.ItemIsMovable, False)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        # Enable mouse tracking for click detection
        self.setAcceptHoverEvents(True)
        
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
        
        # Add function name text (bold and bigger, above signature)
        self.function_name_text = QGraphicsTextItem(name, self)
        self.function_name_text.setDefaultTextColor(QColor(255, 255, 255))
        font_name = QFont("Courier", 14)
        font_name.setBold(True)
        self.function_name_text.setFont(font_name)
        self.function_name_text.setPos(5, 5)
        self.function_name_text.setTextWidth(width - 10)
        
        # Add signature text (positioned below function name)
        # Use the pre-calculated function_name_height with 5 pixels spacing
        self.signature_text = QGraphicsTextItem(self.format_signature(signature), self)
        self.signature_text.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Courier", 7)
        font.setBold(True)
        self.signature_text.setFont(font)
        self.signature_text.setPos(5, 5 + function_name_height + 5)  # 5 pixels spacing after function name
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
    
    def calculate_required_width(self, name, signature, assembly):
        """Calculate the minimum width needed to fit signature and assembly without wrapping."""
        from PyQt5.QtGui import QFontMetrics
        
        # Use Courier font with size 7 to match the display font
        font = QFont("Courier", 7)
        font.setBold(True)
        metrics_bold = QFontMetrics(font)
        
        # Use larger font for function name (size 10)
        font_large = QFont("Courier", 10)
        font_large.setBold(True)
        metrics_large_bold = QFontMetrics(font_large)
        
        font.setBold(False)
        metrics_normal = QFontMetrics(font)
        
        max_width = 0
        
        # Check function name width (using large bold metrics)
        function_name_width = metrics_large_bold.width(name)
        max_width = max(max_width, function_name_width)
        
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
    
    def format_c_code(self, c_code):
        """Format C code for display as plain text, removing signature and braces."""
        if not c_code or c_code.strip() == "":
            return "No C code available"
        
        # Remove function signature and first curly brace
        # Find the first opening brace
        first_brace_idx = c_code.find('{')
        if first_brace_idx != -1:
            # Skip the brace and any whitespace after it
            body_start = first_brace_idx + 1
            # Find the last closing brace
            last_brace_idx = c_code.rfind('}')
            if last_brace_idx != -1 and last_brace_idx > first_brace_idx:
                # Extract just the body content
                body_code = c_code[body_start:last_brace_idx].strip()
                return body_code
        
        # Fallback: return as-is if braces not found
        return c_code
    
    def toggle_display(self):
        """Toggle between showing assembly and C code."""
        if not self.c_code:
            # No C code available, can't toggle
            return
        
        self.showing_assembly = not self.showing_assembly
        
        # Update the display
        if self.showing_assembly:
            # Show assembly (with HTML formatting)
            formatted_asm = self.format_assembly(self.assembly)
            self.assembly_text.setHtml(formatted_asm)
        else:
            # Show C code (plain text, no HTML)
            formatted_c = self.format_c_code(self.c_code)
            self.assembly_text.setPlainText(formatted_c)
        
        # Recalculate height and update rectangle
        width = self.rect().width()
        assembly_doc = self.assembly_text.document()
        assembly_doc.setTextWidth(width - 10)
        actual_height = assembly_doc.size().height()
        required_height = actual_height + 25
        
        # Update body rectangle height
        signature_rect_height = self.signature_rect.height()
        call_graph_registers_rect_height = self.call_graph_registers_rect.height()
        func_registers_rect_height = self.func_registers_rect.height()
        
        self.body_rect = QRectF(0, signature_rect_height + call_graph_registers_rect_height + func_registers_rect_height, 
                                width, required_height)
        
        # Update total height
        new_total_height = signature_rect_height + call_graph_registers_rect_height + func_registers_rect_height + required_height
        self.setRect(0, 0, width, new_total_height)
        
        # Update the scene to reflect changes
        self.update()
    
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
        
        # Process lines to add indentation for local label blocks
        # First, split into lines and process them
        lines = assembly.split('\n')
        processed_lines = []
        in_local_label_block = False  # Track if we're in a local label block
        
        for line in lines:
            stripped = line.strip()
            
            # Check if this is a local label (starts with .L followed by letters/digits and ends with :)
            # Examples: .LFB0:, .LFE0:, .L19:, .L18:
            if re.match(r'^\s*\.L[A-Za-z0-9_]+\s*:', stripped):
                # This is a local label - don't indent it, but mark that we're now in a block
                in_local_label_block = True
                processed_lines.append(line)
            elif stripped:
                # Non-empty line - if we're in a local label block, indent it
                if in_local_label_block:
                    # Add indentation (preserve existing leading whitespace, add 4 more spaces)
                    leading_whitespace = len(line) - len(line.lstrip())
                    indented_line = ' ' * (leading_whitespace + 4) + line.lstrip()
                    processed_lines.append(indented_line)
                else:
                    processed_lines.append(line)
                # Check if this line might end the local label block
                # (e.g., if it's a non-local label or function definition)
                if re.match(r'^\s*\w+\s*:', stripped) and not stripped.startswith('.'):
                    # This is a non-local label (like a function name)
                    in_local_label_block = False
            else:
                # Empty line - preserve it but reset block state
                in_local_label_block = False
                processed_lines.append(line)
        
        assembly = '\n'.join(processed_lines)
        
        # Escape HTML special characters first
        html_assembly = assembly.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # Convert leading spaces to &nbsp; for proper indentation display in HTML
        lines = html_assembly.split('\n')
        processed_html_lines = []
        for line in lines:
            # Count leading spaces
            leading_spaces = 0
            for char in line:
                if char == ' ':
                    leading_spaces += 1
                else:
                    break
            if leading_spaces > 0:
                # Replace leading spaces with &nbsp; entities
                processed_line = '&nbsp;' * leading_spaces + line[leading_spaces:]
            else:
                processed_line = line
            processed_html_lines.append(processed_line)
        html_assembly = '\n'.join(processed_html_lines)
        
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
        
        # Color memory operand brackets/parentheses black
        # Pattern to match memory operands: [content] or (content)
        # Note: content may contain HTML spans from register/instruction coloring
        def color_memory_brackets(text):
            """Color brackets and parentheses of memory operands black."""
            result = text
            
            # Helper function to check if a position is inside an HTML tag
            def is_inside_html_tag(text, pos):
                """Check if position pos is inside an HTML tag."""
                # Look backwards to find the most recent < or > before this position
                # If we find a < and no > after it (or > comes before <), we're inside a tag
                i = pos - 1
                most_recent_lt = -1
                most_recent_gt = -1
                
                while i >= 0:
                    # Check for HTML entities (4 characters: &lt; or &gt;)
                    if i >= 3:
                        entity = text[i-3:i+1]
                        if entity == '&gt;':
                            if most_recent_gt == -1:
                                most_recent_gt = i - 3
                            i -= 4
                            continue
                        elif entity == '&lt;':
                            if most_recent_lt == -1:
                                most_recent_lt = i - 3
                            i -= 4
                            continue
                    
                    # Check for regular < and >
                    if text[i] == '>':
                        if most_recent_gt == -1:
                            most_recent_gt = i
                    elif text[i] == '<':
                        if most_recent_lt == -1:
                            most_recent_lt = i
                    
                    i -= 1
                
                # If we found a < and either no > or the < comes after the >
                if most_recent_lt != -1:
                    if most_recent_gt == -1 or most_recent_lt > most_recent_gt:
                        return True
                
                return False
            
            # Process square brackets: find [ and matching ]
            i = 0
            while i < len(result):
                if result[i] == '[' and not is_inside_html_tag(result, i):
                    # Find matching ]
                    depth = 1
                    j = i + 1
                    found_match = False
                    
                    while j < len(result) and depth > 0:
                        if result[j] == '[' and not is_inside_html_tag(result, j):
                            depth += 1
                        elif result[j] == ']' and not is_inside_html_tag(result, j):
                            depth -= 1
                            if depth == 0:
                                found_match = True
                                break
                        j += 1
                    
                    if found_match:
                        # Get content between brackets
                        content = result[i+1:j]
                        # Check if content looks like a memory operand
                        if re.search(r'[a-zA-Z0-9]', content) or '<span' in content:
                            # Color the brackets black
                            replacement = (f'<span style="color: #000000;">[</span>'
                                          f'{content}'
                                          f'<span style="color: #000000;">]</span>')
                            result = result[:i] + replacement + result[j+1:]
                            # Move past the replacement (skip the entire replacement)
                            i += len(replacement)
                            continue
                
                i += 1
            
            # Process parentheses: find ( and matching )
            i = 0
            while i < len(result):
                if result[i] == '(' and not is_inside_html_tag(result, i):
                    # Find matching )
                    depth = 1
                    j = i + 1
                    found_match = False
                    
                    while j < len(result) and depth > 0:
                        if result[j] == '(' and not is_inside_html_tag(result, j):
                            depth += 1
                        elif result[j] == ')' and not is_inside_html_tag(result, j):
                            depth -= 1
                            if depth == 0:
                                found_match = True
                                break
                        j += 1
                    
                    if found_match:
                        # Get content between parentheses
                        content = result[i+1:j]
                        # Check if content looks like a memory operand
                        if re.search(r'[a-zA-Z0-9]', content) or '<span' in content:
                            # Color the parentheses black
                            replacement = (f'<span style="color: #000000;">(</span>'
                                          f'{content}'
                                          f'<span style="color: #000000;">)</span>')
                            result = result[:i] + replacement + result[j+1:]
                            # Move past the replacement (skip the entire replacement)
                            i += len(replacement)
                            continue
                
                i += 1
            
            return result
        
        html_assembly = color_memory_brackets(html_assembly)
        
        # Preserve line breaks by converting newlines to <br>
        html_assembly = html_assembly.replace('\n', '<br>')
        
        return html_assembly
    
    def paint(self, painter, option, widget=None):
        """Custom paint to draw rounded rectangles."""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw drop shadows for all rectangles
        shadow_offset = 28  # 7 times bigger than original 4
        shadow_brush = QBrush(QColor(0, 0, 0, 80))  # Semi-transparent black shadow
        
        # Shadow for rectangle 1: signature
        shadow_path1 = QPainterPath()
        shadow_path1.addRoundedRect(self.signature_rect.translated(shadow_offset, shadow_offset), 10, 10)
        painter.fillPath(shadow_path1, shadow_brush)
        
        # Shadow for rectangle 2: call graph registers
        shadow_path2 = QPainterPath()
        shadow_path2.addRoundedRect(self.call_graph_registers_rect.translated(shadow_offset, shadow_offset), 10, 10)
        painter.fillPath(shadow_path2, shadow_brush)
        
        # Shadow for rectangle 3: function registers
        shadow_path3 = QPainterPath()
        shadow_path3.addRoundedRect(self.func_registers_rect.translated(shadow_offset, shadow_offset), 10, 10)
        painter.fillPath(shadow_path3, shadow_brush)
        
        # Shadow for rectangle 4: assembly body
        shadow_path4 = QPainterPath()
        shadow_path4.addRoundedRect(self.body_rect.translated(shadow_offset, shadow_offset), 10, 10)
        painter.fillPath(shadow_path4, shadow_brush)
        
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
    
    def mousePressEvent(self, event):
        """Handle mouse press: right-click on body toggles between assembly and C code."""
        if event.button() == Qt.RightButton:
            click_pos = event.pos()
            if self.body_rect.contains(click_pos):
                self.toggle_display()
                if self.on_toggle_cb:
                    self.on_toggle_cb(self)
                event.accept()
                return
        
        super().mousePressEvent(event)


class NodeDetailOverlay(QWidget):
    """Overlay on the right of the graph view showing selected node + its call rectangles. Tied to viewport."""
    
    overlay_clicked = pyqtSignal()
    overlay_resized = pyqtSignal()
    
    DEFAULT_WIDTH = 380
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(self.DEFAULT_WIDTH)
        self.setStyleSheet("background-color: rgba(30, 30, 40, 240); border-left: 1px solid #444;")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 4, 4, 4)
        self._scene = QGraphicsScene()
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._view.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._view.installEventFilter(self)
        self._layout.addWidget(self._view)
        self._overlay_node = None
        self._overlay_call_rects = []
        self._visualizer = None
        self.hide()
    
    def set_visualizer(self, v):
        self._visualizer = v
    
    def _clear_scene(self):
        for r in self._overlay_call_rects:
            if r.scene():
                self._scene.removeItem(r)
        self._overlay_call_rects = []
        if self._overlay_node and self._overlay_node.scene():
            self._scene.removeItem(self._overlay_node)
        self._overlay_node = None
    
    def set_node(self, source_node):
        """Show source_node and its call rectangles in the overlay."""
        if not self._visualizer:
            return
        self._clear_scene()
        viz = self._visualizer
        name = source_node.name
        info = viz.function_info.get(name, {})
        sig = info.get('signature', f"{name}()")
        asm = info.get('assembly', "Assembly unavailable")
        node = FunctionNode(name, sig, asm, 0, 0, calls=viz.calls, function_info=viz.function_info, on_toggle_cb=None)
        if not source_node.showing_assembly and node.c_code:
            node.toggle_display()
        node.setPos(0, 0)
        self._scene.addItem(node)
        self._overlay_node = node
        
        node_w = node.rect().width()
        node_h = node.rect().height()
        gap = 20
        call_x = node_w + gap
        y_pos = 0
        max_call_w = 0
        call_list = viz.calls_with_args.get(name, [])
        calls_by_callee = defaultdict(list)
        for callee, args in call_list:
            calls_by_callee[callee].append(args)
        for callee_name, args_list in calls_by_callee.items():
            call_rect = FunctionCallRectangle(name, callee_name, args_list, call_x, y_pos)
            self._scene.addItem(call_rect)
            self._overlay_call_rects.append(call_rect)
            max_call_w = max(max_call_w, call_rect.rect().width())
            y_pos += call_rect.rect().height() + 10
        
        self._scene.setSceneRect(self._scene.itemsBoundingRect())
        padding = 24
        if self._overlay_call_rects:
            required_w = int(node_w + gap + max_call_w + padding)
        else:
            required_w = int(node_w + padding)
        required_w = max(required_w, self.DEFAULT_WIDTH)
        self.setFixedWidth(required_w)
        self.overlay_resized.emit()
        self.show()
    
    def clear(self):
        self._clear_scene()
        self.hide()
    
    def eventFilter(self, obj, event):
        if obj is self._view and event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self.overlay_clicked.emit()
        return super().eventFilter(obj, event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.overlay_clicked.emit()
        super().mousePressEvent(event)


class ViewContainerWidget(QWidget):
    """Holds the graph view and the right-side overlay, tied to viewport."""
    
    def __init__(self, view, overlay, parent=None):
        super().__init__(parent)
        self._view = view
        self._overlay = overlay
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)
        overlay.setParent(self)
        overlay.raise_()
        overlay.overlay_resized.connect(self._update_overlay_geometry)
    
    def _update_overlay_geometry(self):
        w, h = self.width(), self.height()
        ow = self._overlay.width()
        self._overlay.setGeometry(w - ow, 0, ow, h)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_overlay_geometry()


class CallGraphVisualizer(QMainWindow):
    """Main window for the call graph visualizer."""
    
    def __init__(self, filename=None):
        super().__init__()
        self.functions = {}
        self.calls = defaultdict(set)
        self.calls_with_args = defaultdict(list)  # caller -> list of (callee, args_string) tuples
        self.function_info = {}  # function_name -> {'signature': str, 'assembly': str}
        self.nodes = {}  # function_name -> FunctionNode
        self.edges = []  # List of (caller, callee) tuples
        self.edge_items = []  # List of QGraphicsItem for edges (lines and arrows)
        self.call_rectangles = []  # List of call display rectangles
        self.current_filename = None
        self.global_variables = {}  # global_var_name -> type string
        self.global_var_usage = {}  # (global_var_name, func_name) -> {'r': bool, 'w': bool}
        self.structs = {}  # struct_name -> {'members': [(member_name, member_type), ...]}
        self.globals_content = "No global variables found"
        self.structs_content = "No structs found"
        self.current_data_tab = 0  # 0 = Global Variables, 1 = Structs
        self.function_sources = {}  # function_name -> source file path
        self.directory_c_files = []  # List of C files when directory is loaded
        self.directory_assembly_files = []  # List of assembly files when directory is loaded
        self.is_directory_mode = False  # Whether we're in directory mode
        self.selected_file_filter = None  # Currently selected file for filtering (None = show all)
        self.current_path = None  # Store current file/directory path for reloading
        self.compiler = 'gcc'  # Default compiler choice
        self.optimization = 'O0'  # Default optimization level
        self.overlay_node_name = None  # name of function shown in right overlay, or None
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
        
        # Main layout (horizontal: left panel + main view)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Left panel for global variables and structs
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_panel.setMinimumWidth(250)
        left_panel_layout = QVBoxLayout()
        left_panel.setLayout(left_panel_layout)
        
        # Tab bar for switching between File Selection (if directory), Globals, and Structs
        self.data_tab_bar = QTabBar()
        self.file_selection_tab_index = -1  # Index of file selection tab (-1 if not present)
        self.globals_tab_index = 0  # Will be updated based on whether file selection tab exists
        self.structs_tab_index = 1  # Will be updated based on whether file selection tab exists
        self.data_tab_bar.addTab("🌐")
        self.data_tab_bar.addTab("🏛")
        self.data_tab_bar.currentChanged.connect(self.on_tab_changed)
        left_panel_layout.addWidget(self.data_tab_bar)
        
        # Stacked widget to switch between file list and text edit
        self.data_stacked = QStackedWidget()
        
        # File selection list (for directory mode)
        self.file_list_widget = QListWidget()
        self.file_list_widget.itemClicked.connect(self.on_file_selected)
        self.data_stacked.addWidget(self.file_list_widget)  # Index 0
        
        # Text area for Globals/Structs
        self.data_text = QTextEdit()
        self.data_text.setReadOnly(True)
        self.data_text.setFont(QFont("Courier", 9))
        self.data_text.setPlainText("No global variables found")
        self.data_stacked.addWidget(self.data_text)  # Index 1
        
        # Start with text edit visible
        self.data_stacked.setCurrentIndex(1)
        left_panel_layout.addWidget(self.data_stacked)
        
        # Store current tab index (0 = File Selection if exists, then Globals, then Structs)
        self.current_data_tab = 0
        
        main_layout.addWidget(left_panel)
        
        # Right side: main content area
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        self.open_button = QPushButton("Open File/Directory")
        self.open_button.clicked.connect(self.open_file)
        control_layout.addWidget(self.open_button)
        
        # Compiler selection dropdown
        compiler_label = QLabel("Compiler:")
        control_layout.addWidget(compiler_label)
        self.compiler_combo = QComboBox()
        self.compiler_combo.addItems(['gcc', 'clang', '@c-compiler'])
        self.compiler_combo.setCurrentText(self.compiler)
        self.compiler_combo.currentTextChanged.connect(self.on_compiler_changed)
        control_layout.addWidget(self.compiler_combo)
        
        # Optimization selection dropdown
        optimization_label = QLabel("Optimization:")
        control_layout.addWidget(optimization_label)
        self.optimization_combo = QComboBox()
        self.optimization_combo.addItems(['O0', 'O1', 'O2', 'O3', 'Os', 'Ofast'])
        self.optimization_combo.setCurrentText(self.optimization)
        self.optimization_combo.currentTextChanged.connect(self.on_optimization_changed)
        control_layout.addWidget(self.optimization_combo)
        # Disable optimization dropdown when @c-compiler is selected
        if self.compiler == '@c-compiler':
            self.optimization_combo.setEnabled(False)
        
        control_layout.addStretch()
        
        self.status_label = QLabel("No file loaded")
        control_layout.addWidget(self.status_label)
        
        right_layout.addLayout(control_layout)
        
        # Graphics view with right-side overlay (viewport-fixed)
        self.scene = QGraphicsScene()
        self.view = PanGraphicsView(self.scene)
        self.overlay = NodeDetailOverlay()
        self.overlay.set_visualizer(self)
        self.view_container = ViewContainerWidget(self.view, self.overlay)
        right_layout.addWidget(self.view_container)
        
        self.view.node_left_clicked.connect(self.on_node_left_clicked)
        self.view.background_left_clicked.connect(self.clear_overlay)
        self.overlay.overlay_clicked.connect(self.clear_overlay)
        
        main_layout.addWidget(right_widget)
    
    def on_node_left_clicked(self, node):
        """Show node and its callee rectangles in the right overlay."""
        self.overlay_node_name = node.name
        self.overlay.set_node(node)
    
    def clear_overlay(self):
        """Clear the right-side overlay."""
        self.overlay_node_name = None
        self.overlay.clear()
    
    def refresh_overlay_if_showing(self, node):
        """Refresh overlay content when node toggles C/assembly, if it's the displayed node."""
        if self.overlay_node_name == node.name and self.overlay.isVisible():
            self.overlay.set_node(node)
    
    def load_file(self, path):
        """
        Load a C file, directory, or list of files and extract the call graph.
        
        Args:
            path: Path to a C file, directory, or list of file paths
        """
        try:
            from call_graph_extractor import extract_call_graph
            from assembly_extractor import get_function_info, get_all_subdirectories
            from file_finder import find_source_files, is_source_file_or_directory
            
            # Store the current path for reloading when compiler changes
            self.current_path = path
            
            # Determine if path is a file or directory
            if isinstance(path, str):
                path_obj = Path(path)
            else:
                path_obj = path
            
            c_filenames = []
            assembly_files = []
            include_dirs = []  # List of include directories to pass to compilers
            
            if path_obj.is_dir() or (isinstance(path, str) and os.path.isdir(path)):
                # It's a directory - find all source files
                c_files, asm_files, linker_scripts = find_source_files(path)
                c_filenames = c_files
                assembly_files = asm_files
                self.current_filename = path
                display_name = os.path.basename(os.path.abspath(path))
                # Enable directory mode when a directory is passed
                self.is_directory_mode = True
                self.directory_c_files = c_filenames
                self.directory_assembly_files = assembly_files
                self.selected_file_filter = None  # Reset filter
                # Get all subdirectories for include paths
                include_dirs = get_all_subdirectories(path)
            elif isinstance(path, list):
                # It's a list of files
                c_filenames = [f for f in path if f.endswith('.c')]
                assembly_files = [f for f in path if f.endswith(('.s', '.S'))]
                self.current_filename = path[0] if path else None
                display_name = f"{len(path)} files"
                # Enable directory mode if we have multiple C files
                self.is_directory_mode = len(c_filenames) > 1
                self.directory_c_files = c_filenames if self.is_directory_mode else []
                self.directory_assembly_files = assembly_files if self.is_directory_mode else []
                self.selected_file_filter = None  # Reset filter
                # Find common base directory and get all subdirectories
                if path:
                    # Get the common directory containing all files
                    common_dir = os.path.commonpath([os.path.abspath(f) for f in path])
                    if os.path.isdir(common_dir):
                        include_dirs = get_all_subdirectories(common_dir)
            else:
                # Single file - check if it's a C file or assembly file
                if path.endswith('.c'):
                    c_filenames = [path]
                elif path.endswith(('.s', '.S')):
                    assembly_files = [path]
                    c_filenames = []  # No C files, but we still need to parse the call graph from C
                    # If it's just an assembly file, we can't extract call graph from C
                    # We'll need to parse it differently
                self.current_filename = path
                display_name = os.path.basename(path)
                # Single file mode - disable directory mode
                self.is_directory_mode = False
                self.directory_c_files = []
                self.directory_assembly_files = []
                self.directory_assembly_files = []
                self.selected_file_filter = None  # Reset filter
                # Get directory containing the file and all its subdirectories
                file_dir = os.path.dirname(os.path.abspath(path))
                if file_dir and os.path.isdir(file_dir):
                    include_dirs = get_all_subdirectories(file_dir)
            
            if not c_filenames and not assembly_files:
                QMessageBox.warning(self, "No Files", 
                                   "No C files or assembly files found. Please select a directory "
                                   "containing .c, .s, or .S files, or a single C or assembly file.")
                return
            
            # Extract call graph from C files
            if c_filenames:
                result = extract_call_graph(c_filenames, include_dirs=include_dirs)
                if len(result) == 4:
                    self.functions, self.calls, self.calls_with_args, self.function_sources = result
                elif len(result) == 3:
                    self.functions, self.calls, self.calls_with_args = result
                    self.function_sources = {}
                else:
                    # Backward compatibility
                    self.functions, self.calls = result
                    self.calls_with_args = defaultdict(list)
                    self.function_sources = {}
            else:
                # No C files - can't extract call graph, but we can still parse assembly
                self.functions = {}
                self.calls = defaultdict(set)
                self.calls_with_args = defaultdict(list)
                QMessageBox.information(self, "Assembly Only", 
                                       "Only assembly files found. Call graph extraction requires C files. "
                                       "Assembly code will be parsed, but function calls won't be extracted.")
            
            # Extract function definitions from assembly files (non-local labels)
            # This should happen even when C files are present, to include assembly-only functions
            if assembly_files:
                from assembly_extractor import parse_assembly_file
                for asm_file in assembly_files:
                    asm_functions = parse_assembly_file(asm_file)
                    # Add functions to our functions dict (they won't have AST nodes though)
                    for func_name in asm_functions.keys():
                        if func_name not in self.functions:
                            # Create a dummy entry - we can't get signature/C code without C source
                            self.functions[func_name] = None
                            # Track that this function comes from an assembly file
                            self.function_sources[func_name] = asm_file
            
            # Extract function signatures and assembly
            if c_filenames:
                self.function_info = get_function_info(c_filenames, self.functions, assembly_files, compiler=self.compiler, optimization=self.optimization, include_dirs=include_dirs)
            else:
                # Assembly-only mode - create minimal function_info
                self.function_info = {}
            
            # Add assembly-only functions to function_info (those not found in C files)
            # Also ensure assembly-only functions have empty c_code to prevent switching
            from assembly_extractor import parse_assembly_file
            for asm_file in assembly_files:
                asm_functions = parse_assembly_file(asm_file)
                for func_name, asm_code in asm_functions.items():
                    # Only add if not already in function_info (i.e., assembly-only function)
                    if func_name not in self.function_info:
                        self.function_info[func_name] = {
                            'signature': f"{func_name}()",
                            'assembly': asm_code,
                            'c_code': ''  # Empty c_code prevents switching to C code
                        }
            
            # Ensure all assembly-only functions (those with None in functions dict) have empty c_code
            for func_name in self.functions.keys():
                if self.functions.get(func_name) is None and func_name in self.function_info:
                    # This is an assembly-only function - set c_code to empty
                    self.function_info[func_name]['c_code'] = ''
            
            # Extract global variables and detect their usage
            if c_filenames:
                self.global_variables = self.extract_global_variables(c_filenames, include_dirs=include_dirs)
                if self.global_variables and self.function_info:
                    self.global_var_usage = self.detect_global_usage_in_assembly(
                        self.global_variables, self.function_info)
                else:
                    self.global_var_usage = {}
                # Extract structs
                self.structs = self.extract_structs(c_filenames, include_dirs=include_dirs)
            else:
                self.global_variables = {}
                self.global_var_usage = {}
                self.structs = {}
            
            # Update global variables display
            self.update_globals_display()
            # Update structs display
            self.update_structs_display()
            
            # Update file selection tab (add/remove based on directory mode)
            self.update_file_selection_tab()
            
            # Update status
            file_count = len(c_filenames) + len(assembly_files)
            if file_count > 1:
                status_text = f"Loaded: {display_name} ({file_count} files, {len(self.functions)} functions)"
            else:
                status_text = f"Loaded: {display_name} ({len(self.functions)} functions)"
            self.status_label.setText(status_text)
            self.draw_graph()
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Error", f"Failed to parse file/directory:\n{str(e)}\n\n{traceback.format_exc()}")
    
    def open_file(self):
        """Open a file/directory dialog and load the selected file or directory."""
        # Create a simple dialog with two buttons
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Open File or Directory")
        dialog.setModal(True)
        dialog.resize(300, 150)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        label = QLabel("What would you like to open?")
        layout.addWidget(label)
        
        file_button = QPushButton("Select File")
        dir_button = QPushButton("Select Directory")
        cancel_button = QPushButton("Cancel")
        
        layout.addWidget(file_button)
        layout.addWidget(dir_button)
        layout.addWidget(cancel_button)
        
        selected_path = None
        
        def on_file_clicked():
            nonlocal selected_path
            filename, _ = QFileDialog.getOpenFileName(
                dialog, "Open C/Assembly File", "", 
                "C Files (*.c);;Assembly Files (*.s *.S);;All Files (*)"
            )
            if filename:
                selected_path = filename
                dialog.accept()
        
        def on_dir_clicked():
            nonlocal selected_path
            directory = QFileDialog.getExistingDirectory(
                dialog, "Open Directory", "", QFileDialog.ShowDirsOnly
            )
            if directory:
                selected_path = directory
                dialog.accept()
        
        def on_cancel_clicked():
            dialog.reject()
        
        file_button.clicked.connect(on_file_clicked)
        dir_button.clicked.connect(on_dir_clicked)
        cancel_button.clicked.connect(on_cancel_clicked)
        
        if dialog.exec_() == QDialog.Accepted and selected_path:
            self.load_file(selected_path)
    
    def on_compiler_changed(self, compiler):
        """Handle compiler dropdown change - reload the current file if one is loaded."""
        self.compiler = compiler
        # Enable/disable optimization dropdown based on compiler
        if compiler == '@c-compiler':
            self.optimization_combo.setEnabled(False)
        else:
            self.optimization_combo.setEnabled(True)
        if self.current_path:
            # Reload the file with the new compiler
            self.load_file(self.current_path)
    
    def on_optimization_changed(self, optimization):
        """Handle optimization dropdown change - reload the current file if one is loaded."""
        self.optimization = optimization
        if self.current_path:
            # Reload the file with the new optimization level
            self.load_file(self.current_path)
    
    def clear_graph(self):
        """Clear the current graph."""
        self.scene.clear()
        self.nodes = {}
        self.edges = []
        self.edge_items = []
        self.call_rectangles = []
        self.functions = {}
        self.calls = defaultdict(set)
        self.calls_with_args = defaultdict(list)
        self.function_info = {}
        self.current_filename = None
        self.global_variables = {}
        self.global_var_usage = {}
        self.structs = {}
        self.globals_content = "No global variables found"
        self.structs_content = "No structs found"
        self.function_sources = {}
        self.is_directory_mode = False
        self.directory_c_files = []
        self.directory_assembly_files = []
        self.selected_file_filter = None
        self.current_path = None
        # Update tabs (remove file selection tab if it exists)
        self.update_file_selection_tab()
        # Update display based on current tab
        if self.current_data_tab == self.globals_tab_index:
            self.data_text.setPlainText(self.globals_content)
        elif self.current_data_tab == self.structs_tab_index:
            self.data_text.setPlainText(self.structs_content)
        self.status_label.setText("No file loaded")
    
    def extract_global_variables(self, c_filenames, include_dirs=None):
        """
        Extract global variable names and types from C source files.
        
        Args:
            c_filenames: List of C source file paths
            include_dirs: Optional list of include directories to add with -I flags
            
        Returns:
            dict: Mapping of global variable names to their type strings
        """
        if include_dirs is None:
            include_dirs = []
        
        from pycparser import parse_file, c_ast
        from call_graph_extractor import _create_attribute_fix_header, _create_fake_stddef_header
        try:
            from pycparser import __file__ as pycparser_file
            # First try the local fake_libc_include directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            fake_libc_include = os.path.join(script_dir, 'fake_libc_include')
            if not os.path.isdir(fake_libc_include):
                # Fall back to pycparser's fake_libc_include
                pycparser_dir = os.path.dirname(pycparser_file)
                fake_libc_include = os.path.join(pycparser_dir, 'utils', 'fake_libc_include')
            FAKE_LIBC_AVAILABLE = os.path.isdir(fake_libc_include)
            if FAKE_LIBC_AVAILABLE:
                fake_libc_include = os.path.abspath(fake_libc_include)
        except:
            FAKE_LIBC_AVAILABLE = False
            fake_libc_include = None
        
        global_vars = {}
        
        # Use the same cpp_args as call_graph_extractor
        cpp_args = []
        cpp_args.extend([
            '-U__attribute__',
            '-D__attribute__(x)=',
            '-D__alignof__(x)=sizeof(x)',
            '-D__packed__=',
            '-D__aligned__(x)=',
            '-D__unused__=',
            '-D__maybe_unused__=',
            '-D__unused=',
            '-D__maybe_unused=',
        ])
        
        attr_fix_header = _create_attribute_fix_header()
        if attr_fix_header:
            cpp_args.extend(['-include', attr_fix_header])
        
        if FAKE_LIBC_AVAILABLE:
            cpp_args.extend([
                '-I' + fake_libc_include,
                '-nostdinc',
            ])
            # Add user-provided include directories
            for include_dir in include_dirs:
                cpp_args.extend(['-I', include_dir])
        else:
            fake_stddef = _create_fake_stddef_header()
            if fake_stddef:
                fake_stddef_dir = os.path.dirname(fake_stddef)
                cpp_args.extend([
                    '-I' + fake_stddef_dir,
                    '-nostdinc',
                ])
                # Add user-provided include directories
                for include_dir in include_dirs:
                    cpp_args.extend(['-I', include_dir])
            else:
                # No fake headers - add user-provided include directories anyway
                for include_dir in include_dirs:
                    cpp_args.extend(['-I', include_dir])
        
        cpp_args.extend([
            '-D__volatile__=volatile',
            '-Dvolatile=',
            '-D__restrict=',
            '-D__extension__=',
            '-Dasm=',
            '-D__asm=',
            '-D__asm__=',
            '-D__asm__(x)=',
            '-D__asm(x)=',
            '-D__inline=',
            '-D__inline__=',
            '-D__const=const',
            '-D__signed__=signed',
        ])
        
        for filename in c_filenames:
            try:
                ast = parse_file(filename, use_cpp=True, cpp_args=cpp_args)
                self._visit_for_globals(ast, global_vars)
            except Exception as e:
                print(f"Warning: Error parsing file {filename} for globals: {e}", file=sys.stderr)
        
        return global_vars
    
    def _visit_for_globals(self, node, global_vars, in_function=False):
        """Recursively visit AST nodes to find global variable declarations."""
        from pycparser import c_ast, c_generator
        import re
        
        # Track if we're inside a function
        if isinstance(node, c_ast.FuncDef):
            in_function = True
        
        # Check for global variable declarations (Decl nodes at file scope)
        if isinstance(node, c_ast.Decl) and not in_function:
            if node.name:
                # Check if it's a variable (not a function)
                decl_type = node.type
                is_variable = False
                
                if isinstance(decl_type, c_ast.TypeDecl):
                    # It's a variable declaration
                    is_variable = True
                elif isinstance(decl_type, c_ast.ArrayDecl):
                    # It's an array declaration
                    is_variable = True
                elif isinstance(decl_type, c_ast.PtrDecl):
                    # It's a pointer declaration
                    is_variable = True
                
                if is_variable:
                    # Extract the type string using c_generator
                    try:
                        generator = c_generator.CGenerator()
                        # Generate the full declaration string (e.g., "int var_name" or "int *var_name")
                        full_decl = generator.visit(node)
                        # Remove the variable name to get just the type
                        # The declaration format is typically "type var_name" or "type *var_name" etc.
                        var_name = node.name
                        type_str = full_decl
                        
                        # Remove the variable name from the declaration
                        # Handle various patterns:
                        # - "int var" -> "int"
                        # - "int *var" -> "int *"
                        # - "int var[10]" -> "int [10]"
                        # - "struct foo var" -> "struct foo"
                        
                        # First, try exact match replacement
                        if type_str.endswith(var_name):
                            type_str = type_str[:-len(var_name)].strip()
                        elif var_name in type_str:
                            # More complex: find and remove the variable name
                            # Look for patterns like "var_name", "var_name[", "var_name)", etc.
                            # Pattern to match the variable name followed by optional brackets/parentheses
                            pattern = re.escape(var_name) + r'(?=\s*[\[\(]|$|\s)'
                            type_str = re.sub(pattern, '', type_str).strip()
                        
                        # Clean up extra spaces
                        type_str = ' '.join(type_str.split())
                        
                        # If we ended up with an empty string, try a different approach
                        if not type_str:
                            # Fallback: generate type from decl_type directly
                            type_str = generator.visit(decl_type)
                            if var_name in type_str:
                                type_str = type_str.replace(var_name, '').strip()
                                type_str = ' '.join(type_str.split())
                        
                        # Remove initial values (e.g., "int = 0" -> "int", "int = 5" -> "int")
                        # Pattern: = followed by any value (number, string, expression, etc.)
                        # Remove assignment: = followed by any characters until semicolon, comma, or end
                        # Be careful not to remove = in other contexts (like == in expressions)
                        # We only want to remove = that appears after the type (which should be at the end)
                        type_str = re.sub(r'\s*=\s*[^;,\[\]]+(?=[;,]|$)', '', type_str)
                        
                        # Remove array sizes (e.g., "int[10]" -> "int[]", "int[SIZE]" -> "int[]")
                        # Replace [number] or [identifier] with [] for array dimensions
                        # This handles both numeric sizes and constant names
                        # We match brackets that appear after the type (array dimensions)
                        # Pattern: [ followed by optional whitespace, then digits or identifier, then ]
                        type_str = re.sub(r'\[\s*[\w\d]+\s*\]', '[]', type_str)
                        
                        # Clean up extra spaces again after modifications
                        type_str = ' '.join(type_str.split())
                        
                        global_vars[node.name] = type_str if type_str else "unknown"
                    except Exception as e:
                        # Fallback: just use "unknown" if type extraction fails
                        print(f"Warning: Could not extract type for {node.name}: {e}", file=sys.stderr)
                        global_vars[node.name] = "unknown"
        
        # Recursively visit children
        for child_name, child in node.children():
            self._visit_for_globals(child, global_vars, in_function)
    
    def detect_global_usage_in_assembly(self, global_vars, function_info):
        """
        Detect reads and writes to global variables in assembly code.
        
        Args:
            global_vars: dict mapping global variable names to their types
            function_info: dict of function_name -> {'signature': str, 'assembly': str}
            
        Returns:
            dict: (global_var_name, func_name) -> {'r': bool, 'w': bool}
        """
        import re
        
        usage = {}
        
        for func_name, info in function_info.items():
            assembly = info.get('assembly', '')
            if not assembly:
                continue
            
            # Find all references to global variables in assembly
            for global_var in global_vars.keys():
                # Pattern to match global variable references in assembly
                # Look for the variable name in memory references like:
                # mov    DWORD PTR [rip+0x...], eax  (write)
                # mov    eax, DWORD PTR [rip+0x...]  (read)
                # mov    DWORD PTR global_var[rip], eax  (write)
                # mov    eax, DWORD PTR global_var[rip]  (read)
                # Also handle: global_var(%rip), global_var+offset, etc.
                
                # Check for direct references to the global variable name
                # Assembly might have: global_var(%rip), global_var[rip], global_var+offset
                var_pattern = re.escape(global_var)
                
                # Look for the variable name in the assembly
                if re.search(rf'\b{var_pattern}\b', assembly, re.IGNORECASE):
                    # Found a reference - now determine if it's a read or write
                    reads = False
                    writes = False
                    
                    # Split assembly into lines
                    lines = assembly.split('\n')
                    for line in lines:
                        if re.search(rf'\b{var_pattern}\b', line, re.IGNORECASE):
                            stripped = line.strip()
                            
                            # Skip comments and labels
                            if stripped.startswith(';') or stripped.startswith('#'):
                                continue
                            if stripped.endswith(':'):
                                continue
                            
                            # Check for write patterns (destination is memory)
                            # Pattern: mov [mem], reg or mov [mem], imm
                            # Match: mov DWORD PTR [global_var+...], reg
                            # The key is that the memory reference comes first (destination)
                            if re.search(rf'mov\s+.*\[.*{var_pattern}.*\],\s*\w+', stripped, re.IGNORECASE):
                                writes = True
                            # Check for other write instructions that modify memory
                            elif re.search(rf'(add|sub|inc|dec|and|or|xor|not)\s+.*\[.*{var_pattern}', stripped, re.IGNORECASE):
                                writes = True
                            
                            # Check for read patterns (source is memory)
                            # Pattern: mov reg, [mem] - register comes first, then memory
                            if re.search(rf'mov\s+\w+,\s*.*\[.*{var_pattern}', stripped, re.IGNORECASE):
                                reads = True
                            # Check for other read instructions
                            elif re.search(rf'(cmp|test)\s+.*\[.*{var_pattern}', stripped, re.IGNORECASE):
                                reads = True
                            # Check for lea (load effective address) - usually a read
                            elif re.search(rf'lea\s+.*\[.*{var_pattern}', stripped, re.IGNORECASE):
                                reads = True
                            # Check for push [mem] - read
                            elif re.search(rf'push\s+.*\[.*{var_pattern}', stripped, re.IGNORECASE):
                                reads = True
                            # Check for pop [mem] - write
                            elif re.search(rf'pop\s+.*\[.*{var_pattern}', stripped, re.IGNORECASE):
                                writes = True
                    
                    # If we found the variable but couldn't determine read/write, assume both
                    if not reads and not writes:
                        reads = True
                        writes = True
                    
                    usage[(global_var, func_name)] = {'r': reads, 'w': writes}
        
        return usage
    
    def update_globals_display(self):
        """Update the global variables display panel."""
        # Store the content, but only update the display if the globals tab is active
        if not self.global_variables:
            self.globals_content = "No global variables found"
        else:
            # Build display text
            lines = []
            
            # Sort global variables alphabetically
            sorted_globals = sorted(self.global_variables.items())
            
            for global_var, var_type in sorted_globals:
                # Display variable name with type in parentheses
                lines.append(f"{global_var} ({var_type}):")
                
                # Get all functions that use this global variable
                # Store as list of tuples (func_name, usage) where usage is a tuple (r, w)
                funcs_using_var = []
                for (var_name, func_name), usage in self.global_var_usage.items():
                    if var_name == global_var:
                        # Convert usage dict to tuple for sorting
                        funcs_using_var.append((func_name, (usage.get('r', False), usage.get('w', False))))
                
                if not funcs_using_var:
                    lines.append("  (no functions use this variable)")
                else:
                    # Sort functions alphabetically
                    sorted_funcs = sorted(funcs_using_var, key=lambda x: x[0])
                    
                    for func_name, (reads, writes) in sorted_funcs:
                        # Build prefix: r-, w-, or rw-
                        prefix_parts = []
                        if reads:
                            prefix_parts.append('r')
                        if writes:
                            prefix_parts.append('w')
                        
                        if prefix_parts:
                            # Join without separator, then add dash: 'r' + 'w' = 'rw-'
                            prefix = ''.join(prefix_parts) + '-'
                        else:
                            prefix = ''
                        
                        lines.append(f"  {prefix}{func_name}")
                
                lines.append("")  # Empty line between variables
            
            self.globals_content = '\n'.join(lines)
        
        # Update display if globals tab is currently active
        if self.current_data_tab == 0:
            self.data_text.setPlainText(self.globals_content)
    
    def extract_structs(self, c_filenames, include_dirs=None):
        """
        Extract struct definitions and their members from C source files.
        
        Args:
            c_filenames: List of C source file paths
            include_dirs: Optional list of include directories to add with -I flags
            
        Returns:
            dict: Mapping of struct names to {'members': [(member_name, member_type), ...]}
        """
        if include_dirs is None:
            include_dirs = []
        
        from pycparser import parse_file, c_ast
        from call_graph_extractor import _create_attribute_fix_header, _create_fake_stddef_header
        try:
            from pycparser import __file__ as pycparser_file
            # First try the local fake_libc_include directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            fake_libc_include = os.path.join(script_dir, 'fake_libc_include')
            if not os.path.isdir(fake_libc_include):
                # Fall back to pycparser's fake_libc_include
                pycparser_dir = os.path.dirname(pycparser_file)
                fake_libc_include = os.path.join(pycparser_dir, 'utils', 'fake_libc_include')
            FAKE_LIBC_AVAILABLE = os.path.isdir(fake_libc_include)
            if FAKE_LIBC_AVAILABLE:
                fake_libc_include = os.path.abspath(fake_libc_include)
        except:
            FAKE_LIBC_AVAILABLE = False
            fake_libc_include = None
        
        structs = {}
        
        # Use the same cpp_args as call_graph_extractor
        cpp_args = []
        cpp_args.extend([
            '-U__attribute__',
            '-D__attribute__(x)=',
            '-D__alignof__(x)=sizeof(x)',
            '-D__packed__=',
            '-D__aligned__(x)=',
            '-D__unused__=',
            '-D__maybe_unused__=',
            '-D__unused=',
            '-D__maybe_unused=',
        ])
        
        attr_fix_header = _create_attribute_fix_header()
        if attr_fix_header:
            cpp_args.extend(['-include', attr_fix_header])
        
        if FAKE_LIBC_AVAILABLE:
            cpp_args.extend([
                '-I' + fake_libc_include,
                '-nostdinc',
            ])
            # Add user-provided include directories
            for include_dir in include_dirs:
                cpp_args.extend(['-I', include_dir])
        else:
            fake_stddef = _create_fake_stddef_header()
            if fake_stddef:
                fake_stddef_dir = os.path.dirname(fake_stddef)
                cpp_args.extend([
                    '-I' + fake_stddef_dir,
                    '-nostdinc',
                ])
                # Add user-provided include directories
                for include_dir in include_dirs:
                    cpp_args.extend(['-I', include_dir])
            else:
                # No fake headers - add user-provided include directories anyway
                for include_dir in include_dirs:
                    cpp_args.extend(['-I', include_dir])
        
        cpp_args.extend([
            '-D__volatile__=volatile',
            '-Dvolatile=',
            '-D__restrict=',
            '-D__extension__=',
            '-Dasm=',
            '-D__asm=',
            '-D__asm__=',
            '-D__asm__(x)=',
            '-D__asm(x)=',
            '-D__inline=',
            '-D__inline__=',
            '-D__const=const',
            '-D__signed__=signed',
        ])
        
        for filename in c_filenames:
            try:
                ast = parse_file(filename, use_cpp=True, cpp_args=cpp_args)
                self._visit_for_structs(ast, structs)
            except Exception as e:
                print(f"Warning: Error parsing file {filename} for structs: {e}", file=sys.stderr)
        
        return structs
    
    def _visit_for_structs(self, node, structs):
        """Recursively visit AST nodes to find struct definitions."""
        from pycparser import c_ast, c_generator
        import re
        
        # Helper function to extract members from a Struct node
        def extract_members_from_struct(struct_node):
            """Extract member list from a Struct node."""
            members = []
            if hasattr(struct_node, 'decls') and struct_node.decls:
                generator = c_generator.CGenerator()
                for decl in struct_node.decls:
                    if isinstance(decl, c_ast.Decl) and decl.name:
                        # Extract member name and type
                        try:
                            # Generate the full declaration
                            full_decl = generator.visit(decl)
                            member_name = decl.name
                            
                            # Extract type by removing the member name
                            type_str = full_decl
                            if type_str.endswith(member_name):
                                type_str = type_str[:-len(member_name)].strip()
                            elif member_name in type_str:
                                pattern = re.escape(member_name) + r'(?=\s*[\[\(]|$|\s)'
                                type_str = re.sub(pattern, '', type_str).strip()
                            
                            # Clean up extra spaces
                            type_str = ' '.join(type_str.split())
                            
                            # Remove array sizes
                            type_str = re.sub(r'\[\s*[\w\d]+\s*\]', '[]', type_str)
                            type_str = ' '.join(type_str.split())
                            
                            if type_str:
                                members.append((member_name, type_str))
                        except Exception as e:
                            print(f"Warning: Could not extract member {decl.name if hasattr(decl, 'name') else 'unknown'}: {e}", file=sys.stderr)
            return members
        
        # Check for Decl nodes with Struct type (struct definitions at file scope)
        # Example: struct Point { int x; int y; };
        if isinstance(node, c_ast.Decl):
            if hasattr(node, 'type') and isinstance(node.type, c_ast.Struct):
                struct_node = node.type
                struct_name = None
                
                # Get struct name from the Struct node itself
                if hasattr(struct_node, 'name') and struct_node.name:
                    struct_name = struct_node.name
                
                # Extract members
                members = extract_members_from_struct(struct_node)
                
                # Store struct if it has a name or members
                if struct_name:
                    structs[struct_name] = {'members': members}
                elif members:
                    # Anonymous struct - use a generated name
                    struct_name = f"<anonymous_{len(structs)}>"
                    structs[struct_name] = {'members': members}
        
        # Check for direct Struct nodes (might be nested)
        if isinstance(node, c_ast.Struct):
            struct_name = None
            members = []
            
            # Get struct name if it's a named struct
            if hasattr(node, 'name') and node.name:
                struct_name = node.name
            
            # Get struct members
            members = extract_members_from_struct(node)
            
            # Store struct if it has a name or members (and we haven't already stored it)
            if struct_name and struct_name not in structs:
                structs[struct_name] = {'members': members}
            elif members and not struct_name:
                # Anonymous struct - use a generated name
                struct_name = f"<anonymous_{len(structs)}>"
                structs[struct_name] = {'members': members}
        
        # Also check for typedef struct definitions
        if isinstance(node, c_ast.Typedef):
            if hasattr(node, 'type') and isinstance(node.type, c_ast.Struct):
                struct_node = node.type
                struct_name = node.name if hasattr(node, 'name') and node.name else None
                
                # Extract members
                members = extract_members_from_struct(struct_node)
                
                # Also check if the struct itself has a name (for typedef struct Name { ... } Alias;)
                if hasattr(struct_node, 'name') and struct_node.name:
                    # The struct has a name, store it with that name
                    if struct_node.name not in structs:
                        structs[struct_node.name] = {'members': members}
                
                # Store with typedef name if different
                if struct_name and struct_name not in structs:
                    structs[struct_name] = {'members': members}
        
        # Recursively visit children
        for child_name, child in node.children():
            self._visit_for_structs(child, structs)
    
    def update_structs_display(self):
        """Update the structs display panel."""
        # Store the content, but only update the display if the structs tab is active
        if not self.structs:
            self.structs_content = "No structs found"
        else:
            # Build display text
            lines = []
            
            # Sort structs alphabetically
            sorted_structs = sorted(self.structs.items())
            
            for struct_name, struct_info in sorted_structs:
                # Display struct name (without 'struct' prefix)
                lines.append(f"{struct_name}:")
                
                # Display members
                members = struct_info.get('members', [])
                if not members:
                    lines.append("  (no members)")
                else:
                    for member_name, member_type in members:
                        # Format: member_name (type) - no semicolon
                        lines.append(f"  {member_name} ({member_type})")
                
                lines.append("")  # Empty line between structs
            
            self.structs_content = '\n'.join(lines)
        
        # Update display if structs tab is currently active
        if self.current_data_tab == 1:
            self.data_text.setPlainText(self.structs_content)
    
    def on_tab_changed(self, index):
        """Handle tab change to update the displayed content."""
        self.current_data_tab = index
        
        # Determine which tab is active
        if self.file_selection_tab_index >= 0 and index == self.file_selection_tab_index:
            # File selection tab - show file list
            self.data_stacked.setCurrentIndex(0)  # Show file list widget
            # Highlight the currently selected file
            self._highlight_selected_file()
        else:
            # Globals or Structs tab - show text edit
            self.data_stacked.setCurrentIndex(1)  # Show text edit
            
            # Determine if it's Globals or Structs
            if index == self.globals_tab_index:
                # Globals tab
                if hasattr(self, 'globals_content'):
                    self.data_text.setPlainText(self.globals_content)
                else:
                    self.data_text.setPlainText("No global variables found")
            elif index == self.structs_tab_index:
                # Structs tab
                if hasattr(self, 'structs_content'):
                    self.data_text.setPlainText(self.structs_content)
                else:
                    self.data_text.setPlainText("No structs found")
    
    def update_file_selection_tab(self):
        """Add or remove the file selection tab based on directory mode."""
        if self.is_directory_mode and (len(self.directory_c_files) > 0 or len(self.directory_assembly_files) > 0):
            # Add file selection tab if it doesn't exist
            if self.file_selection_tab_index < 0:
                # Insert at the beginning
                self.data_tab_bar.insertTab(0, "🗅")
                self.file_selection_tab_index = 0
                self.globals_tab_index = 1
                self.structs_tab_index = 2
            
            # Always update file list when in directory mode (including when switching directories)
            self.file_list_widget.clear()
            self.file_list_widget.addItem("(All Files)")
            # Add C files
            for c_file in sorted(self.directory_c_files):
                display_name = os.path.basename(c_file)
                self.file_list_widget.addItem(display_name)
            # Add assembly files
            for asm_file in sorted(self.directory_assembly_files):
                display_name = os.path.basename(asm_file)
                self.file_list_widget.addItem(display_name)
            self._highlight_selected_file()
        else:
            # Remove file selection tab if it exists
            if self.file_selection_tab_index >= 0:
                self.data_tab_bar.removeTab(self.file_selection_tab_index)
                self.file_selection_tab_index = -1
                self.globals_tab_index = 0
                self.structs_tab_index = 1
                # Make sure we're showing the text edit, not the file list
                self.data_stacked.setCurrentIndex(1)
    
    def _highlight_selected_file(self):
        """Highlight the currently selected file in the file list."""
        if self.file_selection_tab_index < 0:
            return
        
        # Find and select the appropriate item
        if self.selected_file_filter is None:
            # Select "(All Files)"
            for i in range(self.file_list_widget.count()):
                if self.file_list_widget.item(i).text() == "(All Files)":
                    self.file_list_widget.setCurrentRow(i)
                    break
        else:
            # Select the file that matches selected_file_filter
            filter_basename = os.path.basename(self.selected_file_filter)
            for i in range(self.file_list_widget.count()):
                if self.file_list_widget.item(i).text() == filter_basename:
                    self.file_list_widget.setCurrentRow(i)
                    break
    
    def on_file_selected(self, item):
        """Handle file selection from the file list."""
        selected_text = item.text()
        
        if selected_text == "(All Files)":
            self.selected_file_filter = None
        else:
            # Find the full path of the selected file (check both C and assembly files)
            for c_file in self.directory_c_files:
                if os.path.basename(c_file) == selected_text:
                    self.selected_file_filter = c_file
                    break
            if not self.selected_file_filter or os.path.basename(self.selected_file_filter) != selected_text:
                # Check assembly files if not found in C files
                for asm_file in self.directory_assembly_files:
                    if os.path.basename(asm_file) == selected_text:
                        self.selected_file_filter = asm_file
                        break
        
        # Highlight the selected item
        self._highlight_selected_file()
        
        # Redraw the graph with the filter
        self.draw_graph()
    
    def draw_graph(self):
        """Draw the call graph."""
        self.clear_overlay()
        self.scene.clear()
        self.nodes = {}
        self.edges = []
        self.edge_items = []
        self.call_rectangles = []
        
        if not self.functions:
            return
        
        # Filter functions based on selected file (if in directory mode)
        filtered_functions = set()
        if self.selected_file_filter and self.function_sources:
            # Only show functions from the selected file
            for func_name, source_file in self.function_sources.items():
                if source_file == self.selected_file_filter:
                    filtered_functions.add(func_name)
        else:
            # Show all functions
            filtered_functions = set(self.functions.keys())
        
        # Create nodes for filtered functions with signature and assembly
        for func_name in filtered_functions:
            # Skip functions that don't have function_info (e.g., assembly-only functions without proper entry)
            if func_name not in self.function_info:
                continue
                
            info = self.function_info.get(func_name, {})
            signature = info.get('signature', f"{func_name}()")
            assembly = info.get('assembly', "Assembly unavailable")
            
            # Pass call graph information to the node; on_toggle refreshes overlay if shown
            node = FunctionNode(func_name, signature, assembly, 0, 0, 
                              calls=self.calls, function_info=self.function_info,
                              on_toggle_cb=lambda n: self.refresh_overlay_if_showing(n))
            self.nodes[func_name] = node
            self.scene.addItem(node)
        
        # Create edges for function calls (only between filtered functions)
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
        
        # Draw jump arrows within each function node
        for func_name, node in self.nodes.items():
            self.draw_jump_arrows(node)
        
        # Draw function call rectangles with arguments
        self.draw_function_calls()
    
    def find_call_line_in_assembly(self, assembly, callee_name):
        """Find the line number (0-indexed) in processed assembly that contains call to callee_name.
        Uses the same processing as color_code_assembly to ensure line numbers match."""
        import re
        if not assembly:
            return None
        
        # Process assembly the same way as color_code_assembly does
        lines = assembly.split('\n')
        cleaned_lines = []
        skip_initial_labels = True
        function_name_removed = False
        
        for line in lines:
            stripped = line.strip()
            
            # Remove file location annotations
            if re.match(r'^@[^\s]+\.s\s+\(\d+-\d+\)', stripped):
                continue
            
            # Remove function name lines (only first occurrence)
            if not function_name_removed and re.match(r'^\s*\w+\s*:', stripped):
                label_name = stripped.split(':')[0].strip()
                if not label_name.startswith('.'):
                    function_name_removed = True
                    continue
            
            # Remove initial local labels like .LFB0:
            if skip_initial_labels:
                if re.match(r'^\s*\.LFB\d+\s*:', stripped):
                    continue
                if stripped and not re.match(r'^\s*\.LFB\d+\s*:', stripped):
                    skip_initial_labels = False
            
            # Keep all other lines
            cleaned_lines.append(line)
        
        # Now search in the cleaned lines
        call_pattern = re.compile(r'\bcall\b.*\b' + re.escape(callee_name) + r'\b', re.IGNORECASE)
        
        for i, line in enumerate(cleaned_lines):
            if call_pattern.search(line):
                return i
        
        return None
    
    def find_entry_point_line(self, assembly):
        """Find the line number (0-indexed) of the entry point (first actual instruction).
        Uses the same processing as color_code_assembly to ensure line numbers match."""
        import re
        
        if not assembly:
            return 0
        
        # Process assembly the same way as color_code_assembly does
        lines = assembly.split('\n')
        cleaned_lines = []
        skip_initial_labels = True
        function_name_removed = False
        
        for line in lines:
            stripped = line.strip()
            
            # Remove file location annotations
            if re.match(r'^@[^\s]+\.s\s+\(\d+-\d+\)', stripped):
                continue
            
            # Remove function name lines (only first occurrence)
            if not function_name_removed and re.match(r'^\s*\w+\s*:', stripped):
                label_name = stripped.split(':')[0].strip()
                if not label_name.startswith('.'):
                    function_name_removed = True
                    continue
            
            # Remove initial local labels like .LFB0:
            if skip_initial_labels:
                if re.match(r'^\s*\.LFB\d+\s*:', stripped):
                    continue
                if stripped and not re.match(r'^\s*\.LFB\d+\s*:', stripped):
                    skip_initial_labels = False
            
            # Keep all other lines
            cleaned_lines.append(line)
        
        # Now find entry point in cleaned lines
        for i, line in enumerate(cleaned_lines):
            stripped = line.strip()
            if not stripped:  # Empty line
                continue
            # Found first non-empty line (this is the entry point after cleaning)
            return i
        
        return 0
    
    def process_assembly_for_jumps(self, assembly):
        """Process assembly the same way as color_code_assembly and return cleaned lines.
        Returns tuple: (cleaned_lines, line_mapping) where line_mapping maps original line indices to cleaned indices."""
        import re
        
        if not assembly:
            return [], {}
        
        lines = assembly.split('\n')
        cleaned_lines = []
        line_mapping = {}  # Maps original line index to cleaned line index
        skip_initial_labels = True
        function_name_removed = False
        
        for orig_idx, line in enumerate(lines):
            stripped = line.strip()
            
            # Remove file location annotations
            if re.match(r'^@[^\s]+\.s\s+\(\d+-\d+\)', stripped):
                continue
            
            # Remove function name lines (only first occurrence)
            if not function_name_removed and re.match(r'^\s*\w+\s*:', stripped):
                label_name = stripped.split(':')[0].strip()
                if not label_name.startswith('.'):
                    function_name_removed = True
                    continue
            
            # Remove initial local labels like .LFB0:
            if skip_initial_labels:
                if re.match(r'^\s*\.LFB\d+\s*:', stripped):
                    continue
                if stripped and not re.match(r'^\s*\.LFB\d+\s*:', stripped):
                    skip_initial_labels = False
            
            # Keep all other lines
            cleaned_idx = len(cleaned_lines)
            cleaned_lines.append(line)
            line_mapping[orig_idx] = cleaned_idx
        
        return cleaned_lines, line_mapping
    
    def find_jumps_in_assembly(self, assembly):
        """Find all jump instructions and their target labels.
        Returns list of tuples: (jump_line_index, target_label) where jump_line_index is 0-indexed in cleaned assembly."""
        import re
        
        if not assembly:
            return []
        
        # Process assembly the same way as color_code_assembly
        cleaned_lines, _ = self.process_assembly_for_jumps(assembly)
        
        # Jump instruction patterns (excluding call and ret)
        jump_patterns = [
            r'\bjmp\b',
            r'\bje\b', r'\bjz\b',
            r'\bjne\b', r'\bjnz\b',
            r'\bja\b', r'\bjae\b',
            r'\bjb\b', r'\bjbe\b',
            r'\bjg\b', r'\bjge\b',
            r'\bjl\b', r'\bjle\b',
            r'\bjc\b', r'\bjnc\b',
            r'\bjo\b', r'\bjno\b',
            r'\bjs\b', r'\bjns\b',
            r'\bjp\b', r'\bjnp\b',
        ]
        
        jump_instructions = []
        
        for line_idx, line in enumerate(cleaned_lines):
            stripped = line.strip()
            if not stripped:
                continue
            
            # Check if this line contains a jump instruction
            for pattern in jump_patterns:
                if re.search(pattern, stripped, re.IGNORECASE):
                    # Extract target label/address
                    # Pattern: jmp label or jmp .L123 or jmp 0x1234
                    # Try to find label after jump instruction
                    jump_match = re.search(pattern, stripped, re.IGNORECASE)
                    if jump_match:
                        # Get text after the jump instruction
                        after_jump = stripped[jump_match.end():].strip()
                        if after_jump:
                            # Extract potential label (could be .L123, label_name, or address)
                            # Remove comments
                            if '#' in after_jump or ';' in after_jump:
                                comment_pos = min(
                                    after_jump.find('#') if '#' in after_jump else len(after_jump),
                                    after_jump.find(';') if ';' in after_jump else len(after_jump)
                                )
                                after_jump = after_jump[:comment_pos].strip()
                            
                            # Try to match label patterns
                            # Label can be: .L123, label_name, or *label (indirect)
                            # Also handle cases like: jmp .L123 or jmp label_name
                            # Skip if it's a register or immediate value (hex/decimal numbers)
                            # Pattern: not starting with $, %, 0x, or pure digits
                            if not re.match(r'^[\$%]|^0x[0-9a-f]+|^\d+', after_jump, re.IGNORECASE):
                                label_match = re.match(r'^\*?([\w.]+)', after_jump)
                                if label_match:
                                    target_label = label_match.group(1)
                                    # Skip if it looks like a register (common x86 registers)
                                    if target_label.lower() not in ['rax', 'rbx', 'rcx', 'rdx', 'rsi', 'rdi', 'rbp', 'rsp', 'rip',
                                                                     'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp', 'eip',
                                                                     'ax', 'bx', 'cx', 'dx', 'si', 'di', 'bp', 'sp', 'ip']:
                                        jump_instructions.append((line_idx, target_label))
                                        break
        
        return jump_instructions
    
    def find_label_line(self, assembly, target_label):
        """Find the line number (0-indexed) in processed assembly where target_label appears.
        Returns None if label not found."""
        import re
        
        if not assembly:
            return None
        
        # Process assembly the same way as color_code_assembly
        cleaned_lines, _ = self.process_assembly_for_jumps(assembly)
        
        # Look for label definition (label: or label followed by :)
        # Pattern: label: or .L123: or label followed by whitespace and :
        label_pattern = re.compile(r'^\s*' + re.escape(target_label) + r'\s*:', re.IGNORECASE)
        
        for line_idx, line in enumerate(cleaned_lines):
            if label_pattern.match(line.strip()):
                return line_idx
        
        return None
    
    def get_line_y_position_in_body(self, node, line_number):
        """Get the y-position (relative to node's top) of a specific line in the assembly body.
        line_number should be 0-indexed and correspond to the processed assembly (after cleaning).
        
        This function processes the raw assembly the same way as find_call_line_in_assembly
        to ensure line numbers match correctly."""
        from PyQt5.QtGui import QFontMetrics
        import re
        
        if line_number < 0:
            line_number = 0
        
        # Calculate approximate line height
        font = QFont("Courier", 7)
        metrics = QFontMetrics(font)
        line_height = metrics.height()
        
        # Process the raw assembly the same way as find_call_line_in_assembly does
        # This ensures we're counting lines consistently
        assembly = node.assembly
        if not assembly:
            # Fallback if no assembly
            body_y_offset = node.signature_rect.height() + node.call_graph_registers_rect.height() + node.func_registers_rect.height()
            return body_y_offset + 5 + line_number * line_height + line_height / 2
        
        # Process assembly the same way as color_code_assembly and find_call_line_in_assembly
        lines = assembly.split('\n')
        cleaned_lines = []
        skip_initial_labels = True
        function_name_removed = False
        
        for line in lines:
            stripped = line.strip()
            
            # Remove file location annotations
            if re.match(r'^@[^\s]+\.s\s+\(\d+-\d+\)', stripped):
                continue
            
            # Remove function name lines (only first occurrence)
            if not function_name_removed and re.match(r'^\s*\w+\s*:', stripped):
                label_name = stripped.split(':')[0].strip()
                if not label_name.startswith('.'):
                    function_name_removed = True
                    continue
            
            # Remove initial local labels like .LFB0:
            if skip_initial_labels:
                if re.match(r'^\s*\.LFB\d+\s*:', stripped):
                    continue
                if stripped and not re.match(r'^\s*\.LFB\d+\s*:', stripped):
                    skip_initial_labels = False
            
            # Keep all other lines
            cleaned_lines.append(line)
        
        # Now we have the cleaned lines that match what's displayed
        # The line_number corresponds to an index in cleaned_lines
        # Verify that line_number is within bounds
        if line_number >= len(cleaned_lines):
            line_number = len(cleaned_lines) - 1
            if line_number < 0:
                line_number = 0
        
        # Get the document to try to get accurate line positions
        assembly_text = node.assembly_text
        assembly_doc = assembly_text.document()
        
        # Ensure the document is laid out
        assembly_doc.setTextWidth(assembly_text.textWidth())
        
        # Try to get accurate position from the document by counting lines
        # The HTML document should have the same number of lines as cleaned_lines
        # (since we convert \n to <br>)
        block = assembly_doc.firstBlock()
        doc_lines_counted = 0
        y_pos = 0
        found_exact = False
        
        while block.isValid() and doc_lines_counted <= line_number:
            block_layout = block.layout()
            if block_layout:
                lines_in_block = block_layout.lineCount()
                
                if doc_lines_counted <= line_number < doc_lines_counted + lines_in_block:
                    # Target line is in this block
                    target_line_idx = line_number - doc_lines_counted
                    if target_line_idx >= 0 and target_line_idx < lines_in_block:
                        target_line = block_layout.lineAt(target_line_idx)
                        if target_line.isValid():
                            # Get the center y-position of the line from the document
                            line_rect = target_line.naturalTextRect()
                            y_pos = block_layout.position().y() + line_rect.y() + line_rect.height() / 2
                            found_exact = True
                            break
                    # If line index is out of range, use end of block
                    if not found_exact:
                        y_pos = block_layout.position().y() + block_layout.boundingRect().height()
                        found_exact = True
                        break
                
                # Accumulate position for blocks before the target
                if not found_exact:
                    y_pos = block_layout.position().y() + block_layout.boundingRect().height()
                    doc_lines_counted += lines_in_block
            else:
                # Block with no layout - count as one line
                if doc_lines_counted == line_number:
                    y_pos = doc_lines_counted * line_height + line_height / 2
                    found_exact = True
                    break
                y_pos = (doc_lines_counted + 1) * line_height
                doc_lines_counted += 1
                if doc_lines_counted > line_number:
                    break
            
            block = block.next()
        
        # Fallback: if we didn't find exact position, use simple calculation
        if not found_exact:
            y_pos = line_number * line_height + line_height / 2
        
        # Add the base y-offset of the assembly text within the node
        # The assembly text starts at body_rect.y() + 5 (padding)
        body_y_offset = node.signature_rect.height() + node.call_graph_registers_rect.height() + node.func_registers_rect.height()
        return body_y_offset + 5 + y_pos
    
    def draw_edge(self, caller, callee):
        """Draw an edge between two nodes, pointing from the call line to the entry point."""
        if caller not in self.nodes or callee not in self.nodes:
            return
            
        caller_node = self.nodes[caller]
        callee_node = self.nodes[callee]
        
        # Calculate line endpoints (on the edges of rectangles)
        caller_rect = caller_node.rect()
        callee_rect = callee_node.rect()
        
        # Find the call line in caller's assembly and entry point in callee's assembly
        call_line = self.find_call_line_in_assembly(caller_node.assembly, callee)
        entry_line = self.find_entry_point_line(callee_node.assembly)
        
        # Get y-positions within the body rectangles
        if call_line is not None:
            caller_body_y = self.get_line_y_position_in_body(caller_node, call_line)
        else:
            # Fallback to center of body if call line not found
            caller_body_y = (caller_node.signature_rect.height() + 
                           caller_node.call_graph_registers_rect.height() + 
                           caller_node.func_registers_rect.height() + 
                           caller_node.body_rect.height() / 2)
        
        callee_body_y = self.get_line_y_position_in_body(callee_node, entry_line)
        
        # Calculate x-positions (center of rectangles)
        caller_x = caller_rect.width() / 2
        callee_x = callee_rect.width() / 2
        
        # Convert to scene coordinates - use actual line positions
        caller_line_y = caller_node.scenePos().y() + caller_body_y
        callee_line_y = callee_node.scenePos().y() + callee_body_y
        
        # Calculate direction vector
        # Force arrows to always go rightwards (callee should always be to the right of caller)
        dx = callee_node.scenePos().x() - caller_node.scenePos().x()
        dy = callee_line_y - caller_line_y
        
        # If callee is to the left of caller (shouldn't happen with proper layout, but handle it)
        # Force it to go right by ensuring minimum horizontal distance
        min_horizontal_distance = 100  # Minimum horizontal distance for arrows
        if dx < min_horizontal_distance:
            # Adjust callee position for arrow drawing (visual only, doesn't change node position)
            dx = min_horizontal_distance
        
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        # Normalize
        dx_norm = dx / length
        dy_norm = dy / length
        
        # Calculate start and end points on rectangle edges
        # Always exit from right edge of caller and enter at left edge of callee
        start_point = QPointF(caller_node.scenePos().x() + caller_rect.width(), caller_line_y)
        end_point = QPointF(callee_node.scenePos().x(), callee_line_y)
        
        # Clamp start point y to rectangle bounds
        start_point.setY(max(caller_node.scenePos().y(), 
                             min(caller_node.scenePos().y() + caller_rect.height(), start_point.y())))
        
        # Clamp end point y to rectangle bounds
        end_point.setY(max(callee_node.scenePos().y(), 
                          min(callee_node.scenePos().y() + callee_rect.height(), end_point.y())))
        
        # Recalculate direction for curved path
        dx = end_point.x() - start_point.x()
        dy = end_point.y() - start_point.y()
        length = math.sqrt(dx * dx + dy * dy)
        if length > 0:
            dx_norm = dx / length
            dy_norm = dy / length
        else:
            dx_norm = 1.0
            dy_norm = 0.0
        
        # Create curved path using cubic bezier
        path = QPainterPath()
        path.moveTo(start_point)
        
        # Calculate control points for a smooth curve
        # The curve should bend naturally from start to end
        # Control points are positioned to create a smooth S-curve or arc
        curve_strength = min(length * 0.5, 150)  # Control how much the curve bends
        
        # For left-to-right flow, create a gentle curve
        # Control point 1: slightly offset from start in the direction of travel
        ctrl1_x = start_point.x() + curve_strength * dx_norm
        ctrl1_y = start_point.y() + curve_strength * dy_norm * 0.3  # Less vertical movement
        
        # Control point 2: slightly offset from end in the opposite direction
        ctrl2_x = end_point.x() - curve_strength * dx_norm
        ctrl2_y = end_point.y() - curve_strength * dy_norm * 0.3
        
        # Create the cubic bezier curve
        path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, end_point.x(), end_point.y())
        
        # Create path item
        path_item = QGraphicsPathItem(path)
        pen = QPen(QColor(100, 100, 100), 2)
        pen.setStyle(Qt.DashLine)
        path_item.setPen(pen)
        self.scene.addItem(path_item)
        self.edge_items.append(path_item)
        
        # Add arrowhead at the end
        arrow_size = 10
        # Calculate angle at end point (tangent to the curve)
        # Use the direction from the last control point to the end point
        dx_end = end_point.x() - ctrl2_x
        dy_end = end_point.y() - ctrl2_y
        if dx_end == 0 and dy_end == 0:
            # Fallback: use overall direction
            angle = math.atan2(dy, dx)
        else:
            length_end = math.sqrt(dx_end * dx_end + dy_end * dy_end)
            if length_end > 0:
                dx_end /= length_end
                dy_end /= length_end
            angle = math.atan2(dy_end, dx_end)
        
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
        
        # Calculate and display shared registers at the center of the curve
        # Get point at t=0.5 along the curve
        t = 0.5
        # Cubic bezier formula: (1-t)^3*P0 + 3*(1-t)^2*t*P1 + 3*(1-t)*t^2*P2 + t^3*P3
        mt = 1 - t
        center_point = QPointF(
            mt*mt*mt * start_point.x() + 3*mt*mt*t * ctrl1_x + 3*mt*t*t * ctrl2_x + t*t*t * end_point.x(),
            mt*mt*mt * start_point.y() + 3*mt*mt*t * ctrl1_y + 3*mt*t*t * ctrl2_y + t*t*t * end_point.y()
        )
        
        # Extract registers from both caller and callee
        caller_registers = caller_node.extract_registers_from_assembly(caller_node.assembly)
        callee_registers = callee_node.extract_registers_from_assembly(callee_node.assembly)
        
        # Find intersection (registers used by both)
        shared_registers = caller_registers.intersection(callee_registers)
        
        # Format and display shared registers if any
        if shared_registers:
            shared_registers_text = caller_node.format_registers(shared_registers)
            
            # Create text item for shared registers
            register_label = QGraphicsTextItem()
            register_label.setDefaultTextColor(QColor(255, 255, 255))
            font = QFont("Courier", 6)
            font.setBold(False)
            register_label.setFont(font)
            register_label.setHtml(shared_registers_text)
            
            # Get text dimensions after setting HTML
            # Use document size for more accurate measurement
            text_doc = register_label.document()
            text_doc.setTextWidth(-1)  # No width constraint for measurement
            text_size = text_doc.size()
            text_width = text_size.width()
            text_height = text_size.height()
            
            # Position the label at the center of the arrow
            # Adjust position to account for text size (center it)
            label_x = center_point.x() - text_width / 2
            label_y = center_point.y() - text_height / 2
            register_label.setPos(label_x, label_y)
            
            # Add a semi-transparent background for better visibility
            bg_rect = QGraphicsRectItem(
                label_x - 3, label_y - 2,
                text_width + 6, text_height + 4
            )
            bg_brush = QBrush(QColor(0, 0, 0, 200))  # Semi-transparent black
            bg_rect.setBrush(bg_brush)
            bg_rect.setPen(QPen(QColor(100, 100, 100, 150), 1))
            bg_rect.setZValue(10)  # Ensure it's above the arrow
            register_label.setZValue(11)  # Above the background
            
            self.scene.addItem(bg_rect)
            self.scene.addItem(register_label)
            self.edge_items.append(bg_rect)
            self.edge_items.append(register_label)
    
    def draw_jump_arrows(self, node):
        """Draw arrows from jump instructions to their target labels within a function node."""
        if not node.assembly:
            return
        
        # Find all jumps in the assembly
        jumps = self.find_jumps_in_assembly(node.assembly)
        
        for jump_line_idx, target_label in jumps:
            # Find the target label line
            target_line_idx = self.find_label_line(node.assembly, target_label)
            
            if target_line_idx is None:
                # Target label not found, skip this jump
                continue
            
            # Skip if jump and target are the same line (no arrow needed)
            if jump_line_idx == target_line_idx:
                continue
            
            # Get y-positions for both lines within the node
            jump_y = self.get_line_y_position_in_body(node, jump_line_idx)
            target_y = self.get_line_y_position_in_body(node, target_line_idx)
            
            # Calculate positions relative to node
            node_rect = node.rect()
            node_x = node.scenePos().x()
            node_y = node.scenePos().y()
            
            # Draw arrow from right edge of node at jump line to right edge at target line
            # Use a curved or angled arrow to make it clear
            start_x = node_x + node_rect.width()
            start_y = node_y + jump_y
            end_x = node_x + node_rect.width()
            end_y = node_y + target_y
            
            # Add a horizontal offset to make the arrow visible outside the node
            arrow_offset = 30  # Pixels to extend beyond the node
            
            # Determine if this is a forward or backward jump
            is_forward = target_line_idx > jump_line_idx
            
            # Create a curved path: start -> right offset -> end
            # Use QPainterPath for a smooth curve
            path = QPainterPath()
            path.moveTo(start_x, start_y)
            
            # Create a bezier curve with control points
            # For forward jumps, curve goes right then down
            # For backward jumps, curve goes right then up
            mid_x = start_x + arrow_offset
            mid_y = (start_y + end_y) / 2
            
            # Use cubic bezier for smoother curves
            # Control points: one near start, one near end
            ctrl1_x = start_x + arrow_offset * 0.5
            ctrl1_y = start_y
            ctrl2_x = start_x + arrow_offset * 0.5
            ctrl2_y = end_y
            
            path.cubicTo(ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, end_x, end_y)
            
            # Create a path item
            path_item = QGraphicsPathItem(path)
            
            # Use a different color/style for jump arrows to distinguish from call edges
            pen = QPen(QColor(255, 200, 0), 1.5)  # Orange/yellow color
            pen.setStyle(Qt.SolidLine)  # Solid line for jumps
            path_item.setPen(pen)
            self.scene.addItem(path_item)
            self.edge_items.append(path_item)
            
            # Add arrowhead at the end
            arrow_size = 8
            # Calculate angle at end point (tangent to the curve)
            # Use the direction from the last control point to the end point
            dx = end_x - ctrl2_x
            dy = end_y - ctrl2_y
            if dx == 0 and dy == 0:
                # Fallback: use vertical direction based on jump direction
                angle = math.pi / 2 if is_forward else -math.pi / 2
            else:
                length = math.sqrt(dx * dx + dy * dy)
                if length > 0:
                    dx /= length
                    dy /= length
                angle = math.atan2(dy, dx)
            
            arrow_p1 = QPointF(end_x, end_y) - QPointF(
                arrow_size * math.cos(angle - math.pi / 6),
                arrow_size * math.sin(angle - math.pi / 6)
            )
            arrow_p2 = QPointF(end_x, end_y) - QPointF(
                arrow_size * math.cos(angle + math.pi / 6),
                arrow_size * math.sin(angle + math.pi / 6)
            )
            
            arrow1 = QGraphicsLineItem(
                end_x, end_y,
                arrow_p1.x(), arrow_p1.y()
            )
            arrow1.setPen(pen)
            self.scene.addItem(arrow1)
            self.edge_items.append(arrow1)
            
            arrow2 = QGraphicsLineItem(
                end_x, end_y,
                arrow_p2.x(), arrow_p2.y()
            )
            arrow2.setPen(pen)
            self.scene.addItem(arrow2)
            self.edge_items.append(arrow2)
    
    def auto_layout(self):
        """Automatically layout nodes in a hierarchical left-to-right manner."""
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
        
        # Build adjacency lists for both directions
        # incoming_edges: node -> set of nodes that call it
        # outgoing_edges: node -> set of nodes it calls
        incoming_edges = defaultdict(set)
        outgoing_edges = defaultdict(set)
        
        for caller, callee in self.edges:
            if caller in self.nodes and callee in self.nodes:
                outgoing_edges[caller].add(callee)  
                incoming_edges[callee].add(caller)
        
        # Find root nodes (nodes with no incoming edges)
        # If no roots exist (all nodes are in cycles), pick nodes with fewest incoming edges
        root_nodes = [node for node in node_list if len(incoming_edges[node]) == 0]
        
        if not root_nodes:
            # All nodes are in cycles - pick nodes with minimum incoming edges
            min_incoming = min(len(incoming_edges[node]) for node in node_list)
            root_nodes = [node for node in node_list if len(incoming_edges[node]) == min_incoming]
        
        # Assign levels ensuring callees are always to the right of callers
        # Use iterative constraint satisfaction: if A calls B, then level(B) > level(A)
        levels = {}  # node -> level (0-based, left to right)
        
        # Initialize all nodes: root nodes to 0, others to a high value
        for node in node_list:
            if node in root_nodes:
                levels[node] = 0
            else:
                levels[node] = len(node_list)  # Start high, will be reduced by constraints
        
        # Iteratively enforce constraints until convergence
        # Constraint: if caller calls callee, then level(callee) >= level(caller) + 1
        changed = True
        max_iterations = len(node_list) * 2  # Prevent infinite loops
        iteration = 0
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            # For each edge, enforce the constraint
            for caller, callee in self.edges:
                if caller in self.nodes and callee in self.nodes:
                    # Callee must be at least one level to the right of caller
                    required_level = levels[caller] + 1
                    if levels[callee] < required_level:
                        levels[callee] = required_level
                        changed = True
        
        # Handle any nodes that weren't reached (shouldn't happen, but safety check)
        # Place disconnected components to the right
        max_level = max(levels.values()) if levels else -1
        for node in node_list:
            if node not in levels:
                levels[node] = max_level + 1
        
        # Group nodes by level
        nodes_by_level = defaultdict(list)
        for node, level in levels.items():
            nodes_by_level[level].append(node)
        
        # Calculate spacing - equal horizontal spacing between all levels
        horizontal_padding = 750  # Fixed equal spacing from right edge of one level to left edge of next
        vertical_padding = max_height * 0.3 + 20     # Smaller vertical spacing within levels
        
        # Position nodes level by level (left to right shows call hierarchy)
        start_x = 50
        start_y = 50
        
        # Find the maximum width and total height for each level
        level_max_widths = {}  # level -> max width of nodes in that level
        max_level_height = 0
        for level in sorted(nodes_by_level.keys()):
            level_nodes = nodes_by_level[level]
            # Sort nodes within this level by number of unique function calls (descending)
            level_nodes_sorted = sorted(level_nodes, key=lambda node_name: len(outgoing_edges.get(node_name, set())), reverse=True)
            
            # Find maximum width in this level
            max_width_in_level = max(self.nodes[node].rect().width() for node in level_nodes_sorted)
            level_max_widths[level] = max_width_in_level
            
            # Calculate total height needed for this level
            total_height = sum(self.nodes[node].rect().height() for node in level_nodes_sorted)
            total_height += vertical_padding * (len(level_nodes_sorted) - 1)
            max_level_height = max(max_level_height, total_height)
        
        # Position nodes level by level, ensuring equal spacing from right edge to left edge
        # Store node positions as we go for centering callees with callers
        node_positions = {}  # node_name -> (x, y) position
        
        current_x = start_x
        for level in sorted(nodes_by_level.keys()):
            level_nodes = nodes_by_level[level]
            x = current_x
            
            # Sort nodes within this level by number of unique function calls (descending)
            # Functions with more unique calls appear higher in the stack
            level_nodes_sorted = sorted(level_nodes, key=lambda node_name: len(outgoing_edges.get(node_name, set())), reverse=True)
            
            # Calculate total height needed for this level
            total_height = sum(self.nodes[node].rect().height() for node in level_nodes_sorted)
            total_height += vertical_padding * (len(level_nodes_sorted) - 1)
            
            # Determine starting Y position for this level
            if level == 0:
                # Root level: start from top
                current_y = start_y
            else:
                # For subsequent levels, center callees with their callers
                # Find all callers in the previous level that call nodes in this level
                prev_level = level - 1
                caller_centers = set()  # Use set to avoid duplicates
                
                for caller_name in nodes_by_level.get(prev_level, []):
                    # Check if this caller calls any node in the current level
                    callees = outgoing_edges.get(caller_name, set())
                    # Check if any of the caller's callees are in the current level
                    callees_in_level = [callee for callee in callees if callee in level_nodes]
                    if callees_in_level:
                        # Get the caller's position - use actual node position for accuracy
                        caller_node = self.nodes[caller_name]
                        caller_rect = caller_node.rect()
                        caller_pos = caller_node.pos()
                        caller_y = caller_pos.y()
                        # Calculate center Y of the caller node
                        caller_center_y = caller_y + caller_rect.height() / 2
                        caller_centers.add(caller_center_y)
                
                if caller_centers:
                    # Center the callees with the average center Y of their callers
                    target_center_y = sum(caller_centers) / len(caller_centers)
                    # Position nodes so their center aligns with target_center_y
                    current_y = target_center_y - total_height / 2
                else:
                    # No callers found, fall back to top alignment
                    current_y = start_y
            
            # Position each node in this level
            for node_name in level_nodes_sorted:
                node = self.nodes[node_name]
                node_rect = node.rect()
                node.setPos(x, current_y)
                node_positions[node_name] = (x, current_y)
                current_y += node_rect.height() + vertical_padding
            
            # Update current_x for next level: right edge of current level + padding
            current_x = x + level_max_widths[level] + horizontal_padding
        
        # Redraw edges with new positions
        for caller, callee in self.edges:
            self.draw_edge(caller, callee)
    
    def draw_function_calls(self):
        """Draw rounded rectangles displaying function calls and their arguments."""
        # Remove existing call rectangles first
        for call_rect in self.call_rectangles:
            if call_rect.scene():
                self.scene.removeItem(call_rect)
        self.call_rectangles = []
        
        if not self.calls_with_args:
            return
        
        # For each function that makes calls, create call rectangles
        for caller_name, call_list in self.calls_with_args.items():
            if caller_name not in self.nodes:
                continue
            
            caller_node = self.nodes[caller_name]
            caller_rect = caller_node.rect()
            caller_pos = caller_node.scenePos()
            
            # Position call rectangles to the right of the function node
            x_offset = caller_rect.width() + 20  # Space between node and call rectangles
            y_start = caller_pos.y() + 10  # Start slightly below top of node
            
            # Group calls by callee name for better organization
            calls_by_callee = defaultdict(list)
            for callee, args in call_list:
                calls_by_callee[callee].append(args)
            
            # Create a rectangle for each unique callee with all its call sites
            y_pos = y_start
            for callee_name, args_list in calls_by_callee.items():
                # Create call rectangle
                call_rect = FunctionCallRectangle(caller_name, callee_name, args_list, 
                                                  caller_pos.x() + x_offset, y_pos)
                self.scene.addItem(call_rect)
                self.call_rectangles.append(call_rect)
                
                # Update y position for next rectangle
                y_pos += call_rect.rect().height() + 10  # 10 pixels spacing between rectangles


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
