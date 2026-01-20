"""
Assembly Extractor
Extracts assembly code for functions by running gcc -S and parsing the output.
"""

import subprocess
import os
import tempfile
import re
import sys


def extract_function_signature(func_def_node):
    """
    Extract function signature from a FuncDef AST node.
    
    Args:
        func_def_node: pycparser c_ast.FuncDef node
        
    Returns:
        str: Function signature string
    """
    from pycparser import c_generator
    
    generator = c_generator.CGenerator()
    
    # Generate the function declaration (signature)
    decl = func_def_node.decl
    signature = generator.visit(decl.type)
    
    # Add function name
    func_name = decl.name
    signature = signature.replace('(*)', f'({func_name})')
    
    return signature


def extract_assembly_for_functions(c_filename, function_names):
    """
    Extract assembly code for specific functions from a C file.
    
    Args:
        c_filename: Path to the C source file
        function_names: List of function names to extract
        
    Returns:
        dict: function_name -> assembly code string
    """
    if not function_names:
        return {}
    
    # Create a temporary directory for assembly output
    temp_dir = tempfile.mkdtemp()
    asm_filename = os.path.join(temp_dir, 'output.s')
    
    try:
        # Run gcc -S to generate assembly
        result = subprocess.run(
            ['gcc', '-S', '-o', asm_filename, c_filename],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"Warning: gcc failed: {result.stderr}", file=sys.stderr)
            print(f"gcc stdout: {result.stdout}", file=sys.stderr)
            return {name: f"Assembly unavailable (gcc error)" for name in function_names}
        
        # Read the assembly file
        if not os.path.exists(asm_filename):
            return {name: "Assembly unavailable" for name in function_names}
        
        with open(asm_filename, 'r') as f:
            assembly_content = f.read()
        
        # Parse assembly to extract function bodies
        function_assemblies = {}
        
        for func_name in function_names:
            # Find function label in assembly - try multiple patterns
            func_label_patterns = [
                rf'^\s*{re.escape(func_name)}:',  # Standard: func_name:
                rf'^\s*\.type\s+{re.escape(func_name)}',  # With .type directive
            ]
            
            label_match = None
            start_pos = -1
            for pattern in func_label_patterns:
                match = re.search(pattern, assembly_content, re.MULTILINE)
                if match:
                    label_match = match
                    start_pos = match.start()
                    break
            
            if start_pos == -1:
                function_assemblies[func_name] = f"; {func_name} not found in assembly"
                continue
            
            # Find where this function ends
            # Look for next function label (but not the same one) or .size directive
            remaining = assembly_content[start_pos:]
            lines = remaining.split('\n')
            
            # Find the function label line and collect all instructions
            func_lines = []
            found_label = False
            collecting = False
            
            for i, line in enumerate(lines):
                stripped = line.strip()
                
                if not found_label:
                    # Look for the function label
                    if f'{func_name}:' in line:
                        found_label = True
                        collecting = True
                        func_lines.append(line)
                        continue
                elif collecting:
                    # After finding label, collect lines until we hit a stopping condition
                    
                    # Stop conditions (only for non-local labels):
                    # 1. Next function label (but not a local label starting with .L)
                    if re.match(r'^\s*\w+:', line):
                        label_text = stripped.split(':')[0].strip()
                        # Skip local labels (start with .L)
                        if not label_text.startswith('.L'):
                            # Check if it's a different function
                            if label_text != func_name:
                                break
                    
                    # 2. .size directive for this function (marks end)
                    if f'.size {func_name}' in line or f'.size\t{func_name}' in line:
                        # Don't include .size line, just stop
                        break
                    
                    # 3. End of file markers
                    if stripped.startswith('.ident') or (stripped.startswith('.section') and '.text' not in line):
                        break
                    
                    # Skip function end markers like .LFE0:
                    if re.match(r'^\s*\.LFE\d+:', line):
                        continue
                    
                    # Add the line (including local labels like .LFB0:, but not .LFE0:)
                    func_lines.append(line)
                    
                    # Limit to reasonable number of lines
                    if len(func_lines) > 60:
                        func_lines.append('...')
                        break
            
            # Join and clean up
            if func_lines:
                func_asm = '\n'.join(func_lines)
                # Filter and format - keep ALL non-empty lines (don't filter out labels or directives)
                asm_lines = func_asm.split('\n')
                cleaned_lines = []
                for line in asm_lines:
                    stripped = line.strip()
                    # Keep ALL non-empty lines - don't filter anything out
                    if stripped:
                        # Truncate very long lines for display
                        if len(line) > 80:
                            line = line[:77] + '...'
                        cleaned_lines.append(line)
                    # Limit total lines for display (but keep more than before)
                    if len(cleaned_lines) >= 50:
                        break
                
                func_asm = '\n'.join(cleaned_lines)
                if len(asm_lines) > len(cleaned_lines):
                    func_asm += '\n...'
            else:
                func_asm = f"; {func_name}: (no body captured)"
            
            function_assemblies[func_name] = func_asm
        
        return function_assemblies
        
    except subprocess.TimeoutExpired:
        print("Warning: gcc timed out", file=sys.stderr)
        return {name: "Assembly extraction timed out" for name in function_names}
    except Exception as e:
        print(f"Warning: Failed to extract assembly: {e}", file=sys.stderr)
        return {name: f"Assembly unavailable: {str(e)}" for name in function_names}
    finally:
        # Clean up temporary files
        try:
            if os.path.exists(asm_filename):
                os.remove(asm_filename)
            os.rmdir(temp_dir)
        except:
            pass


def extract_function_c_code(func_def_node):
    """
    Extract C source code from a FuncDef AST node.
    
    Args:
        func_def_node: pycparser c_ast.FuncDef node
        
    Returns:
        str: C source code string
    """
    from pycparser import c_generator
    
    generator = c_generator.CGenerator()
    
    # Generate the full function definition (signature + body)
    c_code = generator.visit(func_def_node)
    
    return c_code


def get_function_info(c_filename, functions_dict):
    """
    Get function signatures, assembly, and C code for all functions.
    
    Args:
        c_filename: Path to the C source file
        functions_dict: Dictionary of function_name -> FuncDef node
        
    Returns:
        dict: function_name -> {'signature': str, 'assembly': str, 'c_code': str}
    """
    function_info = {}
    
    # Extract signatures and C code
    for func_name, func_def in functions_dict.items():
        try:
            signature = extract_function_signature(func_def)
        except:
            signature = f"{func_name}()"
        
        try:
            c_code = extract_function_c_code(func_def)
        except:
            c_code = f"{signature} {{\n    // C code unavailable\n}}"
        
        function_info[func_name] = {'signature': signature, 'assembly': None, 'c_code': c_code}
    
    # Extract assembly for all functions at once
    function_names = list(functions_dict.keys())
    assemblies = extract_assembly_for_functions(c_filename, function_names)
    
    # Combine signatures, assembly, and C code
    for func_name in function_names:
        if func_name in assemblies:
            function_info[func_name]['assembly'] = assemblies[func_name]
        else:
            function_info[func_name]['assembly'] = "Assembly unavailable"
    
    return function_info
