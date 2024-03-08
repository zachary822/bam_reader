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

def gc_fraction(unsigned char * code):
    cdef int gc = 0, at = 0;

    for c in code:
        if c == 67 or c == 71 or c == 83:
           gc += 1;
        elif c == 65 or c == 84 or c == 87:
           at += 1
    return gc / (gc + at)
           