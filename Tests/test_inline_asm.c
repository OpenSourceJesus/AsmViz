/* Inline assembly parsing test */

void inline_nop()
{
    asm volatile("nop");
}

void inline_empty()
{
    asm volatile("");
}

int main()
{
    volatile int iterations = 1000000;  /* 1 million iterations */

    for (int i = 0; i < iterations; i++) {
        inline_nop();
        inline_empty();
    }

    return 0;
}
