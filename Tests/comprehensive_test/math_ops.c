/* Small functions for indexed-jump optimization (<1024 bytes) */

/* Addition - small function */
int add(int a, int b) {
    return a + b;
}

/* Subtraction - small function */
int subtract(int a, int b) {
    return a - b;
}

/* Multiplication - small function */
int multiply(int x, int y) {
    return x * y;
}

/* Division - small function */
int divide(int x, int y) {
    if (y == 0) {
        return 0;
    }
    return x / y;
}

/* Comparison - small function with single return */
int compare_values(int a, int b) {
    if (a < b) {
        return -1;
    } else if (a == b) {
        return 0;
    } else {
        return 1;
    }
}

/* Absolute value - small function */
int abs_value(int x) {
    if (x < 0) {
        return -x;
    }
    return x;
}

/* Maximum - small function */
int max(int a, int b) {
    if (a > b) {
        return a;
    }
    return b;
}

/* Minimum - small function */
int min(int a, int b) {
    if (a < b) {
        return a;
    }
    return b;
}

/* Power of 2 - small function */
int power2(int n) {
    if (n <= 0) {
        return 1;
    }
    return 2 * power2(n - 1);
}

/* Modulo - small function */
int modulo(int a, int b) {
    if (b == 0) {
        return 0;
    }
    return a - (a / b) * b;
}
