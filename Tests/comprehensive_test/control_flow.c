/* Control flow structures: if/else, while, for loops */

/* Factorial using while loop */
int factorial(int n) {
    int result = 1;
    int i = 1;
    
    while (i <= n) {
        result = result * i;
        i = i + 1;
    }
    
    return result;
}

/* Fibonacci using for loop */
int fibonacci(int n) {
    if (n <= 0) {
        return 0;
    }
    if (n == 1) {
        return 1;
    }
    
    int a = 0;
    int b = 1;
    int temp = 0;
    
    for (int i = 2; i <= n; i = i + 1) {
        temp = a + b;
        a = b;
        b = temp;
    }
    
    return b;
}

/* Sum array using while loop */
int sum_array(int *arr, int len) {
    int sum = 0;
    int i = 0;
    
    while (i < len) {
        sum = sum + arr[i];
        i = i + 1;
    }
    
    return sum;
}

/* Count even numbers using for loop */
int count_even(int *arr, int len) {
    int count = 0;
    
    for (int i = 0; i < len; i = i + 1) {
        if ((arr[i] % 2) == 0) {
            count = count + 1;
        }
    }
    
    return count;
}

/* Nested if/else */
int classify_number(int n) {
    if (n < 0) {
        return -1;  /* Negative */
    } else if (n == 0) {
        return 0;   /* Zero */
    } else if (n < 10) {
        return 1;   /* Single digit */
    } else if (n < 100) {
        return 2;   /* Two digits */
    } else {
        return 3;   /* Three or more digits */
    }
}

/* Nested loops */
int matrix_sum(int size) {
    int sum = 0;
    
    for (int i = 0; i < size; i = i + 1) {
        for (int j = 0; j < size; j = j + 1) {
            int index = i * size + j;
            sum = sum + index;
        }
    }
    
    return sum;
}

/* Complex control flow with multiple returns */
int find_value(int *arr, int len, int target) {
    for (int i = 0; i < len; i = i + 1) {
        if (arr[i] == target) {
            return i;  /* Found at index i */
        }
    }
    return -1;  /* Not found */
}

/* While with break-like pattern */
int sum_until_negative(int *arr, int len) {
    int sum = 0;
    int i = 0;
    
    while (i < len) {
        if (arr[i] < 0) {
            return sum;  /* Early return */
        }
        sum = sum + arr[i];
        i = i + 1;
    }
    
    return sum;
}

/* Process data with nested control flow */
void process_data(int *data, int len) {
    int processed = 0;
    
    for (int i = 0; i < len; i = i + 1) {
        if (data[i] > 0) {
            data[i] = data[i] * 2;
            processed = processed + 1;
        } else if (data[i] < 0) {
            data[i] = -data[i];
            processed = processed + 1;
        }
    }
}
