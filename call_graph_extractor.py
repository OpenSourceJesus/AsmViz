"""
Call Graph Extractor using pycparser
Extracts function definitions and their calls from C source files.
Supports both single files and multiple files.
"""

from pycparser import parse_file, c_ast
from collections import defaultdict
import sys
import os
import tempfile
try:
    from pycparser import __file__ as pycparser_file
    # Try to find fake_libc_include directory
    pycparser_dir = os.path.dirname(pycparser_file)
    fake_libc_include = os.path.join(pycparser_dir, 'utils', 'fake_libc_include')
    FAKE_LIBC_AVAILABLE = os.path.isdir(fake_libc_include)
except:
    FAKE_LIBC_AVAILABLE = False
    fake_libc_include = None

# Create temporary header files for attribute fixes and minimal stddef
_ATTRIBUTE_FIX_HEADER_PATH = None
_FAKE_STDDEF_HEADER_PATH = None

def _create_attribute_fix_header():
    """Create a temporary header file that redefines __attribute__."""
    global _ATTRIBUTE_FIX_HEADER_PATH
    if _ATTRIBUTE_FIX_HEADER_PATH and os.path.exists(_ATTRIBUTE_FIX_HEADER_PATH):
        return _ATTRIBUTE_FIX_HEADER_PATH
    
    # Create temporary header file
    header_fd, header_path = tempfile.mkstemp(suffix='.h', prefix='pycparser_attr_fix_', text=True)
    try:
        with os.fdopen(header_fd, 'w') as f:
            f.write('''#ifndef PARSER_ATTRIBUTE_FIX_H
#define PARSER_ATTRIBUTE_FIX_H
/* Redefine __attribute__ to strip it completely for pycparser */
/* Force undefine first, then redefine */
#ifdef __attribute__
#undef __attribute__
#endif
/* Define __attribute__ as a macro that strips everything */
/* This handles patterns like __attribute__((packed)) */
#define __attribute__(x)
/* Handle __alignof__ which is used in system headers with __attribute__ */
#ifndef __alignof__
#define __alignof__(x) (sizeof(x))
#endif
/* Also handle common attribute-related macros that might be used */
#define __packed__
#define __aligned__(x)
#define __unused__
#define __maybe_unused__
#define __unused
#define __maybe_unused
#endif
''')
        _ATTRIBUTE_FIX_HEADER_PATH = header_path
        return header_path
    except Exception:
        os.close(header_fd)
        if os.path.exists(header_path):
            os.remove(header_path)
        return None

def _create_fake_stddef_header():
    """Create a minimal fake stddef.h to avoid system header issues."""
    global _FAKE_STDDEF_HEADER_PATH
    if _FAKE_STDDEF_HEADER_PATH and os.path.exists(_FAKE_STDDEF_HEADER_PATH):
        return _FAKE_STDDEF_HEADER_PATH
    
    # Create a minimal stddef.h
    header_fd, header_path = tempfile.mkstemp(suffix='.h', prefix='pycparser_stddef_', text=True)
    try:
        with os.fdopen(header_fd, 'w') as f:
            f.write('''#ifndef PARSER_STDDEF_H
#define PARSER_STDDEF_H
/* Minimal fake stddef.h for pycparser */
/* Basic types that are commonly used */
typedef unsigned long size_t;
typedef long ssize_t;
typedef long ptrdiff_t;
typedef int wchar_t;
#ifndef NULL
#define NULL ((void*)0)
#endif
#endif
''')
        _FAKE_STDDEF_HEADER_PATH = header_path
        return header_path
    except Exception:
        os.close(header_fd)
        if os.path.exists(header_path):
            os.remove(header_path)
        return None


class CallGraphExtractor:
    """Extracts call graph information from C source files."""
    
    def __init__(self):
        self.functions = {}  # function_name -> FunctionDef node
        self.calls = defaultdict(set)  # caller -> set of callees (for backward compatibility)
        self.calls_with_args = defaultdict(list)  # caller -> list of (callee, args_string) tuples
        self.defined_functions = set()  # All defined function names
        self.current_function = None  # Track current function context
        self.function_sources = {}  # function_name -> source file path
        
    def extract(self, filenames, include_dirs=None):
        """
        Extract call graph from one or more C files.
        
        Args:
            filenames: Path to a C source file, or list of paths to C source files
            include_dirs: Optional list of include directories to add with -I flags
            
        Returns:
            tuple: (functions dict, calls dict)
        """
        if include_dirs is None:
            include_dirs = []
        
        # Convert single filename to list for uniform handling
        if isinstance(filenames, str):
            filenames = [filenames]
        
        # Reset state
        self.functions = {}
        self.calls = defaultdict(set)
        self.calls_with_args = defaultdict(list)
        self.defined_functions = set()
        self.current_function = None
        self.function_sources = {}
        
        # Process each file
        # Use cpp_args to handle GCC-specific attributes that pycparser can't parse
        # This helps avoid parsing errors with system headers that contain __attribute__
        # Build cpp_args list - ORDER MATTERS!
        cpp_args = []
        
        # CRITICAL: Define __attribute__ stripping FIRST, before any includes
        # This must come before -include, -I, or any other flags that might trigger header processing
        # Try to undefine built-in first, then define our version
        cpp_args.extend([
            '-U__attribute__',  # Try to undefine GCC's built-in (may not work, but harmless)
            # Define __attribute__ to strip everything
            # The pattern __attribute__((packed)) matches __attribute__(x) where x is ((packed))
            '-D__attribute__(x)=',
            # Handle __alignof__ which is used in system headers with __attribute__
            '-D__alignof__(x)=sizeof(x)',
            # Also handle common attribute-related macros that might be used directly
            '-D__packed__=',
            '-D__aligned__(x)=',
            '-D__unused__=',
            '-D__maybe_unused__=',
            '-D__unused=',
            '-D__maybe_unused=',
        ])
        
        # Create and include a header file that redefines __attribute__ 
        # This provides a backup redefinition that happens during preprocessing
        # The -include flag processes this before the source file but after command-line -D flags
        attr_fix_header = _create_attribute_fix_header()
        if attr_fix_header:
            cpp_args.extend(['-include', attr_fix_header])
        
        # Use fake libc headers if available (recommended approach)
        if FAKE_LIBC_AVAILABLE:
            cpp_args.extend([
                '-I' + fake_libc_include,
                '-nostdinc',  # Don't use system headers - this is critical!
            ])
            # Add user-provided include directories
            for include_dir in include_dirs:
                cpp_args.extend(['-I', include_dir])
        else:
            # Create minimal fake stddef.h and use it to avoid system header conflicts
            fake_stddef = _create_fake_stddef_header()
            if fake_stddef:
                fake_stddef_dir = os.path.dirname(fake_stddef)
                cpp_args.extend([
                    '-I' + fake_stddef_dir,
                    '-nostdinc',  # Don't use system headers
                    # Create a wrapper that redirects stddef.h to our fake version
                ])
                # Add user-provided include directories
                for include_dir in include_dirs:
                    cpp_args.extend(['-I', include_dir])
                # Create a symlink or wrapper for stddef.h
                # Actually, we can't easily redirect system headers without more complex setup
                # So we'll rely on the -include approach and hope the source files
                # don't directly include system headers
            else:
                # No fake headers - add user-provided include directories anyway
                for include_dir in include_dirs:
                    cpp_args.extend(['-I', include_dir])
            # Note: Without fake headers, we can't use -nostdinc because
            # the source files might need some system definitions
            # So we'll try to make our __attribute__ definition work with system headers
        
        # Additional defines for GCC-specific keywords
        cpp_args.extend([
            '-D__volatile__=volatile',  # Handle __volatile__ keyword
            '-D__restrict=',  # Remove __restrict__
            '-D__extension__=',  # Remove __extension__
            '-D__asm__(x)=',  # Remove inline assembly attributes
            '-D__asm(x)=',  # Remove inline assembly attributes
            '-D__inline=',  # Handle inline
            '-D__inline__=',  # Handle __inline__
            '-D__const=const',  # Handle __const
            '-D__signed__=signed',  # Handle __signed__
            # Don't define __GNUC__ - it's already defined by GCC and causes redefinition warnings
        ])
        
        for filename in filenames:
            try:
                ast = parse_file(filename, use_cpp=True, cpp_args=cpp_args)
            except Exception as e:
                print(f"Warning: Error parsing file {filename}: {e}", file=sys.stderr)
                continue
            
            # Visit all nodes in the AST, passing source file for tracking
            self.visit(ast, source_file=filename)
        
        return self.functions, self.calls, self.calls_with_args, self.function_sources
    
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
                # Extract arguments as string
                args_string = self.get_function_args_string(node)
                self.calls_with_args[self.current_function].append((callee_name, args_string))
        
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
    
    def get_function_args_string(self, node):
        """Extract function call arguments as a formatted string."""
        if not isinstance(node, c_ast.FuncCall):
            return ""
        
        if not node.args:
            return ""
        
        from pycparser import c_generator
        generator = c_generator.CGenerator()
        
        # Generate string representation of each argument
        args_list = []
        for arg in node.args.exprs:
            try:
                arg_str = generator.visit(arg)
                # Truncate very long arguments for display
                if len(arg_str) > 50:
                    arg_str = arg_str[:47] + "..."
                args_list.append(arg_str)
            except:
                args_list.append("?")
        
        return ", ".join(args_list)


def extract_call_graph(filenames, include_dirs=None):
    """
    Convenience function to extract call graph from one or more C files.
    
    Args:
        filenames: Path to a C source file, or list of paths to C source files
        include_dirs: Optional list of include directories to add with -I flags
        
    Returns:
        tuple: (functions dict, calls dict, calls_with_args dict, function_sources dict)
        - functions: function_name -> FunctionDef node
        - calls: caller -> set of callees (for backward compatibility)
        - calls_with_args: caller -> list of (callee, args_string) tuples
        - function_sources: function_name -> source file path
    """
    extractor = CallGraphExtractor()
    return extractor.extract(filenames, include_dirs=include_dirs)
