/* Array operations and pointer handling */

/* Global array */
int global_array[10];

/* Sum array elements */
int sum_array_elements(int *arr, int len) {
    int sum = 0;
    for (int i = 0; i < len; i = i + 1) {
        sum = sum + arr[i];
    }
    return sum;
}

/* Find maximum in array */
int find_max(int *arr, int len) {
    if (len <= 0) {
        return 0;
    }
    
    int max = arr[0];
    for (int i = 1; i < len; i = i + 1) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}

/* Find minimum in array */
int find_min(int *arr, int len) {
    if (len <= 0) {
        return 0;
    }
    
    int min = arr[0];
    for (int i = 1; i < len; i = i + 1) {
        if (arr[i] < min) {
            min = arr[i];
        }
    }
    return min;
}

/* Reverse array */
void reverse_array(int *arr, int len) {
    int i = 0;
    int j = len - 1;
    
    while (i < j) {
        int temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
        i = i + 1;
        j = j - 1;
    }
}

/* Count elements matching condition */
int count_matching(int *arr, int len, int value) {
    int count = 0;
    for (int i = 0; i < len; i = i + 1) {
        if (arr[i] == value) {
            count = count + 1;
        }
    }
    return count;
}

/* Initialize array with values */
void init_array(int *arr, int len, int start_value) {
    for (int i = 0; i < len; i = i + 1) {
        arr[i] = start_value + i;
    }
}

/* Test array operations with modulo */
int test_array_modulo(int *arr, int len) {
    int sum = 0;
    for (int i = 0; i < len; i = i + 1) {
        /* Use modulo to wrap indices */
        int index = i % len;
        sum = sum + arr[index];
    }
    return sum;
}

/* Test array with all comparison operators */
int test_array_comparisons(int *arr, int len) {
    int count = 0;
    for (int i = 0; i < len; i = i + 1) {
        if (arr[i] > 10) {
            count = count + 1;
        }
        if (arr[i] >= 20) {
            count = count + 1;
        }
        if (arr[i] <= 5) {
            count = count + 1;
        }
        if (arr[i] != 0) {
            count = count + 1;
        }
    }
    return count;
}

/* Test logical operators with arrays */
int test_array_logical(int *arr, int len) {
    int count = 0;
    for (int i = 0; i < len; i = i + 1) {
        if ((arr[i] > 0) && (arr[i] < 100)) {
            count = count + 1;
        }
        if ((arr[i] < 0) || (arr[i] > 1000)) {
            count = count + 1;
        }
    }
    return count;
}
