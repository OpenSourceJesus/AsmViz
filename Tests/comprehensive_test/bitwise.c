/* Bit-shifting and bitwise operations */

/* Left shift */
int left_shift(int value, int shift) {
    return value << shift;
}

/* Right shift */
int right_shift(int value, int shift) {
    return value >> shift;
}

/* Bitwise AND */
int bitwise_and(int a, int b) {
    return a & b;
}

/* Bitwise OR */
int bitwise_or(int a, int b) {
    return a | b;
}

/* Bitwise XOR */
int bitwise_xor(int a, int b) {
    return a ^ b;
}

/* Bitwise NOT */
int bitwise_not(int a) {
    return ~a;
}

/* Combined bitwise operations */
int bitwise_combined(int a, int b, int c) {
    int result = (a << 2) & (b >> 1);
    result = result | (c & 0xFF);
    result = result ^ (a << 1);
    return ~result;
}

/* Power of 2 using left shift */
int power_of_2(int n) {
    if (n < 0) {
        return 0;
    }
    return 1 << n;  /* 2^n */
}

/* Extract bits using shifting and masking */
int extract_bits(int value, int start, int count) {
    int mask = ((1 << count) - 1) << start;
    return (value & mask) >> start;
}

/* Set bits using bitwise OR */
int set_bits(int value, int bits) {
    return value | bits;
}

/* Clear bits using bitwise AND and NOT */
int clear_bits(int value, int bits) {
    return value & ~bits;
}

/* Toggle bits using bitwise XOR */
int toggle_bits(int value, int bits) {
    return value ^ bits;
}

/* Compound bitwise assignments */
int test_compound_bitwise(int a, int b) {
    int result = a;
    result <<= 2;  /* result = result << 2 */
    result >>= 1;  /* result = result >> 1 */
    result &= b;   /* result = result & b */
    result |= a;   /* result = result | a */
    result ^= b;   /* result = result ^ b */
    return result;
}
