/* Test file for nested structs and complex function pointer calls */

struct Inner {
    int x;
    int y;
    void (*callback)(int);
};

struct Outer {
    struct Inner inner;
    struct Inner* inner_ptr;
    int value;
    struct Inner (*get_inner)(void);
    void (*handler)(struct Inner*);
};

struct Container {
    struct Outer outer;
    struct Outer* outer_ptr;
    struct Inner nested;
    struct Inner (*func_ptr)(struct Outer*);
};

// Global struct instances
struct Container container;
struct Outer outer;
struct Inner inner;

void test_func1(int x) {
    // Function pointer call through nested struct
    if (container.outer.inner.callback) {
        container.outer.inner.callback(x);
    }
}

void test_func2(void) {
    // Nested struct member access
    int val = container.outer.inner.x;
    val = container.outer.inner.y;
    
    // Function pointer call through pointer to nested struct
    if (container.outer.inner_ptr && container.outer.inner_ptr->callback) {
        container.outer.inner_ptr->callback(val);
    }
}

void test_func3(void) {
    // Function pointer that returns struct
    if (container.outer.get_inner) {
        struct Inner result = container.outer.get_inner();
        if (result.callback) {
            result.callback(result.x);
        }
    }
}

void test_func4(void) {
    // Function pointer that takes struct pointer
    if (container.outer.handler && container.outer.inner_ptr) {
        container.outer.handler(container.outer.inner_ptr);
    }
}

void test_func5(void) {
    // Complex nested struct function pointer
    if (container.func_ptr) {
        struct Inner result = container.func_ptr(container.outer_ptr);
        if (result.callback) {
            result.callback(result.x + result.y);
        }
    }
}

void test_func6(void) {
    // Array of structs with function pointers
    struct Inner handlers[10];
    int i = 5;
    if (handlers[i].callback) {
        handlers[i].callback(i);
    }
}

void test_func7(void) {
    // Triple nesting
    struct Deep1 {
        struct Deep2 {
            struct Deep3 {
                void (*deep_callback)(int);
                int value;
            } deep3;
            struct Deep3* deep3_ptr;
        } deep2;
    } deep1;
    
    if (deep1.deep2.deep3.deep_callback) {
        deep1.deep2.deep3.deep_callback(deep1.deep2.deep3.value);
    }
    
    if (deep1.deep2.deep3_ptr && deep1.deep2.deep3_ptr->deep_callback) {
        deep1.deep2.deep3_ptr->deep_callback(deep1.deep2.deep3_ptr->value);
    }
}

int main(void) {
    volatile int iterations = 1000000;  /* 1 million iterations */
    
    /* Loop to test actual execution time, not just startup */
    for (int i = 0; i < iterations; i++) {
        test_func1(1);
        test_func2();
        test_func3();
        test_func4();
        test_func5();
        test_func6();
        test_func7();
    }
    
    return 0;
}
