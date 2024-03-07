from libc.stdlib cimport malloc

CODE = b"=ACMGRSVTWYHKDBN"

def bin2code(unsigned char[] bin):
    cdef int i
    cdef unsigned char * result = <unsigned char *> malloc(len(bin) * 2 * sizeof(unsigned char))
     
    for i in range(len(bin)):
        result[i * 2] = CODE[bin[i] >> 4]
        result[i * 2 + 1] = CODE[bin[i] & 0b1111]

    return result
