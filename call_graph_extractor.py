"""
Call Graph Extractor using pycparser
Extracts function definitions and their calls from C source files.
"""

from pycparser import parse_file, c_ast
from collections import defaultdict
import sys


class CallGraphExtractor:
    """Extracts call graph information from C source files."""
    
    def __init__(self):
        self.functions = {}  # function_name -> FunctionDef node
        self.calls = defaultdict(set)  # caller -> set of callees
        self.defined_functions = set()  # All defined function names
        self.current_function = None  # Track current function context
        
    def extract(self, filename):
        """
        Extract call graph from a C file.
        
        Args:
            filename: Path to the C source file
            
        Returns:
            tuple: (functions dict, calls dict)
        """
        try:
            ast = parse_file(filename, use_cpp=True)
        except Exception as e:
            print(f"Error parsing file: {e}", file=sys.stderr)
            return self.functions, self.calls
        
        # Reset state
        self.functions = {}
        self.calls = defaultdict(set)
        self.defined_functions = set()
        self.current_function = None
        
        # Visit all nodes in the AST
        self.visit(ast)
        
        return self.functions, self.calls
    
    def visit(self, node):
        """Recursively visit AST nodes."""
        if isinstance(node, c_ast.FuncDef):
            # Save previous context
            prev_function = self.current_function
            func_name = node.decl.name
            self.current_function = func_name
            self.defined_functions.add(func_name)
            self.functions[func_name] = node
            
            # Visit function body
            if node.body:
                self.visit(node.body)
            
            # Restore previous context
            self.current_function = prev_function
        elif isinstance(node, c_ast.FuncCall):
            # Record function call if we're inside a function
            callee_name = self.get_function_name(node)
            if callee_name and self.current_function:
                self.calls[self.current_function].add(callee_name)
        
        # Recursively visit children
        for child_name, child in node.children():
            self.visit(child)
    
    def get_function_name(self, node):
        """Extract function name from a function call node."""
        if isinstance(node, c_ast.FuncCall):
            if isinstance(node.name, c_ast.ID):
                return node.name.name
            elif isinstance(node.name, c_ast.StructRef):
                # Handle method calls like obj->func()
                if isinstance(node.name.field, c_ast.ID):
                    return node.name.field.name
        return None


def extract_call_graph(filename):
    """
    Convenience function to extract call graph from a C file.
    
    Args:
        filename: Path to the C source file
        
    Returns:
        tuple: (functions dict, calls dict)
    """
    extractor = CallGraphExtractor()
    return extractor.extract(filename)
