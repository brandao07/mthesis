#include <stdio.h>
#include <stdint.h>
#include <inttypes.h>  // for PRIu64

uint64_t fibonacci(int n) {
    if (n == 0) return 0;
    if (n == 1) return 1;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main(void) {
    int n = 49;
    printf("%" PRIu64 "\n", fibonacci(n));
    return 0;
}