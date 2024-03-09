REV_COM = bytes.maketrans(b"AGCTYRWSKMDVHB", b"TCGARYWSMKHBDV")


def reverse_complement(code: bytes) -> bytes:
    return code.translate(REV_COM)[::-1]
