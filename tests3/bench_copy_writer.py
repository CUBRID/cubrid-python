"""
Benchmark: CopyWriter (buffered, auto-chunked) vs raw copy_send_data.

Question: does the Python-side buffering layer add perceptible overhead on top
of raw pass-through?

Both paths produce the same bytes on the wire; only the Python glue differs.
"""

import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import CUBRIDdb


DIM = 256
N = 50_000  # ~52 MB of payload


def row_bytes(i):
    hdr = struct.pack("!h", 2)
    int_f = struct.pack("!i", 4) + struct.pack("!i", i)
    vec_body = struct.pack("!i", DIM)
    for k in range(DIM):
        vec_body += struct.pack("!f", (i + k) * 0.001)
    vec_f = struct.pack("!i", len(vec_body)) + vec_body
    return hdr + int_f + vec_f


def footer():
    return struct.pack("!h", -1)


def build_all_bytes(n):
    buf = bytearray()
    for i in range(n):
        buf += row_bytes(i)
    return bytes(buf)


def bench_raw_single(conn, cur, payload):
    """Baseline: one copy_send_data with everything."""
    cur.execute("DROP TABLE IF EXISTS t_bench")
    cur.execute(f"CREATE TABLE t_bench (id INT, vec VECTOR({DIM}))")
    conn.commit()

    t0 = time.perf_counter()
    cur.execute("COPY t_bench FROM STDIN WITH (FORMAT BINARY)")
    conn.connection.copy_send_data(payload + footer())
    loaded = conn.connection.copy_end()
    conn.commit()
    return time.perf_counter() - t0, loaded


def bench_raw_manual_chunks(conn, cur, payload, chunk):
    """Baseline: manual chunking, same size as CopyWriter default."""
    cur.execute("DROP TABLE IF EXISTS t_bench")
    cur.execute(f"CREATE TABLE t_bench (id INT, vec VECTOR({DIM}))")
    conn.commit()

    t0 = time.perf_counter()
    cur.execute("COPY t_bench FROM STDIN WITH (FORMAT BINARY)")
    for i in range(0, len(payload), chunk):
        conn.connection.copy_send_data(payload[i:i + chunk])
    conn.connection.copy_send_data(footer())
    loaded = conn.connection.copy_end()
    conn.commit()
    return time.perf_counter() - t0, loaded


def bench_copywriter_bytes(conn, cur, payload, buffer_size):
    """CopyWriter with pre-encoded bytes via .write()."""
    cur.execute("DROP TABLE IF EXISTS t_bench")
    cur.execute(f"CREATE TABLE t_bench (id INT, vec VECTOR({DIM}))")
    conn.commit()

    t0 = time.perf_counter()
    with conn.copy(
        f"COPY t_bench FROM STDIN WITH (FORMAT BINARY)",
        buffer_size=buffer_size,
    ) as w:
        # Feed in same-sized slices as raw_manual_chunks for fair compare
        # but CopyWriter does its own chunking internally.
        w.write(payload)
    conn.commit()
    return time.perf_counter() - t0, w.rows_loaded


def bench_copywriter_rows(conn, cur, n, buffer_size):
    """CopyWriter with .write_row() — also pays the Python-side encoding cost."""
    cur.execute("DROP TABLE IF EXISTS t_bench")
    cur.execute(f"CREATE TABLE t_bench (id INT, vec VECTOR({DIM}))")
    conn.commit()

    t0 = time.perf_counter()
    with conn.copy(
        f"COPY t_bench FROM STDIN WITH (FORMAT BINARY)",
        types=["INT", "VECTOR"],
        buffer_size=buffer_size,
    ) as w:
        for i in range(n):
            w.write_row((i, [(i + k) * 0.001 for k in range(DIM)]))
    conn.commit()
    return time.perf_counter() - t0, w.rows_loaded


def fmt(dt, size, loaded):
    mbs = size / dt / (1024 * 1024)
    krows = loaded / dt / 1000
    return f"{dt:.3f}s  {mbs:6.1f} MB/s  {krows:6.1f} k rows/s"


def main():
    conn = CUBRIDdb.connect("CUBRID:localhost:33091:testdb:::", "dba", "")
    conn.set_autocommit(False)
    cur = conn.cursor()

    try:
        print(f"pre-building {N} rows of (INT, VECTOR({DIM}))...")
        payload = build_all_bytes(N)
        size = len(payload) + len(footer())
        print(f"payload: {size / (1024*1024):.1f} MB\n")

        # Warmup
        bench_raw_single(conn, cur, payload)

        # Run each 3 times, take best
        def best(f, *args):
            return min(f(*args) for _ in range(3))

        dt, loaded = best(bench_raw_single, conn, cur, payload)
        print(f"[raw   single ]  {fmt(dt, size, loaded)}")

        dt, loaded = best(bench_raw_manual_chunks, conn, cur, payload, 1 << 20)
        print(f"[raw   1MB chk]  {fmt(dt, size, loaded)}")

        dt, loaded = best(bench_copywriter_bytes, conn, cur, payload, 1 << 20)
        print(f"[CopyW bytes  ]  {fmt(dt, size, loaded)}")

        dt, loaded = best(bench_copywriter_rows, conn, cur, N, 1 << 20)
        print(f"[CopyW rows   ]  {fmt(dt, size, loaded)}  (includes py-encoding)")

    finally:
        try:
            cur.execute("DROP TABLE IF EXISTS t_bench")
            conn.commit()
        except Exception:
            pass
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
