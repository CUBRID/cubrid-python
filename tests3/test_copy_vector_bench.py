"""
Benchmark: COPY FROM STDIN (FORMAT BINARY) with 290k rows of (INT, VECTOR(256)).

Mirrors the annb workload so we can measure where time goes inside copy_session.
"""

import os
import random
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import CUBRIDdb  # noqa: E402


NUM_ROWS = 290_000
VEC_DIM = 256
CHUNK_ROWS = 4096  # flush_batch size inside copy_session


def row_bytes(row_id: int, floats: list[float]) -> bytes:
    # int16 num_fields=2
    out = struct.pack('!h', 2)
    # field 1: INT (4 bytes BE)
    out += struct.pack('!i', 4) + struct.pack('!i', row_id)
    # field 2: VECTOR (int32 BE dim + dim*LE float32)
    vec_data = struct.pack('!i', len(floats)) + struct.pack(f'<{len(floats)}f', *floats)
    out += struct.pack('!i', len(vec_data)) + vec_data
    return out


def main():
    random.seed(42)
    dsn = "CUBRID:localhost:33000:testdb:::"
    conn = CUBRIDdb.connect(dsn, "dba", "")
    conn.set_autocommit(False)
    cur = conn.cursor()

    try:
        cur.execute("DROP TABLE IF EXISTS t_copy_bench")
    except Exception:
        pass
    cur.execute(f"CREATE TABLE t_copy_bench (id INT, vec VECTOR({VEC_DIM}))")
    conn.commit()

    print(f"Generating {NUM_ROWS} rows × VECTOR({VEC_DIM})...")
    t_gen_start = time.time()
    # Pre-generate in chunks to avoid holding all payload in memory at once.
    chunks: list[bytes] = []
    buf = bytearray()
    for i in range(NUM_ROWS):
        floats = [random.random() * 2.0 - 1.0 for _ in range(VEC_DIM)]
        buf += row_bytes(i, floats)
        if (i + 1) % CHUNK_ROWS == 0:
            chunks.append(bytes(buf))
            buf = bytearray()
    if buf:
        chunks.append(bytes(buf))
    # Footer sentinel
    footer = struct.pack('!h', -1)
    t_gen = time.time() - t_gen_start
    total_bytes = sum(len(c) for c in chunks) + len(footer)
    print(f"  generated in {t_gen:.2f}s, total payload {total_bytes/1e6:.1f} MB")

    print("Executing COPY FROM STDIN...")
    cur.execute("COPY t_copy_bench FROM STDIN WITH (FORMAT BINARY)")

    t_send_start = time.time()
    for c in chunks:
        conn.connection.copy_send_data(c)
    conn.connection.copy_send_data(footer)
    rows_loaded = conn.connection.copy_end()
    t_send = time.time() - t_send_start
    print(f"Rows loaded: {rows_loaded} in {t_send:.3f}s "
          f"({rows_loaded/t_send:.0f} rows/s, {total_bytes/t_send/1e6:.1f} MB/s)")

    conn.commit()

    cur.execute("DROP TABLE t_copy_bench")
    conn.commit()

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
