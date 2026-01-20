/* Test that prints 'Hello World!' using a syscall without any #include */

#ifdef GCC
#include <stdio.h>
#endif

/* String constant for "Hello World!\n" */
char msg[] = "Hello World!\n";

/* Function to make write syscall - compiler will detect this pattern and generate syscall code */
#ifdef GCC
#define print printf
#else
void print(char *fmt, char *msg) {
    /* Empty body - compiler will generate syscall code */
}
#endif

void a ()
{
    b ();
}

void b ()
{
    print("%s", msg);
}

int main() {
    volatile int iterations = 1000000;  /* 1 million iterations */
    
    /* Loop to test actual execution time, not just startup */
    for (int i = 0; i < iterations; i++) {
        a ();
    }
    
    return 0;
}
