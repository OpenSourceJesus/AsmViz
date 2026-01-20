"""
Call Graph Visualizer using PyQt5
Displays a call graph as an interactive graph visualization.
"""

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,
                             QGraphicsView, QGraphicsScene, QGraphicsRectItem,
                             QGraphicsTextItem, QGraphicsLineItem, QMessageBox)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QFont, QPen, QBrush, QColor, QPainter, QPainterPath
import sys
import math
from collections import defaultdict


class FunctionNode(QGraphicsRectItem):
    """Represents a function node with signature and assembly body."""
    
    def __init__(self, name, signature, assembly, x, y, width=250, min_height=60):
        # Calculate required heights
        signature_height = self.calculate_text_height(signature, width - 10, 7, bold=True)
        formatted_asm = self.format_assembly(assembly)
        assembly_height = self.calculate_text_height(formatted_asm, width - 10, 7, bold=False)
        
        # Set heights with padding
        signature_rect_height = max(40, signature_height + 10)  # Min 40, or content + padding
        assembly_rect_height = max(60, assembly_height + 10)  # Min 60, or content + padding
        
        total_height = signature_rect_height + assembly_rect_height
        
        super().__init__(0, 0, width, total_height)
        self.name = name
        self.signature = signature
        self.assembly = assembly
        self.setPos(x, y)
        self.setPen(QPen(QColor(50, 100, 200), 2))
        self.setFlag(QGraphicsRectItem.ItemIsMovable, True)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        
        # Set rounded rectangle appearance
        self.setBrush(QBrush(QColor(100, 150, 255)))
        
        # Create two rectangles for signature and body
        corner_radius = 10
        
        # Top rectangle (signature)
        self.signature_rect = QRectF(0, 0, width, signature_rect_height)
        self.signature_brush = QBrush(QColor(80, 130, 235))
        
        # Bottom rectangle (assembly) - dynamically sized
        self.body_rect = QRectF(0, signature_rect_height, width, assembly_rect_height)
        self.body_brush = QBrush(QColor(100, 150, 255))
        
        # Add signature text
        self.signature_text = QGraphicsTextItem(self.format_signature(signature), self)
        self.signature_text.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Courier", 7)
        font.setBold(True)
        self.signature_text.setFont(font)
        self.signature_text.setPos(5, 5)
        self.signature_text.setTextWidth(width - 10)
        
        # Add assembly text
        self.assembly_text = QGraphicsTextItem(formatted_asm, self)
        self.assembly_text.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Courier", 7)
        self.assembly_text.setFont(font)
        self.assembly_text.setPos(5, signature_rect_height + 5)
        self.assembly_text.setTextWidth(width - 10)
        
        # Enable text wrapping and ensure it's visible
        self.assembly_text.setOpenExternalLinks(False)
    
    def calculate_text_height(self, text, text_width, font_size, bold=False):
        """Calculate the height needed to display text."""
        from PyQt5.QtGui import QFontMetrics
        font = QFont("Courier", font_size)
        if bold:
            font.setBold(True)
        metrics = QFontMetrics(font)
        line_height = metrics.height()
        
        # Count lines and calculate wrapped height
        lines = text.split('\n')
        total_height = 0
        for line in lines:
            if line.strip():
                # Calculate how many wrapped lines this line will take
                wrapped_rect = metrics.boundingRect(0, 0, int(text_width), 0, 
                                                    Qt.TextWordWrap, line)
                wrapped_height = wrapped_rect.height()
                if wrapped_height == 0:
                    wrapped_height = line_height
                total_height += wrapped_height
            else:
                # Empty line still takes space
                total_height += line_height
        
        return total_height
    
    def format_signature(self, signature):
        """Format signature text to fit in rectangle."""
        # Truncate if too long
        max_chars = 40
        if len(signature) > max_chars:
            return signature[:max_chars-3] + "..."
        return signature
    
    def format_assembly(self, assembly):
        """Format assembly text - show all lines, truncate very long lines."""
        if not assembly or assembly.strip() == "":
            return "No assembly available"
        
        lines = assembly.split('\n')
        # Keep all lines, just truncate very long individual lines
        display_lines = []
        for line in lines:
            # Truncate very long lines for display
            if len(line) > 70:
                line = line[:67] + '...'
            display_lines.append(line)
        
        result = '\n'.join(display_lines)
        return result
    
    def paint(self, painter, option, widget=None):
        """Custom paint to draw rounded rectangles."""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw top rounded rectangle (signature)
        path1 = QPainterPath()
        path1.addRoundedRect(self.signature_rect, 10, 10)
        painter.fillPath(path1, self.signature_brush)
        painter.strokePath(path1, self.pen())
        
        # Draw bottom rounded rectangle (body)
        path2 = QPainterPath()
        path2.addRoundedRect(self.body_rect, 10, 10)
        painter.fillPath(path2, self.body_brush)
        painter.strokePath(path2, self.pen())
        
        # Draw separator line between signature and assembly
        separator_y = self.signature_rect.height()
        painter.setPen(QPen(QColor(50, 100, 200), 1))
        painter.drawLine(QPointF(0, separator_y), 
                        QPointF(self.rect().width(), separator_y))
    
    def set_highlighted(self, highlighted):
        """Highlight or unhighlight the node."""
        if highlighted:
            self.signature_brush = QBrush(QColor(255, 150, 100))
            self.body_brush = QBrush(QColor(255, 130, 80))
            self.setPen(QPen(QColor(255, 100, 50), 3))
        else:
            self.signature_brush = QBrush(QColor(80, 130, 235))
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
        
        self.layout_button = QPushButton("Auto Layout")
        self.layout_button.clicked.connect(self.auto_layout)
        self.layout_button.setEnabled(False)
        control_layout.addWidget(self.layout_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_graph)
        self.clear_button.setEnabled(False)
        control_layout.addWidget(self.clear_button)
        
        control_layout.addStretch()
        
        self.status_label = QLabel("No file loaded")
        control_layout.addWidget(self.status_label)
        
        main_layout.addLayout(control_layout)
        
        # Graphics view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.RubberBandDrag)
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
            self.layout_button.setEnabled(True)
            self.clear_button.setEnabled(True)
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
        self.layout_button.setEnabled(False)
        self.clear_button.setEnabled(False)
    
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
            
            
            node = FunctionNode(func_name, signature, assembly, 0, 0)
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
        
        # Circular layout - account for rectangle size (250x180)
        center_x, center_y = 600, 500
        # Increase radius to accommodate larger rectangles
        radius = min(350, max(200, n * 30))
        
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
