/* Test C file for the custom compiler */

int add(int a, int b) {
    return a + b;
}

int multiply(int x, int y) {
    return x * y;
}

int main() {
    volatile int iterations = 1000000;  /* 1 million iterations */
    volatile int result = 0;
    
    /* Loop to test actual execution time, not just startup */
    for (int i = 0; i < iterations; i++) {
        int result1 = add(3, 4);
        int result2 = multiply(5, 6);
        result += result1 + result2;
    }
    
    return result % 256;  /* Modulo to keep return value in valid range */
}