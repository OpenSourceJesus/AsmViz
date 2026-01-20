"""
Assembly Extractor
Extracts assembly code for functions by running gcc -S and parsing the output.
Supports multiple C files and direct assembly file parsing.
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


def parse_assembly_file(asm_filename):
    """
    Parse an assembly file and extract all function definitions.
    
    Args:
        asm_filename: Path to the assembly file (.s or .S)
        
    Returns:
        dict: function_name -> assembly code string
    """
    if not os.path.exists(asm_filename):
        return {}
    
    try:
        with open(asm_filename, 'r') as f:
            assembly_content = f.read()
    except Exception as e:
        print(f"Warning: Failed to read assembly file {asm_filename}: {e}", file=sys.stderr)
        return {}
    
    function_assemblies = {}
    
    # Find all function labels in the assembly
    # Pattern: function_name: or .type function_name
    function_labels = []
    lines = assembly_content.split('\n')
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check for function label (non-local label ending with :)
        if re.match(r'^\s*\w+:', stripped):
            label_name = stripped.split(':')[0].strip()
            # Skip local labels (start with .L) and other special labels
            if not label_name.startswith('.L') and not label_name.startswith('.'):
                function_labels.append((i, label_name))
        
        # Also check for .type directive which can indicate a function
        type_match = re.match(r'^\s*\.type\s+(\w+),', stripped)
        if type_match:
            func_name = type_match.group(1)
            # Check if we already have this function, if not add it
            if not any(name == func_name for _, name in function_labels):
                # Try to find the label earlier in the file
                for j in range(max(0, i - 10), i):
                    if re.search(rf'^\s*{re.escape(func_name)}:', lines[j], re.MULTILINE):
                        function_labels.append((j, func_name))
                        break
    
    # Extract each function's assembly
    for func_idx, (start_line, func_name) in enumerate(function_labels):
        # Find the start of this function
        func_lines = []
        collecting = False
        
        # Determine end line (start of next function or end of file)
        end_line = len(lines)
        if func_idx + 1 < len(function_labels):
            end_line = function_labels[func_idx + 1][0]
        
        # Extract function body from start_line to end_line
        for i in range(start_line, end_line):
            line = lines[i]
            stripped = line.strip()
            
            # Start collecting when we find the function label
            if not collecting and f'{func_name}:' in line:
                collecting = True
            
            if collecting:
                # Stop conditions
                # 1. .size directive for this function (marks end)
                if f'.size {func_name}' in line or f'.size\t{func_name}' in line:
                    func_lines.append(line)
                    break
                
                func_lines.append(line)
        
        if func_lines:
            func_asm = '\n'.join(func_lines)
            # Clean up: remove excessive empty lines
            func_asm = re.sub(r'\n\n\n+', '\n\n', func_asm)
            function_assemblies[func_name] = func_asm.strip()
    
    return function_assemblies


def extract_assembly_for_functions(c_filenames, function_names, assembly_files=None):
    """
    Extract assembly code for specific functions from one or more C files.
    Optionally also include functions from assembly files.
    
    Args:
        c_filenames: Path to C source file(s) - can be a single string or list
        function_names: List of function names to extract
        assembly_files: Optional list of assembly file paths to also parse
        
    Returns:
        dict: function_name -> assembly code string
    """
    if not function_names:
        return {}
    
    # Convert single filename to list
    if isinstance(c_filenames, str):
        c_filenames = [c_filenames]
    
    function_assemblies = {}
    
    # First, parse any provided assembly files
    if assembly_files:
        for asm_file in assembly_files:
            asm_functions = parse_assembly_file(asm_file)
            # Only include functions we're looking for
            for func_name in function_names:
                if func_name in asm_functions and func_name not in function_assemblies:
                    function_assemblies[func_name] = asm_functions[func_name]
    
    # Find functions we still need from C files
    remaining_functions = [f for f in function_names if f not in function_assemblies]
    
    if not remaining_functions or not c_filenames:
        return function_assemblies
    
    # Create a temporary directory for assembly output
    temp_dir = tempfile.mkdtemp()
    asm_files = []  # Track all generated assembly files for cleanup
    asm_filename = None  # Combined assembly file
    
    try:
        # Compile each C file separately to assembly, then combine them
        # This is necessary because gcc -S -o doesn't work with multiple input files
        for c_file in c_filenames:
            # Generate a unique assembly filename for each C file
            base_name = os.path.basename(c_file)
            asm_file = os.path.join(temp_dir, base_name + '.s')
            asm_files.append(asm_file)
            
            # Compile this C file to assembly
            # Define GCC so that #ifdef GCC code will run
            result = subprocess.run(
                ['gcc', '-S', '-DGCC', '-o', asm_file, c_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                print(f"Warning: gcc failed for {c_file}: {result.stderr}", file=sys.stderr)
                # Continue with other files even if one fails
        
        # Combine all assembly files into one
        asm_filename = os.path.join(temp_dir, 'combined.s')
        assembly_content = ""
        for asm_file in asm_files:
            if os.path.exists(asm_file):
                with open(asm_file, 'r') as f:
                    file_content = f.read()
                    # Add a comment to mark where this file's assembly starts
                    assembly_content += f"\n# Assembly from {os.path.basename(asm_file)}\n"
                    assembly_content += file_content
                    assembly_content += "\n"
        
        if not assembly_content:
            # No assembly was generated
            for name in remaining_functions:
                if name not in function_assemblies:
                    function_assemblies[name] = "Assembly unavailable"
            return function_assemblies
        
        # Write combined assembly to a file for easier debugging if needed
        with open(asm_filename, 'w') as f:
            f.write(assembly_content)
        
        # Parse assembly to extract function bodies for remaining functions
        for func_name in remaining_functions:
            if func_name in function_assemblies:
                continue  # Already found in assembly files
                
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
        for name in remaining_functions:
            if name not in function_assemblies:
                function_assemblies[name] = "Assembly extraction timed out"
        return function_assemblies
    except Exception as e:
        print(f"Warning: Failed to extract assembly: {e}", file=sys.stderr)
        for name in remaining_functions:
            if name not in function_assemblies:
                function_assemblies[name] = f"Assembly unavailable: {str(e)}"
        return function_assemblies
    finally:
        # Clean up temporary files
        try:
            # Remove all temporary assembly files
            if asm_files:
                for asm_file in asm_files:
                    if os.path.exists(asm_file):
                        os.remove(asm_file)
            if asm_filename and os.path.exists(asm_filename):
                os.remove(asm_filename)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except:
            pass


def extract_assembly_for_functions_legacy(c_filename, function_names):
    """
    Legacy function for backward compatibility - extracts assembly from a single C file.
    
    Args:
        c_filename: Path to the C source file
        function_names: List of function names to extract
        
    Returns:
        dict: function_name -> assembly code string
    """
    return extract_assembly_for_functions(c_filename, function_names)


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


def get_function_info(c_filenames, functions_dict, assembly_files=None):
    """
    Get function signatures, assembly, and C code for all functions.
    Supports multiple C files and assembly files.
    
    Args:
        c_filenames: Path to C source file(s) - can be a single string or list
        functions_dict: Dictionary of function_name -> FuncDef node
        assembly_files: Optional list of assembly file paths to also parse
        
    Returns:
        dict: function_name -> {'signature': str, 'assembly': str, 'c_code': str}
    """
    function_info = {}
    
    # Extract signatures and C code
    for func_name, func_def in functions_dict.items():
        # Handle assembly-only functions (func_def is None)
        if func_def is None:
            signature = f"{func_name}()"
            c_code = f"{signature} {{\n    // C code unavailable (assembly-only function)\n}}"
        else:
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
    assemblies = extract_assembly_for_functions(c_filenames, function_names, assembly_files)
    
    # Combine signatures, assembly, and C code
    for func_name in function_names:
        if func_name in assemblies:
            function_info[func_name]['assembly'] = assemblies[func_name]
        else:
            function_info[func_name]['assembly'] = "Assembly unavailable"
    
    return function_info
