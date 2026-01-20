/* Test file for indexed stack pointer system (16-byte intervals) */

// Simple function with local variables to test indexed stack allocation
int test_local_vars() {
    int a = 10;
    int b = 20;
    int c = 30;
    int result = a + b + c;
    return result;
}

// Function with multiple operations to test stack slot management
int test_stack_operations(int x, int y) {
    int local1 = x * 2;
    int local2 = y + 5;
    int local3 = local1 - local2;
    int local4 = local3 * 3;
    return local4;
}

// Function to test pointer compression (multiple stack slots)
int test_multiple_slots() {
    int slot0 = 1;
    int slot1 = 2;
    int slot2 = 3;
    int slot3 = 4;
    // These should be allocated in slots 0, 1, 2, 3 (each 16 bytes)
    return slot0 + slot1 + slot2 + slot3;
}

int main() {
    volatile int iterations = 1000000;  /* 1 million iterations */
    volatile int result = 0;
    
    /* Loop to test actual execution time, not just startup */
    for (int i = 0; i < iterations; i++) {
        int result1 = test_local_vars();
        int result2 = test_stack_operations(10, 20);
        int result3 = test_multiple_slots();
        result += result1 + result2 + result3;
    }
    
    return result % 256;  /* Modulo to keep return value in valid range */
}
