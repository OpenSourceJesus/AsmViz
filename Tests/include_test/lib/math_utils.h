/* Math utility functions - header in subfolder */

#ifndef MATH_UTILS_H
#define MATH_UTILS_H

int square(int x) {
    return x * x;
}

int cube(int x) {
    return x * x * x;
}

int sum_of_squares(int a, int b) {
    return square(a) + square(b);
}

#endif /* MATH_UTILS_H */
