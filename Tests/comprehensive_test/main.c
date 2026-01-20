/* Main entry point - tests function calls, local variables, and control flow */

extern int add(int a, int b);
extern int subtract(int a, int b);
extern int multiply(int a, int b);
extern int divide(int a, int b);
extern int compare_values(int a, int b);
extern int factorial(int n);
extern int fibonacci(int n);
extern void process_data(int *data, int len);
extern int isr_timer_handler(void);
extern int irq_keyboard_handler(void);
extern int sum_array_elements(int *arr, int len);
extern int find_max(int *arr, int len);
extern int find_min(int *arr, int len);
extern void reverse_array(int *arr, int len);
extern int test_array_modulo(int *arr, int len);
extern int test_array_comparisons(int *arr, int len);
extern int test_array_logical(int *arr, int len);
extern int left_shift(int value, int shift);
extern int right_shift(int value, int shift);
extern int bitwise_and(int a, int b);
extern int bitwise_or(int a, int b);
extern int bitwise_xor(int a, int b);
extern int bitwise_not(int a);
extern int test_compound_bitwise(int a, int b);
extern int power_of_2(int n);
extern int test_struct_operations(void);
extern int test_compound_assignment(int a, int b);
extern int test_increment_decrement(int a);
extern int test_ternary(int a, int b);
extern int test_combined_operators(int a, int b);

/* Global variables from globals.c */
extern int global_counter;
extern int global_result;

/* SIMD-packed globals (1-8 bits) */
#ifdef GCC
#define int1_t char
#define int2_t char
#define int3_t char
#define int4_t char
#define int5_t char
#define int6_t char
#define int7_t char
#define int8_t char
#endif
#ifndef GCC
#define int1_t auto _Alignas(1) char
#define int2_t auto _Alignas(2) char
#define int3_t auto _Alignas(3) char
#define int4_t auto _Alignas(4) char
#define int5_t auto _Alignas(5) char
#define int6_t auto _Alignas(6) char
#define int7_t auto _Alignas(7) char
#define int8_t auto _Alignas(8) char
#endif

extern int1_t flag_1bit;
extern int2_t counter_2bit;
extern int3_t state_3bit;
extern int4_t mode_4bit;
extern int5_t level_5bit;
extern int6_t index_6bit;
extern int7_t offset_7bit;
extern int8_t value_8bit;

int main() {
    /* Test local variables with indexed stack pointer */
    int local_a = 10;
    int local_b = 20;
    int local_c = 0;
    int local_d = 100;
    
    /* Test function calls to small functions (indexed-jump) */
    local_c = add(local_a, local_b);
    local_d = subtract(local_d, local_c);
    
    /* Test arithmetic operations */
    int result1 = multiply(5, 6);
    int result2 = divide(100, 4);
    
    /* Test comparison operations */
    int cmp1 = compare_values(result1, result2);
    int cmp2 = compare_values(local_a, local_b);
    
    /* Test control flow with all comparison operators */
    if (cmp1 == 1) {
        local_a = local_a + 10;
    } else if (cmp1 != 0) {
        local_b = local_b + 20;
    }
    
    /* Test comparison operators */
    int gt_test = (local_a > local_b);
    int ge_test = (local_a >= local_b);
    int le_test = (local_a <= local_b);
    
    /* Test while loop */
    int counter = 0;
    while (counter < 5) {
        counter = counter + 1;
        local_c = local_c + counter;
    }
    
    /* Test for loop */
    int sum = 0;
    for (int i = 0; i < 10; i = i + 1) {
        sum = sum + i;
    }
    
    /* Test array operations - use global array from arrays.c */
    extern int global_array[10];
    
    /* Initialize array */
    for (int i = 0; i < 10; i = i + 1) {
        global_array[i] = i * 2;
    }
    
    int arr_sum = 0;
    for (int i = 0; i < 10; i = i + 1) {
        arr_sum = arr_sum + global_array[i];
    }
    
    /* Test modulo operator */
    int mod_result = local_a % 7;
    
    /* Test logical operators */
    int and_result = (local_a > 0) && (local_b > 0);
    int or_result = (local_a < 0) || (local_b < 0);
    
    /* Test bit-shifting operations */
    int shift_left = local_a << 2;
    int shift_right = local_b >> 1;
    int shift_result = left_shift(10, 3) + right_shift(100, 2);
    
    /* Test bitwise operations */
    int bit_and = local_a & local_b;
    int bit_or = local_a | local_b;
    int bit_xor = local_a ^ local_b;
    int bit_not = ~local_a;
    int bitwise_result = bitwise_and(5, 3) + bitwise_or(5, 3) + bitwise_xor(5, 3) + bitwise_not(5);
    
    /* Test compound bitwise assignments */
    int compound_bitwise = test_compound_bitwise(local_a, local_b);
    
    /* Test power of 2 using shift */
    int pow2 = power_of_2(5);
    
    /* Test struct operations */
    int struct_result = test_struct_operations();
    
    /* Test compound assignment operators */
    int compound_result = test_compound_assignment(local_a, local_b);
    
    /* Test increment/decrement */
    int inc_dec_result = test_increment_decrement(local_a);
    
    /* Test ternary operator */
    int ternary_result = test_ternary(local_a, local_b);
    int ternary_direct = (local_a > local_b) ? local_a : local_b;
    
    /* Test combined operators */
    int combined_result = test_combined_operators(local_a, local_b);
    
    /* Test increment/decrement directly */
    int pre_inc = ++local_a;
    int post_inc = local_b++;
    int pre_dec = --local_a;
    int post_dec = local_b--;
    
    /* Test compound assignments directly */
    local_a += 10;
    local_b -= 5;
    local_c *= 2;
    local_d /= 2;
    int mod_temp = local_a;
    mod_temp %= 7;
    
    /* Test function calls to larger functions */
    int fact_result = factorial(5);
    int fib_result = fibonacci(7);
    
    /* Test global variable access */
    global_counter = global_counter + 1;
    global_result = fact_result + fib_result;
    
    /* Test SIMD-packed global variables */
    flag_1bit = 1;
    counter_2bit = 3;
    state_3bit = 5;
    mode_4bit = 10;
    level_5bit = 15;
    index_6bit = 20;
    offset_7bit = 30;
    value_8bit = 50;
    
    /* Test reading SIMD-packed variables */
    int read_flag = flag_1bit;
    int read_counter = counter_2bit;
    int read_state = state_3bit;
    
    /* Test unary operations */
    int neg_value = -local_a;
    int not_value = !cmp1;
    
    /* Test complex expressions */
    int complex = (local_a + local_b) * (local_c - local_d) / 2;
    
    /* Test nested function calls */
    int nested = add(multiply(2, 3), subtract(10, 5));
    
    /* Test array function calls */
    extern int global_array[10];
    int arr_sum_func = sum_array_elements(global_array, 10);
    int arr_max = find_max(global_array, 10);
    int arr_min = find_min(global_array, 10);
    
    /* Test array operations */
    reverse_array(global_array, 10);
    int arr_mod = test_array_modulo(global_array, 10);
    int arr_cmp = test_array_comparisons(global_array, 10);
    int arr_log = test_array_logical(global_array, 10);
    
    /* Test interrupt callbacks (should use zero-latency SIMD access) */
    int timer_result = isr_timer_handler();
    int keyboard_result = irq_keyboard_handler();
    
    /* Final return with complex expression including all new features */
    return local_c + result1 + result2 + fact_result + fib_result + complex + nested + 
           arr_sum + arr_sum_func + arr_max + arr_min + arr_mod + arr_cmp + arr_log +
           shift_result + bitwise_result + compound_bitwise + pow2 + struct_result +
           compound_result + inc_dec_result + ternary_result + ternary_direct + combined_result +
           pre_inc + post_inc + pre_dec + post_dec + mod_temp;
}
