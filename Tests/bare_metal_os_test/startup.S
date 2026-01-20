# Bare Metal OS Startup Code
# Assembly entry point and low-level initialization

.section .text

# Global symbols for C code
.global _start
.global interrupt_handler_asm
.global kernel_entry

# Entry point - called by bootloader or directly
_start:
    # Set up stack pointer
    # For bare metal, we need to set up our own stack
    # Use appropriate register size based on mode (32-bit: esp, 64-bit: rsp)
    # movl works in both modes (lower 32 bits of rsp in 64-bit mode)
    movl $stack_top, %esp
    
    # Clear direction flag (required for string operations)
    cld
    
    # Initialize segment registers (if needed)
    # For 32-bit mode, we set segment registers
    # In 64-bit mode, segment registers are mostly ignored, but setting them is harmless
    movw $0, %ax
    movw %ax, %ds
    movw %ax, %es
    movw %ax, %fs
    movw %ax, %gs
    movw %ax, %ss
    
    # Call kernel entry point (C main function)
    # Support both naming conventions: GCC uses 'main', custom compiler uses 'FUNC_main'
#ifdef GCC
    call main
#else
    call FUNC_main
#endif
    
    # If main returns, halt the system
    hlt
    
    # Infinite loop as fallback
halt_loop:
    jmp halt_loop

# Assembly wrapper for interrupt handler
interrupt_handler_asm:
    # Save all registers
    # Use instruction suffixes to work in both 32-bit and 64-bit modes
    # pushl/popl for 32-bit, pushq/popq for 64-bit
    # We'll use a macro-like approach with conditionals
#ifdef __x86_64__
    # 64-bit mode: use 64-bit registers
    pushq %rax
    pushq %rbx
    pushq %rcx
    pushq %rdx
    pushq %rsi
    pushq %rdi
    pushq %rbp
#else
    # 32-bit mode: use 32-bit registers  
    pushl %eax
    pushl %ebx
    pushl %ecx
    pushl %edx
    pushl %esi
    pushl %edi
    pushl %ebp
#endif
    
    # Call C interrupt handler
    # Support both naming conventions: GCC uses 'interrupt_handler', custom compiler uses 'FUNC_interrupt_handler'
#ifdef GCC
    call interrupt_handler
#else
    call FUNC_interrupt_handler
#endif
    
    # Restore all registers
#ifdef __x86_64__
    # 64-bit mode
    popq %rbp
    popq %rdi
    popq %rsi
    popq %rdx
    popq %rcx
    popq %rbx
    popq %rax
#else
    # 32-bit mode
    popl %ebp
    popl %edi
    popl %esi
    popl %edx
    popl %ecx
    popl %ebx
    popl %eax
#endif
    
    # Return from interrupt
#ifdef __x86_64__
    iretq
#else
    iretl
#endif

# Kernel entry point (alternative entry)
kernel_entry:
    # Same as _start but can be called from other contexts
    movl $stack_top, %esp
    cld
    # Support both naming conventions
#ifdef GCC
    call main
#else
    call FUNC_main
#endif
    hlt
    jmp kernel_entry

.section .bss
# Stack space (8KB stack)
stack_bottom:
    .space 8192
stack_top:

.section .data
# Kernel data section
kernel_magic:
    .quad 0x4B45524E454C00  # "KERNEL\0" in ASCII
