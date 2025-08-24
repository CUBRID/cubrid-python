# pylint: disable=missing-function-docstring,missing-module-docstring
import datetime
import decimal

import pytest

from conftest import (
    BOOZE_SAMPLES,
    TABLE_PREFIX,
)

import CUBRIDdb


@pytest.mark.xfail(reason="CCI does not return error when fetchall cannot return rows")
def test_fetchall_error_no_rows(cubrid_db_cursor, booze_table):
    cur, _ = cubrid_db_cursor

    # cursor.fetchall should raise an Error if called without
    # executing a query that may return rows (such as a select)
    # like the create table query performed by booze_table
    with pytest.raises(CUBRIDdb.Error):
        cur.fetchall()

    # or the insert query
    cur.execute(f"insert into {booze_table} values ('Victoria Bitter')")
    with pytest.raises(CUBRIDdb.Error):
        cur.fetchall()


def test_fetchall_error_no_query(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor

    # cursor.fetchall should raise an Error if called without issuing a query
    with pytest.raises(CUBRIDdb.Error):
        cur.fetchall()


def test_fetchall(cubrid_db_cursor, populated_booze_table):
    cur, _ = cubrid_db_cursor

    row_count = len(BOOZE_SAMPLES)

    cur.execute(f'select name from {populated_booze_table}')
    rows = cur.fetchall()

    assert cur.rowcount in (-1, row_count)
    assert len(rows) == row_count, 'cursor.fetchall did not retrieve all rows'

    rows = [r[0] for r in rows]
    rows.sort()
    assert rows == BOOZE_SAMPLES, 'cursor.fetchall retrieved incorrect rows'

    rows = cur.fetchall()
    assert not rows,\
        'cursor.fetchall should return an empty list if called '\
        'after the whole result set has been fetched'
    assert cur.rowcount in (-1, row_count)


def test_fetchall_empty_table(cubrid_db_cursor, populated_booze_table,
                               barflys_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f'select name from {barflys_table}')
    rows = cur.fetchall()

    assert cur.rowcount in (-1, 0)
    assert not rows,\
            'cursor.fetchall should return an empty list '\
            'if a select query returns no rows'


def _test_fetchall_datatype(cur, columns_sql, rows, expected_rows = None):
    table_name = f'{TABLE_PREFIX}fetchall'
    placeholders = ','.join(['?'] * len(rows[0]))
    cur.execute(f'drop table if exists {table_name}')
    try:
        cur.execute(f"create table if not exists {table_name} ({columns_sql})")
        cur.executemany(f"insert into {table_name} values ({placeholders})", rows)
        assert cur.rowcount == 1

        cur.execute(f"select * from {table_name}")
        fetched_rows = cur.fetchall()
        expected_rows = expected_rows or rows
        assert fetched_rows == expected_rows
    finally:
        cur.execute(f'drop table if exists {table_name}')


def test_fetchall_int(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(x,) for x in [1,0,-1,2147483647,-2147483648]]
    _test_fetchall_datatype(cur, 'c_int int', rows)


def test_fetchall_short(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(x,) for x in [1,0,-1,32767,-32768]]
    _test_fetchall_datatype(cur, 'c_int short', rows)


def test_fetchall_numeric(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(decimal.Decimal(x),) for x in ['12345.6789','0.12345678','-0.123456789']]
    expected_rows = [(decimal.Decimal(x),) for x in ['12345.6789','0.1235','-0.1235']]
    _test_fetchall_datatype(cur, 'c_num numeric(10,4)', rows, expected_rows)


def test_fetchall_float(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(x,) for x in [1.1,0.0,-1.1]]
    _test_fetchall_datatype(cur, 'c_float float', rows)


def test_fetchall_double(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(x,) for x in [1.1,0.0,-1.1]]
    _test_fetchall_datatype(cur, 'c_double double', rows)


def test_fetchall_char(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(x,) for x in ['a','abcd','zzz']]
    expected_rows = [(x,) for x in ['a   ','abcd','zzz ']]
    _test_fetchall_datatype(cur, 'c_char char(4)', rows, expected_rows)


def test_fetchall_varchar(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(x,) for x in ['a','abcd','abc']]
    _test_fetchall_datatype(cur, 'c_varchar varchar(4)', rows)


def test_fetchall_string(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(x,) for x in ['a','abcd','abcdefgh']]
    _test_fetchall_datatype(cur, 'c_string string', rows)


def test_fetchall_date(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(x,) for x in [datetime.date.min, datetime.date.today(), datetime.date.max]]
    _test_fetchall_datatype(cur, 'c_date date', rows)


def test_fetchall_time(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(t,) for t in [datetime.time.min, datetime.time.max]]
    expected_rows = [(datetime.time(t.hour, t.minute, t.second),)
                     for t in [datetime.time.min, datetime.time.max]]
    _test_fetchall_datatype(cur, 'c_time time', rows, expected_rows)


def test_fetchall_datetime(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(t,) for t in [datetime.datetime.now(), datetime.datetime.max]]
    expected_rows = [(datetime.datetime(t.year, t.month, t.day,
        t.hour, t.minute, t.second, t.microsecond // 1000 * 1000),)
        for t in [datetime.datetime.now(), datetime.datetime.max]]
    _test_fetchall_datatype(cur, 'c_datetime datetime', rows, expected_rows)


def test_fetchall_bit(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(x,) for x in [b'\xde\xad', b'\xbe\xaf', b'\x55']]
    expected_rows = [(x,) for x in [b'\xde\xad', b'\xbe\xaf', b'\x55\x00']]
    _test_fetchall_datatype(cur, 'c_bit bit(16)', rows, expected_rows)


def test_fetchall_varbit(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [(x,) for x in [b'\xde\xad\xbe\xef', b'\xbe\xaf', b'\x55']]
    _test_fetchall_datatype(cur, 'c_varbit bit varying', rows)


def test_fetchall_multiple_columns(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    rows = [
        (1400, 0.987654321, "ana has apples", datetime.date.today()),
        (1500, 1.987654321, "bonny has oranges", datetime.date.today()),
        (1600, 2.987654321, "chris has bananas", datetime.date.today()),
        (2000, 3.987654321, "dora has pies", datetime.date.today()),
    ]
    _test_fetchall_datatype(cur, 'c_int int, c_double double, c_varchar varchar, c_date date', rows)
