"""
CUBRIDdb.copy — high-level buffered writer for COPY FROM STDIN (FORMAT BINARY).

Usage:

    # Low-level (caller builds bytes, driver chunks them to the wire):
    with conn.copy("COPY t FROM STDIN WITH (FORMAT BINARY)") as w:
        w.write(raw_bytes)
        w.write(more_raw_bytes)
    rows_loaded = w.rows_loaded

    # High-level (driver encodes Python tuples):
    with conn.copy("COPY t FROM STDIN WITH (FORMAT BINARY)",
                   types=["INT", "VECTOR"]) as w:
        for id_, vec in iter_rows:
            w.write_row((id_, vec))
    rows_loaded = w.rows_loaded
"""

import struct


DEFAULT_BUFFER_SIZE = 1 << 20   # 1 MiB per network flush


# ----- wire-format primitives ---------------------------------------------

_NULL_FIELD = struct.pack("!i", -1)
_FOOTER = struct.pack("!h", -1)


def _enc_null():
    return _NULL_FIELD


def _enc_int(v):
    return struct.pack("!ii", 4, int(v))


def _enc_bigint(v):
    return struct.pack("!i", 8) + struct.pack("!q", int(v))


def _enc_float(v):
    return struct.pack("!i", 4) + struct.pack("!f", float(v))


def _enc_double(v):
    return struct.pack("!i", 8) + struct.pack("!d", float(v))


def _enc_varchar(v):
    b = v.encode("utf-8") if isinstance(v, str) else bytes(v)
    return struct.pack("!i", len(b)) + b


def _enc_vector(v):
    # v is a sequence of floats
    body = struct.pack("!i", len(v))
    for x in v:
        body += struct.pack("!f", float(x))
    return struct.pack("!i", len(body)) + body


_ENCODERS = {
    "INT":       _enc_int,
    "INTEGER":   _enc_int,
    "BIGINT":    _enc_bigint,
    "FLOAT":     _enc_float,
    "REAL":      _enc_float,
    "DOUBLE":    _enc_double,
    "VARCHAR":   _enc_varchar,
    "STRING":    _enc_varchar,
    "CHAR":      _enc_varchar,
    "VECTOR":    _enc_vector,
}


def _encoder_for(type_name):
    key = type_name.upper().strip()
    # Strip "(n)" / "(n,m)" suffixes so "VARCHAR(64)" → "VARCHAR".
    paren = key.find("(")
    if paren != -1:
        key = key[:paren].rstrip()
    try:
        return _ENCODERS[key]
    except KeyError:
        raise ValueError(f"CopyWriter: unsupported column type {type_name!r}")


# ----- buffered writer ----------------------------------------------------

class CopyWriter:
    """Buffered writer over `cci_copy_send_data`. Auto-chunks to buffer_size
    bytes per network flush. Sends the footer on close.

    The writer runs `COPY ... FROM STDIN WITH (FORMAT BINARY)` on construction
    (via the given cursor) and leaves the connection in an in-progress COPY
    state until close() — you must close() or use it as a context manager."""

    def __init__(self, connection, stmt, types=None, buffer_size=DEFAULT_BUFFER_SIZE):
        self._conn = connection
        # Accumulator for partial data smaller than buffer_size. Pieces larger
        # than buffer_size are sliced straight from the caller's buffer with
        # memoryview (zero-copy) so large writes don't pay a staging cost.
        self._buf = bytearray()
        self._buffer_size = int(buffer_size)
        self._closed = False
        self._rows_loaded = None
        self._encoders = (
            [_encoder_for(t) for t in types] if types is not None else None
        )

        cur = connection.cursor()
        try:
            cur.execute(stmt)
        finally:
            cur.close()

    # context manager
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            # Still need to close the COPY state cleanly. Best effort.
            try:
                self.close()
            except Exception:
                pass
            return False
        self.close()
        return False

    @property
    def rows_loaded(self):
        """Number of rows loaded; available after close()."""
        return self._rows_loaded

    # --- writing -----------------------------------------------------------

    def write(self, data):
        """Append already-encoded bytes; flushes in buffer_size chunks.

        Fast path: when the accumulator is empty and `data` is bigger than
        `buffer_size`, we slice the caller's buffer with memoryview and send
        each slice directly — no staging copy. Small pieces (from write_row)
        still accumulate in `self._buf` until it reaches buffer_size."""
        if self._closed:
            raise ValueError("CopyWriter is closed")
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError("write() expects bytes-like object")

        bs = self._buffer_size
        n = len(data)
        if n == 0:
            return

        # Merge with any accumulator first so we keep chunk boundaries aligned.
        if self._buf:
            remaining = bs - len(self._buf)
            if n <= remaining:
                self._buf.extend(data)
                if len(self._buf) >= bs:
                    self._flush()
                return
            self._buf.extend(memoryview(data)[:remaining])
            self._flush()
            data = memoryview(data)[remaining:]
            n = len(data)

        # Stream full chunks directly out of the caller's buffer.
        if n >= bs:
            mv = data if isinstance(data, memoryview) else memoryview(data)
            send = self._conn.connection.copy_send_data
            i = 0
            while i + bs <= n:
                send(mv[i:i + bs])
                i += bs
            if i < n:
                self._buf.extend(mv[i:])
            return

        # Tail smaller than buffer_size — accumulate.
        self._buf.extend(data)

    def write_row(self, values):
        """Encode a tuple/list of Python values using the types= given at
        construction time. Requires types= to be set."""
        if self._encoders is None:
            raise ValueError(
                "write_row() requires types=[...] to be given to CopyWriter"
            )
        if len(values) != len(self._encoders):
            raise ValueError(
                f"row has {len(values)} values, expected {len(self._encoders)}"
            )
        row = bytearray(struct.pack("!h", len(values)))
        for v, enc in zip(values, self._encoders):
            row += _NULL_FIELD if v is None else enc(v)
        self.write(bytes(row))

    def write_rows(self, rows):
        """Write an iterable of tuples/lists. Convenience wrapper."""
        for r in rows:
            self.write_row(r)

    # --- lifecycle ---------------------------------------------------------

    def _flush(self):
        if self._buf:
            # bytearray supports the buffer protocol, so copy_send_data (y#)
            # reads it directly without an extra copy.
            self._conn.connection.copy_send_data(self._buf)
            self._buf.clear()

    def close(self):
        """Flush any buffered bytes, send the footer, call copy_end.
        Sets self.rows_loaded. Safe to call twice."""
        if self._closed:
            return self._rows_loaded
        self._closed = True
        try:
            self._buf.extend(_FOOTER)
            self._flush()
            self._rows_loaded = self._conn.connection.copy_end()
        except Exception:
            # Do NOT swallow the error — caller needs to see it. But mark closed
            # to prevent re-entry.
            self._rows_loaded = None
            raise
        return self._rows_loaded
