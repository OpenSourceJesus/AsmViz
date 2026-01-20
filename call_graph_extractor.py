"""
Call Graph Extractor using pycparser
Extracts function definitions and their calls from C source files.
Supports both single files and multiple files.
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
        self.function_sources = {}  # function_name -> source file path
        
    def extract(self, filenames):
        """
        Extract call graph from one or more C files.
        
        Args:
            filenames: Path to a C source file, or list of paths to C source files
            
        Returns:
            tuple: (functions dict, calls dict)
        """
        # Convert single filename to list for uniform handling
        if isinstance(filenames, str):
            filenames = [filenames]
        
        # Reset state
        self.functions = {}
        self.calls = defaultdict(set)
        self.defined_functions = set()
        self.current_function = None
        self.function_sources = {}
        
        # Process each file
        for filename in filenames:
            try:
                ast = parse_file(filename, use_cpp=True)
            except Exception as e:
                print(f"Warning: Error parsing file {filename}: {e}", file=sys.stderr)
                continue
            
            # Visit all nodes in the AST, passing source file for tracking
            self.visit(ast, source_file=filename)
        
        return self.functions, self.calls
    
    def visit(self, node, source_file=None):
        """Recursively visit AST nodes."""
        if isinstance(node, c_ast.FuncDef):
            # Save previous context
            prev_function = self.current_function
            func_name = node.decl.name
            self.current_function = func_name
            self.defined_functions.add(func_name)
            
            # Check for duplicate definitions
            if func_name in self.functions:
                print(f"Warning: Function '{func_name}' defined in multiple files: "
                      f"{self.function_sources.get(func_name, 'unknown')} and {source_file}", 
                      file=sys.stderr)
            else:
                self.functions[func_name] = node
                if source_file:
                    self.function_sources[func_name] = source_file
            
            # Visit function body
            if node.body:
                self.visit(node.body, source_file)
            
            # Restore previous context
            self.current_function = prev_function
        elif isinstance(node, c_ast.FuncCall):
            # Record function call if we're inside a function
            callee_name = self.get_function_name(node)
            if callee_name and self.current_function:
                self.calls[self.current_function].add(callee_name)
        
        # Recursively visit children
        for child_name, child in node.children():
            self.visit(child, source_file)
    
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


def extract_call_graph(filenames):
    """
    Convenience function to extract call graph from one or more C files.
    
    Args:
        filenames: Path to a C source file, or list of paths to C source files
        
    Returns:
        tuple: (functions dict, calls dict)
    """
    extractor = CallGraphExtractor()
    return extractor.extract(filenames)
