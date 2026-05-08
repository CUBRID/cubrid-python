"""
End-to-end test: COPY FROM STDIN (FORMAT BINARY) with VECTOR type.

Requires a running CUBRID server with a database named 'testdb'.

Usage:
  python test_copy_vector.py
"""

import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _cubrid
import CUBRIDdb


def build_binary_copy_payload(rows):
    """
    Build a COPY binary payload for table (id INT, vec VECTOR(3)).

    Each row is (int_val, [float, float, float]).
    Wire format per row:
      int16  num_fields
      For each field:
        int32  field_len  (-1 for NULL)
        bytes  field_data
    Footer: int16 -1
    """
    buf = bytearray()

    for int_val, floats in rows:
        num_fields = 2
        buf += struct.pack('!h', num_fields)

        # Field 1: INT (4 bytes, network byte order)
        buf += struct.pack('!i', 4)
        buf += struct.pack('!i', int_val)

        # Field 2: VECTOR (int32 dim + dim * float32)
        dim = len(floats)
        vec_data = struct.pack('!i', dim)
        for f in floats:
            vec_data += struct.pack('!f', f)
        buf += struct.pack('!i', len(vec_data))
        buf += vec_data

    # Footer sentinel
    buf += struct.pack('!h', -1)

    return bytes(buf)


def main():
    dsn = "CUBRID:localhost:33091:testdb:::"
    user = "dba"
    passwd = ""

    print("Connecting to CUBRID...")
    conn = CUBRIDdb.connect(dsn, user, passwd)
    conn.set_autocommit(False)
    cur = conn.cursor()

    # Setup: create table
    print("Creating table...")
    try:
        cur.execute("DROP TABLE IF EXISTS t_copy_vec")
    except Exception:
        pass
    cur.execute("CREATE TABLE t_copy_vec (id INT, vec VECTOR(3))")
    conn.commit()

    # Execute COPY statement
    print("Executing COPY FROM STDIN...")
    cur.execute("COPY t_copy_vec FROM STDIN WITH (FORMAT BINARY)")

    # Build binary payload with 3 rows
    rows = [
        (1, [1.0, 2.5, -3.75]),
        (2, [0.0, 0.0, 0.0]),
        (3, [1.5, -2.25, 3.125]),
    ]
    payload = build_binary_copy_payload(rows)

    print(f"Sending {len(payload)} bytes of binary data...")
    conn.connection.copy_send_data(payload)

    print("Ending COPY...")
    result = conn.connection.copy_end()
    print(f"Rows loaded: {result}")

    conn.commit()

    # Verify INT column via Python driver (VECTOR fetch not yet supported by _cubrid)
    print("Verifying INT column via Python driver...")
    cur.execute("SELECT id FROM t_copy_vec ORDER BY id")
    fetched = cur.fetchall()

    assert len(fetched) == 3, f"Expected 3 rows, got {len(fetched)}"
    for i, (expected_id, _) in enumerate(rows):
        row = fetched[i]
        assert row[0] == expected_id, f"Row {i+1} id: expected {expected_id}, got {row[0]}"
        print(f"  Row {i+1}: id={row[0]}")

    # Verify VECTOR column via CAST to STRING (Python _cubrid can't fetch VECTOR directly)
    print("Verifying VECTOR column via CAST to STRING...")
    cur.execute("SELECT id, CAST(vec AS STRING) FROM t_copy_vec ORDER BY id")
    fetched = cur.fetchall()
    for i, (expected_id, expected_vec) in enumerate(rows):
        row = fetched[i]
        vec_str = row[1]
        print(f"  Row {i+1}: id={row[0]}, vec={vec_str}")
        assert vec_str is not None, f"Row {i+1} vec is None"
        # Parse the stringified vector like "[1, 2.5, -3.75]" and compare as floats
        parsed = [float(x) for x in vec_str.strip("[]").split(",")]
        assert len(parsed) == len(expected_vec), \
            f"Row {i+1}: expected {len(expected_vec)} dims, got {len(parsed)}"
        for j, (got, want) in enumerate(zip(parsed, expected_vec)):
            assert abs(got - want) < 1e-5, \
                f"Row {i+1} dim {j}: expected {want}, got {got}"

    # Cleanup
    cur.execute("DROP TABLE t_copy_vec")
    conn.commit()

    cur.close()
    conn.close()

    print("\nAll COPY VECTOR tests passed!")


if __name__ == "__main__":
    main()
