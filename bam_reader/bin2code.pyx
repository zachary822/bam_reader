from libc.stdlib cimport malloc, free

CODE = b"=ACMGRSVTWYHKDBN"

def bin2code(unsigned char *bin, int size):
    cdef int i, b_len = len(bin)
    cdef unsigned char * result = <unsigned char *> malloc(b_len * 2 * sizeof(unsigned char))
     
    for i in range(b_len):
        result[i * 2] = CODE[bin[i] >> 4]
        result[i * 2 + 1] = CODE[bin[i] & 0b1111]

    try:
        return result[:size]
    finally:
        free(result)