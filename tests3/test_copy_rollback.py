"""
Correctness scenarios for COPY FROM STDIN (FORMAT BINARY) with (INT, VECTOR(256)),
exercising the skip_inner_sysop path in file_alloc.

Notes on semantics (important):
  - COPY FROM STDIN uses the BU_LOCK bulk-insert path. With bulk logging in
    effect, inserted rows are NOT rolled back by a transaction ROLLBACK — same
    property as other databases' bulk-load fast paths. Tests therefore assert
    commit-visibility only, and do not assume rollback undoes the rows.
  - The outer atomic sysop in copy_session::flush_batch guarantees file-header
    consistency on crash recovery; that property is verified separately via
    the FI_TEST_FILE_PERM_EXPAND_AFTER_COMMIT fault injection (manual test),
    not here.

Scenarios:
  1. Small batch (commit): <1 heap page.
  2. Large batch (commit): thousands of rows, forces many file_alloc calls and
     at least one file_perm_expand, exercising skip_inner_sysop + atomic outer.
  3. Successive COPY in the same transaction: each batch must remain visible
     after its own commit and to subsequent SELECTs in the same session.
"""

import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import CUBRIDdb


DIM = 256
SMALL_ROWS = 5
LARGE_ROWS = 10_000
TABLE = "t_copy_skip_sysop"


def _row_bytes(i):
    hdr = struct.pack("!h", 2)
    int_f = struct.pack("!i", 4) + struct.pack("!i", i)
    vec_body = (struct.pack("!i", DIM)
                + struct.pack(f"<{DIM}f", *((i + k) * 0.001 for k in range(DIM))))
    vec_f = struct.pack("!i", len(vec_body)) + vec_body
    return hdr + int_f + vec_f


def _build_payload(start, n):
    buf = bytearray()
    for i in range(start, start + n):
        buf += _row_bytes(i)
    buf += struct.pack("!h", -1)
    return bytes(buf)


def _run_copy(conn, cur, payload):
    cur.execute(f"COPY {TABLE} FROM STDIN WITH (FORMAT BINARY)")
    conn.connection.copy_send_data(payload)
    return conn.connection.copy_end()


def _count(cur):
    cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
    return cur.fetchone()[0]


def _min_max(cur):
    cur.execute(f"SELECT MIN(id), MAX(id) FROM {TABLE}")
    return cur.fetchone()


def main():
    dsn = "CUBRID:localhost:33000:testdb:::"
    conn = CUBRIDdb.connect(dsn, "dba", "")
    conn.set_autocommit(False)
    cur = conn.cursor()

    try:
        cur.execute(f"DROP TABLE IF EXISTS {TABLE}")
        cur.execute(f"CREATE TABLE {TABLE} (id INT, vec VECTOR({DIM}))")
        conn.commit()

        # --- Scenario 1: small batch (commit) ---
        print(f"[1/3] small batch: COPY {SMALL_ROWS} rows + commit")
        loaded = _run_copy(conn, cur, _build_payload(0, SMALL_ROWS))
        assert loaded == SMALL_ROWS, f"loaded {loaded}, expected {SMALL_ROWS}"
        conn.commit()
        n = _count(cur)
        assert n == SMALL_ROWS, f"count after small commit: got {n}"
        lo, hi = _min_max(cur)
        assert (lo, hi) == (0, SMALL_ROWS - 1), f"id range: got ({lo},{hi})"
        conn.commit()

        # Clear for the next scenario (DDL flushes bulk-inserted rows cleanly).
        cur.execute(f"DROP TABLE {TABLE}")
        cur.execute(f"CREATE TABLE {TABLE} (id INT, vec VECTOR({DIM}))")
        conn.commit()

        # --- Scenario 2: large batch (commit) — exercises file_perm_expand ---
        print(f"[2/3] large batch: COPY {LARGE_ROWS} rows + commit")
        loaded = _run_copy(conn, cur, _build_payload(0, LARGE_ROWS))
        assert loaded == LARGE_ROWS, f"loaded {loaded}, expected {LARGE_ROWS}"
        conn.commit()
        n = _count(cur)
        assert n == LARGE_ROWS, f"count after large commit: got {n}"
        lo, hi = _min_max(cur)
        assert (lo, hi) == (0, LARGE_ROWS - 1), f"id range: got ({lo},{hi})"
        conn.commit()

        cur.execute(f"DROP TABLE {TABLE}")
        cur.execute(f"CREATE TABLE {TABLE} (id INT, vec VECTOR({DIM}))")
        conn.commit()

        # --- Scenario 3: two successive COPY batches in one session ---
        print(f"[3/3] successive batches: 2 × COPY {SMALL_ROWS} rows")
        loaded = _run_copy(conn, cur, _build_payload(0, SMALL_ROWS))
        assert loaded == SMALL_ROWS, f"first batch loaded {loaded}"
        conn.commit()
        loaded = _run_copy(conn, cur, _build_payload(SMALL_ROWS, SMALL_ROWS))
        assert loaded == SMALL_ROWS, f"second batch loaded {loaded}"
        conn.commit()
        n = _count(cur)
        assert n == 2 * SMALL_ROWS, f"count after two batches: got {n}"
        lo, hi = _min_max(cur)
        assert (lo, hi) == (0, 2 * SMALL_ROWS - 1), f"id range: got ({lo},{hi})"
        conn.commit()

        print("\nAll COPY skip_inner_sysop scenarios passed.")
    finally:
        try:
            cur.execute(f"DROP TABLE IF EXISTS {TABLE}")
            conn.commit()
        except Exception:
            pass
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
