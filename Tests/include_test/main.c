/* Test file demonstrating #include from a subfolder */

#include "math_utils.h"

int main() {
    volatile int iterations = 1000000;  /* 1 million iterations */
    volatile int result = 0;
    
    /* Loop to test actual execution time, not just startup */
    for (int i = 0; i < iterations; i++) {
        int a = 3;
        int b = 4;
        
        /* square(3) = 9 */
        int sq = square(a);
        
        /* cube(2) = 8 */
        int cb = cube(2);
        
        /* sum_of_squares(3, 4) = 9 + 16 = 25 */
        int sos = sum_of_squares(a, b);
        
        result += sq + cb + sos;
    }
    
    /* Return result modulo to keep in valid range */
    return result % 256;
}
