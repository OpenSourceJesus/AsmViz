/* Utility functions with various C features */

/* Binary operations: +, -, *, /, ==, <, >, >=, <=, !=, %, &&, || */
int test_binary_ops(int a, int b) {
    int add_result = a + b;
    int sub_result = a - b;
    int mul_result = a * b;
    int div_result = 0;
    
    if (b != 0) {
        div_result = a / b;
    }
    
    int mod_result = 0;
    if (b != 0) {
        mod_result = a % b;
    }
    
    int eq_result = (a == b);
    int ne_result = (a != b);
    int lt_result = (a < b);
    int gt_result = (a > b);
    int le_result = (a <= b);
    int ge_result = (a >= b);
    
    int and_result = (a > 0) && (b > 0);
    int or_result = (a < 0) || (b < 0);
    
    return add_result + sub_result + mul_result + div_result + mod_result + 
           eq_result + ne_result + lt_result + gt_result + le_result + ge_result +
           and_result + or_result;
}

/* Unary operations: -, ! */
int test_unary_ops(int x) {
    int neg = -x;
    int not_val = !x;
    
    return neg + not_val;
}

/* Complex expressions with parentheses */
int test_complex_expressions(int a, int b, int c) {
    int expr1 = (a + b) * c;
    int expr2 = a * (b - c);
    int expr3 = (a + b) / (c + 1);
    int expr4 = (a * b) + (c * 2);
    
    return expr1 + expr2 + expr3 + expr4;
}

/* Nested function calls */
int nested_calls(int x) {
    /* Call functions that call other functions */
    int result = test_binary_ops(x, x + 1);
    result = result + test_unary_ops(result);
    result = result + test_complex_expressions(result, result + 1, result + 2);
    
    return result;
}

/* Multiple return statements */
int multiple_returns(int x) {
    if (x < 0) {
        return -1;
    }
    
    if (x == 0) {
        return 0;
    }
    
    if (x < 10) {
        return 1;
    }
    
    if (x < 100) {
        return 2;
    }
    
    return 3;
}

/* Single return statement (for metamorphic return site optimization) */
int single_return(int x) {
    int result = x * 2;
    result = result + 10;
    return result;
}

/* Character constants */
int test_char_constants() {
    int a = 'A';
    int b = 'B';
    int c = 'C';
    
    return a + b + c;
}

/* Numeric constants (decimal, hex, octal) */
int test_numeric_constants() {
    int dec = 100;
    int hex = 0xFF;
    int oct = 077;
    
    return dec + hex + oct;
}

/* Variable declarations with initialization */
int test_declarations() {
    int a = 10;
    int b = 20;
    int c = a + b;
    int d = c * 2;
    int e = d / 4;
    
    return a + b + c + d + e;
}

/* Variable assignments */
int test_assignments() {
    int x = 0;
    x = 10;
    x = x + 5;
    x = x - 3;
    x = x * 2;
    x = x / 4;
    
    return x;
}

/* Mixed operations with all operators */
int test_mixed_operations(int a, int b, int c) {
    int result = 0;
    
    result = a + b;
    result = result - c;
    result = result * 2;
    result = result / 2;
    result = result % 7;
    
    if (result == a) {
        result = result + 1;
    }
    
    if (result != b) {
        result = result + 2;
    }
    
    if (result < b) {
        result = result * 2;
    }
    
    if (result > c) {
        result = result - 1;
    }
    
    if (result <= a) {
        result = result + 3;
    }
    
    if (result >= b) {
        result = result - 2;
    }
    
    if ((result > 0) && (result < 100)) {
        result = result * 2;
    }
    
    if ((result < 0) || (result > 1000)) {
        result = result + 10;
    }
    
    return result;
}
