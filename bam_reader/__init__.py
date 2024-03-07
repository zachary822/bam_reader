import struct
import zlib
from typing import BinaryIO

FLG_FEXTRA = 0b00000100

LAST_BLOCK = b"\x1f\x8b\x08\x04\x00\x00\x00\x00\x00\xff\x06\x00\x42\x43\x02\x00\x1b\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00"


class BamError(Exception):
    pass


class BzgfError(BamError):
    pass


def decompress_bzgf(f: BinaryIO) -> bytearray:
    data = bytearray()

    while LAST_BLOCK != f.peek(28):
        id1, id2, cm, flg, mtime, xfl, os_, xlen = struct.unpack("4BI2BH", f.read(12))

        if not (flg & FLG_FEXTRA):
            raise BzgfError("gzip flag incorrectly set")

        end = f.tell() + xlen

        bsize = 0
        while f.tell() < end:
            si1, si2, slen = struct.unpack("2BH", f.read(4))

            sdata = f.read(slen)
            if si1 == 66 and si2 == 67:
                (bsize,) = struct.unpack("H", sdata)
                break
        else:
            raise BzgfError("block size not found")

        f.seek(end)
        cdata = f.read(bsize - xlen - 19)

        infl = zlib.decompress(cdata, wbits=-zlib.MAX_WBITS)

        crc_infl = zlib.crc32(infl)

        (crc32, isize) = struct.unpack("2I", f.read(8))

        if crc_infl != crc32:
            raise BzgfError("crc32 does not match")

        if isize != len(infl):
            raise BzgfError("decompressed size does not match")

        data.extend(infl)

    return data
