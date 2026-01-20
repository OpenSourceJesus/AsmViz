/* Test metamorphic return sites: function that overwrites msg before printing */

#ifdef GCC
#include <stdio.h>
#endif

/* String constant that will be overwritten - make sure it's large enough */
char msg[14] = "Original\n";

/* Function that overwrites msg - should use metamorphic return site (single return) */
void overwrite_msg() {
    msg[0] = 'M';
    msg[1] = 'e';
    msg[2] = 't';
    msg[3] = 'a';
    msg[4] = 'm';
    msg[5] = 'o';
    msg[6] = 'r';
    msg[7] = 'p';
    msg[8] = 'h';
    msg[9] = 'i';
    msg[10] = 'c';
    msg[11] = '!';
    msg[12] = '\n';
    msg[13] = '\0';  /* Ensure null terminator */
}

/* Function to make write syscall - compiler will detect this pattern and generate syscall code */
#ifdef GCC
#define print printf
#else
void print(char *fmt, char *msg) {
    /* Empty body - compiler will generate syscall code */
}
#endif

int main() {
    volatile int iterations = 1000000;  /* 1 million iterations */
    
    /* Loop to test actual execution time, not just startup */
    for (int i = 0; i < iterations; i++) {
        overwrite_msg();  /* Call function that overwrites msg - tests metamorphic return sites */
    }
    
    print("%s", msg);
    return 0;
}
