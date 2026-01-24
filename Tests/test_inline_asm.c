/* Inline assembly parsing test */

void inline_nop()
{
    asm volatile("nop");
}

void inline_empty()
{
    asm volatile("");
}

void inline_with_clobbers()
{
    /* Test ::: syntax (no outputs, no inputs, just clobbers) */
    asm volatile("nop" ::: "memory");
}

void inline_with_operands()
{
    /* Test full syntax with outputs, inputs, and clobbers */
    int result;
    int input = 5;
    asm volatile("movl %1, %0" : "=r"(result) : "r"(input) : "memory");
}

int main()
{
    volatile int iterations = 1000000;  /* 1 million iterations */

    for (int i = 0; i < iterations; i++) {
        inline_nop();
        inline_empty();
        inline_with_clobbers();
        inline_with_operands();
    }

    return 0;
}
