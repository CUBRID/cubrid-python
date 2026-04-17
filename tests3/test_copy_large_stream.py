"""
Stress test: COPY FROM STDIN (FORMAT BINARY) with (INT, VECTOR(256)) rows.

Per-row size ≈ 1042 bytes (2 header + 8 int + 1032 vector).

Two modes:
  - "single":  all rows + footer in ONE copy_send_data call
  - "chunked": split into multiple copy_send_data calls, footer at end

Used to characterize the network/buffer ceiling of one message vs. streaming.
"""

import os
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import CUBRIDdb


DIM = 256


def row_bytes(i):
    """Encode one (INT, VECTOR(256)) tuple."""
    # header
    hdr = struct.pack("!h", 2)
    # INT
    int_f = struct.pack("!i", 4) + struct.pack("!i", i)
    # VECTOR(256)
    vec_body = struct.pack("!i", DIM)
    for k in range(DIM):
        vec_body += struct.pack("!f", (i + k) * 0.001)
    vec_f = struct.pack("!i", len(vec_body)) + vec_body
    return hdr + int_f + vec_f


def footer():
    return struct.pack("!h", -1)


def fmt_bytes(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def run_single(conn, cur, n_rows, table):
    cur.execute(f"DROP TABLE IF EXISTS {table}")
    cur.execute(f"CREATE TABLE {table} (id INT, vec VECTOR({DIM}))")
    conn.commit()

    print(f"  building payload: {n_rows} rows ...", flush=True)
    buf = bytearray()
    for i in range(n_rows):
        buf += row_bytes(i)
    buf += footer()
    size = len(buf)
    print(f"  payload size: {fmt_bytes(size)} in ONE copy_send_data call")

    t0 = time.perf_counter()
    cur.execute(f"COPY {table} FROM STDIN WITH (FORMAT BINARY)")
    conn.connection.copy_send_data(bytes(buf))
    loaded = conn.connection.copy_end()
    conn.commit()
    dt = time.perf_counter() - t0

    assert loaded == n_rows, f"expected {n_rows}, got {loaded}"
    mbs = size / dt / (1024 * 1024)
    print(f"  loaded {loaded} rows in {dt:.2f}s ({mbs:.1f} MB/s) — OK")
    return size, dt


def run_chunked(conn, cur, n_rows, rows_per_send, table):
    cur.execute(f"DROP TABLE IF EXISTS {table}")
    cur.execute(f"CREATE TABLE {table} (id INT, vec VECTOR({DIM}))")
    conn.commit()

    # Pre-encode for a cleaner timing
    chunks = []
    buf = bytearray()
    for i in range(n_rows):
        buf += row_bytes(i)
        if (i + 1) % rows_per_send == 0:
            chunks.append(bytes(buf))
            buf = bytearray()
    if buf:
        chunks.append(bytes(buf))
    chunks.append(footer())
    total = sum(len(c) for c in chunks)
    print(f"  chunked: {n_rows} rows → {len(chunks)} send_data calls, total {fmt_bytes(total)}")

    t0 = time.perf_counter()
    cur.execute(f"COPY {table} FROM STDIN WITH (FORMAT BINARY)")
    for c in chunks:
        conn.connection.copy_send_data(c)
    loaded = conn.connection.copy_end()
    conn.commit()
    dt = time.perf_counter() - t0

    assert loaded == n_rows, f"expected {n_rows}, got {loaded}"
    mbs = total / dt / (1024 * 1024)
    print(f"  loaded {loaded} rows in {dt:.2f}s ({mbs:.1f} MB/s) — OK")


def main():
    dsn = "CUBRID:localhost:33091:testdb:::"
    conn = CUBRIDdb.connect(dsn, "dba", "")
    conn.set_autocommit(False)
    cur = conn.cursor()

    try:
        # Single-shot scaling — find ceiling of one copy_send_data call
        for n in (1_000, 10_000, 50_000):
            print(f"\n[single] n={n}")
            try:
                run_single(conn, cur, n, "t_big_single")
            except Exception as e:
                print(f"  FAILED at n={n}: {type(e).__name__}: {e}")
                # rollback & reconnect so subsequent tests don't see a dead tx
                try:
                    conn.rollback()
                except Exception:
                    pass
                break

        # Chunked streaming — arbitrarily large totals are fine if chunks are safe
        print(f"\n[chunked] 100_000 rows, 1_000 rows/send")
        try:
            run_chunked(conn, cur, 100_000, 1_000, "t_big_chunked")
        except Exception as e:
            print(f"  FAILED: {type(e).__name__}: {e}")

        print("\nDone.")
    finally:
        for t in ("t_big_single", "t_big_chunked"):
            try:
                cur.execute(f"DROP TABLE IF EXISTS {t}")
                conn.commit()
            except Exception:
                pass
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
