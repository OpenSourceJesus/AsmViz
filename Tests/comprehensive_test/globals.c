/* Global variables: regular and SIMD-packed (1-8 bits) */

/* Regular global variables */
int global_counter = 0;
int global_result = 0;
int global_sum = 0;
int global_max = 0;
int global_min = 1000;

/* SIMD-packed global variables (1-8 bits) using _Alignas convention */
/* These will be packed into xmm15 SIMD register for zero-latency access */

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

/* 1-bit flag */
int1_t flag_1bit = 0;

/* 2-bit counter (0-3) */
int2_t counter_2bit = 0;

/* 3-bit state (0-7) */
int3_t state_3bit = 0;

/* 4-bit mode (0-15) */
int4_t mode_4bit = 0;

/* 5-bit level (0-31) */
int5_t level_5bit = 0;

/* 6-bit index (0-63) */
int6_t index_6bit = 0;

/* 7-bit offset (0-127) */
int7_t offset_7bit = 0;

/* 8-bit value (0-255) */
int8_t value_8bit = 0;

/* Function to test global variable access */
int test_globals() {
    global_counter = global_counter + 1;
    global_sum = global_sum + global_counter;
    
    if (global_counter > global_max) {
        global_max = global_counter;
    }
    
    if (global_counter < global_min) {
        global_min = global_counter;
    }
    
    return global_sum;
}

/* Function to test SIMD-packed variable access */
int test_simd_packed() {
    /* Write to SIMD-packed variables */
    flag_1bit = 1;
    counter_2bit = 3;
    state_3bit = 5;
    mode_4bit = 10;
    level_5bit = 15;
    index_6bit = 20;
    offset_7bit = 30;
    value_8bit = 50;
    
    /* Read from SIMD-packed variables */
    int result = 0;
    result = result + flag_1bit;
    result = result + counter_2bit;
    result = result + state_3bit;
    result = result + mode_4bit;
    result = result + level_5bit;
    result = result + index_6bit;
    result = result + offset_7bit;
    result = result + value_8bit;
    
    return result;
}

/* Function to test mixed global access */
int test_mixed_globals() {
    /* Access regular globals */
    global_counter = global_counter + 1;
    
    /* Access SIMD-packed globals */
    flag_1bit = global_counter % 2;
    counter_2bit = global_counter % 4;
    state_3bit = global_counter % 8;
    
    return global_counter + flag_1bit + counter_2bit + state_3bit;
}
