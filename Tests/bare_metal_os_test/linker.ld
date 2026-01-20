/* Linker script for bare metal OS
 * Defines memory layout and sections for a bare metal kernel
 */

ENTRY(_start)

/* Memory layout for bare metal x86-64 */
MEMORY
{
    /* Code and data at 1MB (typical bootloader load address) */
    ROM (rx) : ORIGIN = 0x100000, LENGTH = 512K
    RAM (rwx) : ORIGIN = 0x200000, LENGTH = 1M
}

SECTIONS
{
    /* Code section */
    .text : {
        *(.text)
        *(.text.*)
        . = ALIGN(16);
    } > ROM

    /* Read-only data */
    .rodata : {
        *(.rodata)
        *(.rodata.*)
        . = ALIGN(16);
    } > ROM

    /* Initialized data */
    .data : {
        *(.data)
        *(.data.*)
        . = ALIGN(16);
    } > RAM AT > ROM

    /* Uninitialized data (BSS) */
    .bss : {
        *(.bss)
        *(.bss.*)
        *(COMMON)
        . = ALIGN(16);
    } > RAM

    /* Stack */
    .stack : {
        . = ALIGN(16);
        stack_bottom = .;
        . += 8192;  /* 8KB stack */
        stack_top = .;
    } > RAM

    /* Symbols for debugging */
    _kernel_start = ADDR(.text);
    _kernel_end = ADDR(.bss) + SIZEOF(.bss);
    _data_start = ADDR(.data);
    _data_end = ADDR(.bss);
    _bss_start = ADDR(.bss);
    _bss_end = ADDR(.bss) + SIZEOF(.bss);
}
