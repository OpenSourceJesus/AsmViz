int test_sum (int *a, int length)
{
	int sum = 0;
	for (int i = 0; i < length; i++)
		sum += a[i];
	return sum;
}

int main ()
{
	volatile int iterations = 100000;  /* 100,000 iterations */
	
	int arr[64];
	for (int i = 0; i < 64; i++)
		arr[i] = i;
	/* Loop to test actual execution time, not just startup */
	for (int i = 0; i < iterations; i++)
		test_sum (arr, 64);
	
	return 0;
}