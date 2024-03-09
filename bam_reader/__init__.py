import struct
import zlib
from typing import BinaryIO

from bam_reader.cutils import bin2code

FLG_FEXTRA = 0b00000100

LAST_BLOCK = b"\x1f\x8b\x08\x04\x00\x00\x00\x00\x00\xff\x06\x00\x42\x43\x02\x00\x1b\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00"


class BamError(Exception):
    pass


class BzgfError(BamError):
    pass


def decompress_bzgf(f: BinaryIO) -> bytearray:
    data = bytearray()

    while header := f.read(12):
        id1, id2, cm, flg, mtime, xfl, os_, xlen = struct.unpack("4BI2BH", header)

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


def extract_sequence(bam: BinaryIO) -> list[bytes]:
    magic, l_text = struct.unpack("<4sI", bam.read(8))

    if magic != b"BAM\x01":
        raise BamError("Incorrect magic")

    bam.seek(l_text, 1)

    (n_ref,) = struct.unpack("<I", bam.read(4))

    for i in range(n_ref):
        (l_name,) = struct.unpack("<I", bam.read(4))
        bam.seek(l_name + 4, 1)

    while header := bam.read(36):
        (
            block_size,
            ref_id,
            pos,
            l_read_name,
            mapq,
            bin_,
            n_cigar_op,
            flag,
            l_seq,
            next_ref_id,
            next_pos,
            tlen,
        ) = struct.unpack("<I2i2B3HI3i", header)

        end = bam.tell() + block_size - 32

        bam.seek(l_read_name + 4 * n_cigar_op, 1)

        yield bin2code(bam.read((l_seq + 1) // 2), l_seq)

        bam.seek(end)
