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
import re
try:
    from pycparser import __file__ as pycparser_file
    # Try to find fake_libc_include directory
    pycparser_dir = os.path.dirname(pycparser_file)
    # First try the local fake_libc_include directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fake_libc_include = os.path.join(script_dir, 'fake_libc_include')
    if not os.path.isdir(fake_libc_include):
        # Fall back to pycparser's fake_libc_include
        fake_libc_include = os.path.join(pycparser_dir, 'utils', 'fake_libc_include')
    FAKE_LIBC_AVAILABLE = os.path.isdir(fake_libc_include)
    if FAKE_LIBC_AVAILABLE:
        fake_libc_include = os.path.abspath(fake_libc_include)
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


def preprocess_inline_assembly(content):
    """
    Preprocess inline assembly statements to make them parseable by pycparser.
    Handles all forms including asm volatile("code" ::: "clobbers").
    
    Args:
        content: C source code as string
        
    Returns:
        str: Preprocessed C source code with inline assembly replaced
    """
    # Pattern to match inline assembly statements
    # This handles:
    # - asm("code");
    # - asm volatile("code");
    # - asm("code" : outputs : inputs : clobbers);
    # - asm volatile("code" : outputs : inputs : clobbers);
    # - asm("code" ::: "clobbers");  (no outputs, no inputs, just clobbers - note the :::)
    # - asm volatile("code" ::: "clobbers");
    
    # Use a state machine to find and replace asm statements
    # We need to handle:
    # 1. asm/__asm__/__asm keyword
    # 2. Optional volatile
    # 3. Opening parenthesis
    # 4. Assembly string (may contain escaped quotes and nested parens)
    # 5. Closing parenthesis
    # 6. Optional : outputs
    # 7. Optional : inputs
    # 8. Optional : clobbers or ::: clobbers
    # 9. Semicolon
    
    result = []
    i = 0
    content_len = len(content)
    
    while i < content_len:
        # Look for asm keyword
        if (i == 0 or not (content[i-1].isalnum() or content[i-1] == '_')):
            # Check for __asm__ first (longest match) - note: __asm__ is 7 characters
            if content[i:i+7] == '__asm__':
                asm_start = i
                i += 7
                # Skip whitespace
                while i < content_len and content[i].isspace():
                    i += 1
                # Check for volatile
                if i < content_len and content[i:i+8] == 'volatile':
                    i += 8
                    while i < content_len and content[i].isspace():
                        i += 1
            # Check for __asm (must check before 'asm' to avoid partial match)
            elif content[i:i+5] == '__asm' and (i+5 >= content_len or not (content[i+5].isalnum() or content[i+5] == '_')):
                asm_start = i
                i += 5
                # Skip whitespace
                while i < content_len and content[i].isspace():
                    i += 1
                # Check for volatile
                if i < content_len and content[i:i+8] == 'volatile':
                    i += 8
                    while i < content_len and content[i].isspace():
                        i += 1
            # Check for 'asm' (must be word boundary)
            elif content[i:i+3] == 'asm' and (i+3 >= content_len or not (content[i+3].isalnum() or content[i+3] == '_')):
                asm_start = i
                i += 3
                # Skip whitespace
                while i < content_len and content[i].isspace():
                    i += 1
                # Check for volatile
                if i < content_len and content[i:i+8] == 'volatile':
                    i += 8
                    while i < content_len and content[i].isspace():
                        i += 1
            else:
                result.append(content[i])
                i += 1
                continue
            
            # Now we should have an opening parenthesis
            # If we don't have '(', this wasn't actually an asm statement, so fall through
            if i < content_len and content[i] == '(':
                # Find matching closing parenthesis, handling nested parens and strings
                paren_depth = 1
                i += 1
                in_string = False
                escape_next = False
                
                while i < content_len and paren_depth > 0:
                    if escape_next:
                        escape_next = False
                        i += 1
                        continue
                    
                    char = content[i]
                    
                    if char == '\\':
                        escape_next = True
                        i += 1
                        continue
                    
                    if char == '"':
                        in_string = not in_string
                        i += 1
                        continue
                    
                    if not in_string:
                        if char == '(':
                            paren_depth += 1
                        elif char == ')':
                            paren_depth -= 1
                    
                    i += 1
                
                # Now look for optional : sections or semicolon
                while i < content_len:
                    # Skip whitespace
                    while i < content_len and content[i].isspace():
                        i += 1
                    
                    if i >= content_len:
                        break
                    
                    # Check for ::: (clobbers only, no outputs/inputs)
                    if content[i:i+3] == ':::':
                        i += 3
                        # Skip until semicolon
                        while i < content_len and content[i] != ';':
                            i += 1
                        break
                    # Check for : (operands)
                    elif content[i] == ':':
                        i += 1
                        # Skip until next : or ; or end
                        while i < content_len and content[i] != ':' and content[i] != ';':
                            i += 1
                        # If we hit another :, continue to handle it
                        if i < content_len and content[i] == ':':
                            continue
                        # If we hit ;, break
                        if i < content_len and content[i] == ';':
                            break
                    # Check for semicolon
                    elif content[i] == ';':
                        i += 1
                        break
                    else:
                        # Unexpected character, break
                        break
                
                # Replace the entire asm statement with a comment
                result.append('; /* inline assembly removed */')
                continue
            else:
                # No opening parenthesis found, this wasn't an asm statement
                # Backtrack and append characters normally
                # We need to go back to where we started matching
                result.append(content[asm_start])
                i = asm_start + 1
                continue
        
        result.append(content[i])
        i += 1
    
    return ''.join(result)


def preprocess_file_for_parsing(filename):
    """
    Preprocess a C file to handle inline assembly before parsing.
    Creates a temporary file with preprocessed content.
    
    Args:
        filename: Path to the C source file
        
    Returns:
        str: Path to temporary preprocessed file, or original filename if preprocessing fails
    """
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Preprocess inline assembly
        preprocessed = preprocess_inline_assembly(content)
        
        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.c', prefix='pycparser_asm_', text=True)
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                f.write(preprocessed)
            return temp_path
        except Exception:
            os.close(temp_fd)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return filename
    except Exception:
        # If preprocessing fails, return original filename
        return filename


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
            '-Dvolatile=',  # Strip volatile to allow inline asm parsing
            '-D__restrict=',  # Remove __restrict__
            '-D__extension__=',  # Remove __extension__
            '-Dasm=',  # Strip inline asm keyword (GCC extension)
            '-D__asm=',  # Strip inline asm keyword (alternate spelling)
            '-D__asm__=',  # Strip inline asm keyword (alternate spelling)
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
                # Preprocess file to handle inline assembly
                preprocessed_file = preprocess_file_for_parsing(filename)
                try:
                    ast = parse_file(preprocessed_file, use_cpp=True, cpp_args=cpp_args)
                finally:
                    # Clean up temporary file if it was created
                    if preprocessed_file != filename and os.path.exists(preprocessed_file):
                        try:
                            os.remove(preprocessed_file)
                        except:
                            pass
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
