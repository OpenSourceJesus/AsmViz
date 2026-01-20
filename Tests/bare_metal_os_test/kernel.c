/* Bare Metal OS Kernel
 * Simple kernel demonstrating C compilation with assembly and linker script
 */

/* Kernel state variables */
volatile int kernel_initialized = 0;
volatile int system_ready = 0;
volatile unsigned long tick_count = 0;

/* Simple memory management */
#define MAX_TASKS 8
volatile int task_count = 0;
volatile int active_task = 0;

/* Kernel functions */
void kernel_init(void) {
    kernel_initialized = 1;
    system_ready = 0;
    tick_count = 0;
    task_count = 0;
    active_task = 0;
}

void system_startup(void) {
    if (!kernel_initialized) {
        kernel_init();
    }
    system_ready = 1;
}

void kernel_tick(void) {
    if (system_ready) {
        tick_count++;
    }
}

int create_task(void) {
    if (task_count < MAX_TASKS) {
        task_count++;
        return task_count - 1;
    }
    return -1;
}

void switch_task(int task_id) {
    if (task_id >= 0 && task_id < task_count) {
        active_task = task_id;
    }
}

int get_active_task(void) {
    return active_task;
}

unsigned long get_tick_count(void) {
    return tick_count;
}

/* Interrupt handler (called from assembly) */
void interrupt_handler(void) {
    kernel_tick();
}

/* Main kernel entry point */
int main(void) {
    int task1, task2, task3;
    
    /* Initialize kernel */
    kernel_init();
    
    /* Start system */
    system_startup();
    
    /* Create some tasks */
    task1 = create_task();
    task2 = create_task();
    task3 = create_task();
    
    /* Switch between tasks */
    switch_task(task1);
    switch_task(task2);
    switch_task(task3);
    
    /* Simulate a million kernel operations */
    for (int i = 0; i < 1000000; i++) {
        kernel_tick();
    }
    
    /* Return success code */
    return 0;
}
