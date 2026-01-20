# Comprehensive Multi-File Test Suite

This test suite exercises all features of the C compiler across multiple files.

## Files

- **main.c**: Main entry point with function calls, local variables, and control flow
- **math_ops.c**: Small functions (<1024 bytes) for indexed-jump optimization
- **control_flow.c**: Control flow structures (if/else, while, for loops) with arrays
- **globals.c**: Global variables including SIMD-packed variables (1-8 bits)
- **interrupts.c**: Interrupt callback functions with zero-latency SIMD access
- **utils.c**: Utility functions testing various C features
- **arrays.c**: Array operations and pointer handling
- **bitwise.c**: Bit-shifting and bitwise operations
- **structs.c**: Struct declarations and member access
- **operators.c**: Advanced operators (compound assignment, increment/decrement, ternary)

## Features Tested

### 1. Functions
- Small functions (<1024 bytes) for indexed-jump optimization
- Large functions with multiple return sites
- Functions with single return (metamorphic return site optimization)
- Function calls (direct and nested)
- External function declarations

### 2. Global Variables
- Regular global variables with initialization
- SIMD-packed global variables (1-8 bits) using `auto _Alignas(N) char`
- Mixed access to regular and SIMD-packed globals

### 3. Local Variables
- Variable declarations with initialization
- Variable assignments
- Indexed stack pointer system (16-byte intervals)

### 4. Control Flow
- if/else statements
- while loops
- for loops
- Nested control flow
- Multiple return statements
- Single return statements

### 5. Binary Operations
- Arithmetic: Addition (+), Subtraction (-), Multiplication (*), Division (/), Modulo (%)
- Comparison: Equality (==), Not equal (!=), Less than (<), Greater than (>), Less or equal (<=), Greater or equal (>=)
- Logical: Logical AND (&&), Logical OR (||)

### 6. Unary Operations
- Negation (-)
- Logical NOT (!)

### 7. Constants
- Numeric constants (decimal, hex, octal)
- Character constants

### 8. Complex Expressions
- Parenthesized expressions
- Nested function calls
- Mixed operations

### 10. Array Operations
- Array indexing: `arr[index]`
- Array assignment: `arr[index] = value`
- Global array declarations
- Array operations in loops
- Array functions (sum, max, min, reverse, etc.)

### 11. Bit-Shifting Operations
- Left shift: `<<`
- Right shift: `>>`
- Power of 2 calculations
- Bit extraction and manipulation

### 12. Bitwise Operations
- Bitwise AND: `&`
- Bitwise OR: `|`
- Bitwise XOR: `^`
- Bitwise NOT: `~`
- Combined bitwise operations

### 13. Struct Support
- Struct declarations
- Member access: `struct.member` and `struct->member`
- Struct initialization
- Struct operations (points, rectangles, etc.)

### 14. Compound Assignment Operators
- `+=`, `-=`, `*=`, `/=`, `%=`
- `<<=`, `>>=`, `&=`, `|=`, `^=`

### 15. Increment/Decrement Operators
- Pre-increment: `++var`
- Post-increment: `var++`
- Pre-decrement: `--var`
- Post-decrement: `var--`

### 16. Ternary Operator
- Conditional expression: `condition ? true_expr : false_expr`
- Nested ternary operators
- Ternary with function calls

### 17. Address-of Operator
- Address-of: `&var`
- Pointer operations

### 9. Interrupt Callbacks
- Functions with `isr_*` naming pattern
- Functions with `irq_*` naming pattern
- Functions with `*_handler` naming pattern
- Functions with `*_callback` naming pattern
- Zero-latency SIMD register access

## Compilation

To compile this test suite:

```bash
python3 compiler.py comprehensive_test/ -o comprehensive_test.asm -v
```

This will:
1. Find all `.c` files in the `comprehensive_test/` directory
2. Parse them using `MultiFileParser`
3. Analyze functions and global variables
4. Generate optimized assembly code
5. Assemble and link the executable

## Expected Optimizations

1. **Indexed-Jump**: Small functions in `math_ops.c` should use indexed-jump table
2. **SIMD Bit-Packing**: Variables in `globals.c` with `auto _Alignas(N) char` should be packed into xmm15
3. **Zero-Latency Access**: Interrupt callbacks in `interrupts.c` should use direct SIMD register access
4. **Indexed Stack**: Local variables should use indexed stack pointer system (R12 + slot_index*16)
5. **Metamorphic Return Sites**: Functions with single return should use optimized return sites
6. **Quantized Call-Backs**: Return sites should be 16-byte aligned

## Verification

After compilation, check the generated `.asm` file for:

- `JUMP_TABLE` section for small functions
- `_init_simd_packing` function for SIMD initialization
- `STACK_BASE` data section
- Indexed addressing patterns: `[R12 + offset]`
- SIMD register access: `MOVQ RAX, xmm15`
- Interrupt callback optimizations in `isr_*` and `irq_*` functions
