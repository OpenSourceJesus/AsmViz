/* Benchmark program with deep function call stack */
/* This program has a loop that calls functions in a deep chain */

// Deep call chain: func1 -> func2 -> func3 -> func4 -> func5 -> func6 -> func7 -> func8
// Each function does some computation and calls the next

int func8(int x) {
    return x + 1;
}

int func7(int x) {
    return func8(x * 2) + 3;
}

int func6(int x) {
    return func7(x - 1) * 2;
}

int func5(int x) {
    return func6(x + 5) - 2;
}

int func4(int x) {
    return func5(x * 3) + 7;
}

int func3(int x) {
    return func4(x / 2) * 3;
}

int func2(int x) {
    return func3(x + 10) - 5;
}

int func1(int x) {
    return func2(x * 2) + 1;
}

int main() {
    volatile int result = 0;
    volatile int iterations = 10000000; // 10 million iterations
    
    // Loop that calls the deep function chain
    for (int i = 0; i < iterations; i++) {
        result += func1(i);
    }
    
    // Return result to prevent optimization
    return result % 256; // Modulo to keep return value in valid range
}
