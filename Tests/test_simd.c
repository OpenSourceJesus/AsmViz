#ifdef GCC
#define int1_t char
#else
#define int1_t auto _Alignas(8) char
#endif

int1_t a;

int main ()
{
	volatile int iterations = 1000000;  /* 1 million iterations */
	
	/* Loop to test actual execution time, not just startup */
	for (int i = 0; i < iterations; i++) {
		a = 5000;
	}
	
	return 0;
}