# pylint: disable=missing-function-docstring,missing-module-docstring
import datetime

from decimal import Decimal

from conftest import TABLE_PREFIX


def _test_binding(cur, columns_sql, samples):
    table_name = f'{TABLE_PREFIX}bindings'
    cur.execute(f'drop table if exists {table_name}')
    try:
        cur.execute(f"create table if not exists {table_name} ({columns_sql})")
        cur.executemany(f"insert into {table_name} values (?)",
                        [(sample,) for sample in samples])
        assert cur.rowcount == 1

        cur.execute(f"select * from {table_name}")
        return [r[0] for r in cur.fetchall()]
    finally:
        cur.execute(f'drop table if exists {table_name}')


def test_bind_int(cubrid_db_cursor):
    numbers = [100, 200, 300, 400]
    inserted = _test_binding(cubrid_db_cursor[0], 'x int', numbers)
    assert inserted == numbers


def test_bind_bigint(cubrid_db_cursor):
    numbers_bigint = [-9223372036854775808, +9223372036854775807, 567890987654321012]
    inserted = _test_binding(cubrid_db_cursor[0], 'x bigint', numbers_bigint)
    assert inserted == numbers_bigint


def test_bind_float(cubrid_db_cursor):
    numbers = [1.234, 3.14, -10.441875, 5.]
    inserted = _test_binding(cubrid_db_cursor[0], 'x float', numbers)
    assert inserted == numbers


def test_bind_numeric(cubrid_db_cursor):
    numbers = [Decimal('14.1021'), Decimal('-1.10'), Decimal('0.0015501')]
    numbers_int = [14, -1, 0]
    inserted = _test_binding(cubrid_db_cursor[0], 'x numeric', numbers)
    assert inserted == numbers_int


def test_bind_str(cubrid_db_cursor):
    samples = [
        'Carlton Cold', 'Carlton Draft', 'Mountain Goat',
        'Redback', 'Victoria Bitter', 'XXXX'
    ]
    inserted = _test_binding(cubrid_db_cursor[0], 'name varchar(20)', samples)
    assert inserted == samples


def test_bind_date(cubrid_db_cursor):
    dates = ["1987-10-29", "1989-07-14", "2024-02-29"]
    date_objects = [datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                    for date_str in dates]

    inserted = _test_binding(cubrid_db_cursor[0], 'xdate date', dates)
    assert inserted == date_objects

    inserted = _test_binding(cubrid_db_cursor[0], 'xdate date', date_objects)
    assert inserted == date_objects


def test_bind_time(cubrid_db_cursor):
    times = ["11:30:29", "10:00:00", "23:59:59", "05:30:01"]
    time_objects = [datetime.datetime.strptime(time_str, "%H:%M:%S").time()
                    for time_str in times]

    inserted = _test_binding(cubrid_db_cursor[0], 'xtime time', times)
    assert inserted == time_objects

    inserted = _test_binding(cubrid_db_cursor[0], 'xtime time', time_objects)
    assert inserted == time_objects


def test_bind_timestamp(cubrid_db_cursor):
    times = ["2011-5-3 11:30:29", "2024-2-6 14:01:20"]
    ts_objects = [datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    for time_str in times]

    inserted = _test_binding(cubrid_db_cursor[0], 'xts timestamp', times)
    assert inserted == ts_objects

    inserted = _test_binding(cubrid_db_cursor[0], 'xts timestamp', ts_objects)
    assert inserted == ts_objects


def test_bind_binary(cubrid_db_cursor):
    samples_bin = ['0100', '01010101010101', '111111111', '1111100000010101010110111111']

    # Function to convert a binary string to bytes
    def binary_str_to_bytes(binary_str):
        # Convert to integer
        integer_representation = int(binary_str, 2)

        # Convert integer to bytes
        # Calculate the length of the bytes object needed
        bytes_length = (len(binary_str) + 7) // 8  # Round up division
        return integer_representation.to_bytes(bytes_length, 'big')

    samples_bytes = [binary_str_to_bytes(b) for b in samples_bin]

    inserted = _test_binding(cubrid_db_cursor[0], 'xbit BIT VARYING(256)', samples_bytes)
    assert inserted == samples_bytes
