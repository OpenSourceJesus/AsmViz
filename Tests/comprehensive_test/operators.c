/* Advanced operators: compound assignment, increment/decrement, ternary */

/* Compound assignment operators */
int test_compound_assignment(int a, int b) {
    int result = a;
    
    result += b;   /* result = result + b */
    result -= a;   /* result = result - a */
    result *= 2;   /* result = result * 2 */
    result /= 2;   /* result = result / 2 */
    result %= 7;   /* result = result % 7 */
    
    return result;
}

/* Increment and decrement operators */
int test_increment_decrement(int a) {
    int x = a;
    int y = a;
    
    /* Pre-increment */
    int pre_inc = ++x;
    
    /* Post-increment */
    int post_inc = y++;
    
    /* Pre-decrement */
    int pre_dec = --x;
    
    /* Post-decrement */
    int post_dec = y--;
    
    return pre_inc + post_inc + pre_dec + post_dec + x + y;
}

/* Ternary operator */
int test_ternary(int a, int b) {
    int max = (a > b) ? a : b;
    int min = (a < b) ? a : b;
    int abs = (a < 0) ? -a : a;
    
    return max + min + abs;
}

/* Nested ternary */
int test_nested_ternary(int a, int b, int c) {
    int result = (a > b) ? ((a > c) ? a : c) : ((b > c) ? b : c);
    return result;
}

/* Ternary with function calls */
int test_ternary_with_ops(int a, int b) {
    int result = (a + b > 10) ? (a * 2) : (b * 2);
    return result;
}

/* Combined operators */
int test_combined_operators(int a, int b) {
    int result = a;
    
    /* Mix compound assignment with bitwise */
    result += b;
    result <<= 1;
    result &= 0xFF;
    result |= 0x80;
    result ^= 0x40;
    
    /* Use increment */
    ++result;
    result++;
    
    /* Use ternary */
    result = (result > 100) ? result - 50 : result + 50;
    
    return result;
}

/* Complex expression with all operators */
int test_complex_expression(int a, int b, int c) {
    int x = a;
    int y = b;
    
    /* Complex expression */
    int result = ((x++ + ++y) << 2) & ((x-- - --y) >> 1);
    result = (result > 0) ? result | 0xFF : result & 0x00;
    result += c;
    result *= 2;
    result %= 256;
    
    return result;
}

/* Address-of operator */
int test_address_of(int a, int *ptr) {
    ptr = &a;  /* Get address of a */
    return *ptr;  /* Dereference pointer */
}

/* Pointer arithmetic with increment */
int test_pointer_increment(int *arr, int len) {
    int sum = 0;
    int *p = arr;
    
    for (int i = 0; i < len; i = i + 1) {
        sum += *p;
        p++;  /* Increment pointer */
    }
    
    return sum;
}
