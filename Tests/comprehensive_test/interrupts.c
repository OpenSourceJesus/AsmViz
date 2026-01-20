/* Interrupt callback functions - should use zero-latency SIMD register access */

/* SIMD-packed kernel flags (accessed via zero-latency SIMD register) */
#ifdef GCC
#define int1_t char
#define int2_t char
#define int3_t char
#endif
#ifndef GCC
#define int1_t auto _Alignas(1) char
#define int2_t auto _Alignas(2) char
#define int3_t auto _Alignas(3) char
#endif

extern int1_t flag_1bit;
extern int2_t counter_2bit;
extern int3_t state_3bit;

/* Timer interrupt service routine */
/* Naming pattern: isr_* triggers interrupt callback detection */
int isr_timer_handler(void) {
    /* Zero-latency access to SIMD-packed kernel flags */
    /* These reads/writes use direct SIMD register access, no memory stalls */
    
    int current_flag = flag_1bit;
    int current_counter = counter_2bit;
    int current_state = state_3bit;
    
    /* Update flags without memory reads (zero-latency) */
    flag_1bit = !current_flag;  /* Toggle flag */
    counter_2bit = (current_counter + 1) % 4;
    state_3bit = (current_state + 1) % 8;
    
    return current_flag + current_counter + current_state;
}

/* Keyboard interrupt request handler */
/* Naming pattern: irq_* triggers interrupt callback detection */
int irq_keyboard_handler(void) {
    /* Zero-latency access to kernel flags */
    int flag = flag_1bit;
    int counter = counter_2bit;
    
    /* Update state based on flag */
    if (flag == 1) {
        state_3bit = (state_3bit + 1) % 8;
    } else {
        state_3bit = 0;
    }
    
    /* Increment counter */
    counter_2bit = (counter + 1) % 4;
    
    return flag + counter + state_3bit;
}

/* Generic interrupt handler */
/* Naming pattern: *_handler triggers interrupt callback detection */
int generic_interrupt_handler(void) {
    /* Access SIMD-packed variables with zero latency */
    int result = flag_1bit;
    result = result + counter_2bit;
    result = result + state_3bit;
    
    /* Update flags */
    flag_1bit = 1;
    counter_2bit = 2;
    state_3bit = 3;
    
    return result;
}

/* Interrupt callback with naming pattern */
/* Naming pattern: *_callback triggers interrupt callback detection */
int timer_callback(void) {
    /* Zero-latency SIMD register access */
    int val = flag_1bit;
    flag_1bit = !val;
    return val;
}
