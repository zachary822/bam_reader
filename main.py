import argparse
import struct
from io import BytesIO
from itertools import islice
from pathlib import Path

from bam_reader import decompress_bzgf

CIGAR = b"MIDNSHP=X"
CODE = b"=ACMGRSVTWYHKDBN"

VAL_TYPE = bytes.maketrans(b"AcCsS", b"cbBhH")


class CustomBytesIO(BytesIO):
    def read0(self):
        arr = bytearray()

        while c := self.read(1):
            if c == b"\x00" or c == b"":
                break
            arr.append(int.from_bytes(c, "little"))
        return arr


def seq_to_code(seq: bytes):
    for s in seq:
        yield CODE[s >> 4]
        yield CODE[s & 0b1111]


def translate_cigar(cigar: bytes):
    for c in cigar:
        yield from str(c >> 4).encode("ascii")
        yield CIGAR[c & 0x0F]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("file", type=Path)

    args = parser.parse_args()

    with args.file.open("rb") as f:
        bam = CustomBytesIO(decompress_bzgf(f))

    bam.seek(0)

    magic, l_text = struct.unpack("<4sI", bam.read(8))

    assert magic == b"BAM\x01"

    (text, n_ref) = struct.unpack(f"<{l_text}sI", bam.read(l_text + 4))

    ref_names = []

    for i in range(n_ref):
        (l_name,) = struct.unpack("<I", bam.read(4))
        (name, l_ref) = struct.unpack(f"<{l_name}sI", bam.read(l_name + 4))
        ref_names.append(name.rstrip(b"\x00"))

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

        end = bam.tell() + block_size - 32  # excludes block_size

        read_name = bam.read(l_read_name).rstrip(b"\x00")

        cigar_bytes = struct.unpack(f"<{n_cigar_op}I", bam.read(4 * n_cigar_op))

        cigar = bytes(translate_cigar(cigar_bytes))

        seq = bam.read((l_seq + 1) // 2)

        code = bytes(islice(seq_to_code(seq), l_seq))

        qual = bytes(q + 33 for q in bam.read(l_seq))

        while bam.tell() < end:
            (tag, val_type) = struct.unpack("<2s1s", bam.read(3))

            if val_type in b"AcCsSiIf":
                fmt = f"<{val_type.translate(VAL_TYPE).decode('ascii')}"
                (data,) = struct.unpack(fmt, bam.read(struct.calcsize(fmt)))
            elif val_type in b"ZH":
                data = bam.read0()
            elif val_type == b"B":
                (v, count) = struct.unpack("<cI", bam.read(5))
                fmt = f"<{count}{v.translate(VAL_TYPE).decode('ascii')}"
                (data,) = struct.unpack(fmt, bam.read(struct.calcsize(fmt)))
            else:
                raise Exception("PANIC!!!")
