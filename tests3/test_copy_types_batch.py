"""
End-to-end test: COPY FROM STDIN (FORMAT BINARY) — broad type coverage +
batching confirmation (many tuples in a single copy_send_data call).

Requires a running CUBRID server with a database named 'testdb'.
"""

import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import CUBRIDdb


# --- binary encoders for supported types ---

NULL_LEN = struct.pack("!i", -1)


def enc_null():
    return NULL_LEN


def enc_int(v):
    return struct.pack("!i", 4) + struct.pack("!i", v)


def enc_bigint(v):
    return struct.pack("!i", 8) + struct.pack("!q", v)


def enc_float(v):
    return struct.pack("!i", 4) + struct.pack("!f", v)


def enc_double(v):
    return struct.pack("!i", 8) + struct.pack("!d", v)


def enc_varchar(s):
    b = s.encode("utf-8")
    return struct.pack("!i", len(b)) + b


def enc_vector(xs):
    body = struct.pack("!i", len(xs))
    for x in xs:
        body += struct.pack("!f", x)
    return struct.pack("!i", len(body)) + body


def row_header(num_fields):
    return struct.pack("!h", num_fields)


def footer():
    return struct.pack("!h", -1)


def run(cur, conn, stmt, rows_bytes):
    """Execute COPY, send rows_bytes+footer in one send_data (one round-trip), end."""
    cur.execute(stmt)
    conn.connection.copy_send_data(rows_bytes + footer())
    return conn.connection.copy_end()


def test_all_types_one_row(conn, cur):
    print("[types] create t_types ...")
    cur.execute("DROP TABLE IF EXISTS t_types")
    cur.execute(
        "CREATE TABLE t_types ("
        "i INT, bi BIGINT, f FLOAT, d DOUBLE, "
        "s VARCHAR(64), v VECTOR(3), n INT"
        ")"
    )
    conn.commit()

    # One row with each supported type + a NULL in the last column
    payload = (
        row_header(7)
        + enc_int(42)
        + enc_bigint(9_000_000_000)
        + enc_float(1.5)
        + enc_double(2.71828)
        + enc_varchar("hello COPY")
        + enc_vector([0.25, -0.5, 1.125])
        + enc_null()
    )

    loaded = run(cur, conn, "COPY t_types FROM STDIN WITH (FORMAT BINARY)", payload)
    conn.commit()
    assert loaded == 1, f"expected 1 row loaded, got {loaded}"

    cur.execute("SELECT i, bi, f, d, s, CAST(v AS STRING), n FROM t_types")
    row = cur.fetchone()
    print(f"  got: {row}")
    assert row[0] == 42
    assert row[1] == 9_000_000_000
    assert abs(row[2] - 1.5) < 1e-5
    assert abs(row[3] - 2.71828) < 1e-9
    assert row[4] == "hello COPY"
    parsed = [float(x) for x in row[5].strip("[]").split(",")]
    assert len(parsed) == 3 and abs(parsed[0] - 0.25) < 1e-5
    assert row[6] is None
    print("[types] OK")


def test_batch_many_tuples(conn, cur):
    print("[batch] create t_batch ...")
    cur.execute("DROP TABLE IF EXISTS t_batch")
    cur.execute("CREATE TABLE t_batch (id INT, vec VECTOR(4))")
    conn.commit()

    N = 500
    buf = bytearray()
    for i in range(N):
        buf += row_header(2)
        buf += enc_int(i)
        buf += enc_vector([float(i), float(i) + 0.5, -float(i), 0.0])

    # Single copy_send_data call carrying 500 tuples → one round-trip
    loaded = run(cur, conn, "COPY t_batch FROM STDIN WITH (FORMAT BINARY)", bytes(buf))
    conn.commit()
    assert loaded == N, f"expected {N} rows loaded, got {loaded}"

    cur.execute("SELECT COUNT(*) FROM t_batch")
    n = cur.fetchone()[0]
    assert n == N, f"SELECT COUNT(*) got {n}"

    cur.execute("SELECT id, CAST(vec AS STRING) FROM t_batch ORDER BY id LIMIT 3")
    for i, (got_id, vec_str) in enumerate(cur.fetchall()):
        assert got_id == i
        floats = [float(x) for x in vec_str.strip("[]").split(",")]
        assert abs(floats[0] - i) < 1e-5
        assert abs(floats[1] - (i + 0.5)) < 1e-5
        print(f"  row {i}: id={got_id}, vec={vec_str}")
    print(f"[batch] {N} tuples in one send_data — OK")


def main():
    dsn = "CUBRID:localhost:33091:testdb:::"
    conn = CUBRIDdb.connect(dsn, "dba", "")
    conn.set_autocommit(False)
    cur = conn.cursor()

    try:
        test_all_types_one_row(conn, cur)
        test_batch_many_tuples(conn, cur)
        print("\nAll COPY type + batch tests passed!")
    finally:
        try:
            cur.execute("DROP TABLE IF EXISTS t_types")
            cur.execute("DROP TABLE IF EXISTS t_batch")
            conn.commit()
        except Exception:
            pass
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
