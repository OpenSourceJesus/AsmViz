void test ()
{
}

int main ()
{
    volatile int iterations = 1000000;  /* 1 million iterations */
    
    /* Loop to test actual execution time, not just startup */
    for (int i = 0; i < iterations; i++) {
        test ();
    }
    
    return 0;
}