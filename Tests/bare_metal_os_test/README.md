# Bare Metal OS Test

This directory contains a test for the compiler that demonstrates compilation of a bare metal operating system with:

- **C files**: Kernel code (`kernel.c`)
- **Assembly files**: Startup code and interrupt handlers (`startup.S`)
- **Linker script**: Memory layout definition (`linker.ld`)

## Structure

- `kernel.c`: Main kernel code with task management, initialization, and interrupt handling
- `startup.S`: Assembly startup code that sets up the stack and calls the C main function
- `linker.ld`: Linker script defining memory layout for bare metal execution
- `test.sh`: Test script to build and verify the OS

## Features Tested

1. **Multi-file C compilation**: The compiler processes multiple C files
2. **Assembly integration**: Assembly files are parsed and symbols are extracted
3. **Linker script support**: The compiler automatically finds and uses `linker.ld`
4. **Bare metal entry point**: `_start` symbol for direct execution
5. **Stack initialization**: Assembly code sets up the stack before calling C code
6. **Interrupt handling**: Assembly interrupt wrapper calls C interrupt handler

## Building

Run the test script:

```bash
cd bare_metal_os
./test.sh
```

Or compile manually:

```bash
python3 ../compiler.py . -o kernel.asm --verbose
```

## Running

To run the compiled kernel in QEMU:

```bash
# System mode (full emulation)
python3 ../compiler.py . --qemu-system

# User mode (simpler, but limited)
python3 ../compiler.py . --qemu
```

## Expected Output

The compilation should:
1. Find and parse `kernel.c`
2. Find and parse `startup.S` (extracting symbols like `_start`, `interrupt_handler_asm`)
3. Find and use `linker.ld` for linking
4. Generate `kernel.asm` with combined code
5. Assemble to `kernel.o`
6. Link to `kernel` executable using the linker script

## Memory Layout

The linker script defines:
- **ROM** (0x100000): Code and read-only data (512KB)
- **RAM** (0x200000): Data, BSS, and stack (1MB)
- **Stack**: 8KB stack space

## Notes

- The kernel is designed for x86-64 architecture
- Entry point is `_start` (standard for bare metal)
- Stack is manually initialized in assembly before calling C code
- Interrupt handlers use assembly wrappers to save/restore registers
