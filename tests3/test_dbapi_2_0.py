"""
This module tests DB API 2.0 compliance for the CUBRID database interface, using pytest for setup
and teardown of test environments. It includes fixtures for database table management and covers
a range of DB API 2.0 features like connection and cursor operations, transaction control, and
data integrity.

Goals:
- Ensure predictable interaction with CUBRID via DB API 2.0 standards.
- Facilitate a consistent programming experience for Python developers.

Fixtures:
- booze_table: Prepares a database table for testing, then cleans up afterwards.

Notes:
- Assumes a running CUBRID database instance is available.

Usage:
- Execute with pytest to run all module tests.
- Verify CUBRID connection details are set correctly.
"""
# pylint: disable=missing-function-docstring

import datetime
import decimal
import time

import pytest

from conftest import (
    BOOZE_SAMPLES,
    TABLE_PREFIX,
)

import CUBRIDdb


def test_connect(cubrid_db_connection):
    assert cubrid_db_connection is not None, "Connection to cubrid_db failed"


def test_connect_empty_dsn():
    with pytest.raises(CUBRIDdb.InterfaceError):
        CUBRIDdb.connect(dsn = "")


def test_connect_no_dsn():
    with pytest.raises(CUBRIDdb.InterfaceError):
        CUBRIDdb.connect()


def test_apilevel():
    # Must exist
    assert hasattr(CUBRIDdb, 'apilevel'), "Driver doesn't define apilevel"

    # Must be a valid value
    apilevel = CUBRIDdb.apilevel
    assert apilevel == '2.0', f"Expected apilevel to be '2.0', got {apilevel}"


def test_paramstyle():
    # Must exist
    assert hasattr(CUBRIDdb, 'paramstyle'), "Driver doesn't define paramstyle"

    # Must be a valid value
    paramstyle = CUBRIDdb.paramstyle
    valid_styles = ('qmark', 'numeric', 'format', 'pyformat')
    assert paramstyle in valid_styles, \
        f"paramstyle must be one of {valid_styles}, got {paramstyle}"


def test_db_api_exceptions_hierarchy():
    # Base exceptions
    assert hasattr(CUBRIDdb, 'Error'), "'Error' exception is missing"

    # Subclasses of Error
    for exc in ['InterfaceError', 'DatabaseError']:
        assert hasattr(CUBRIDdb, exc), f"'{exc}' exception is missing"
        assert issubclass(getattr(CUBRIDdb, exc), CUBRIDdb.Error), \
            f"'{exc}' does not subclass 'Error'"

    # Subclasses of DatabaseError
    for exc in ['DataError', 'OperationalError', 'IntegrityError', 'InternalError',
                'ProgrammingError', 'NotSupportedError']:
        assert hasattr(CUBRIDdb, exc), f"'{exc}' exception is missing"
        assert issubclass(getattr(CUBRIDdb, exc), CUBRIDdb.DatabaseError), \
            f"'{exc}' does not subclass 'DatabaseError'"


def test_escape_string(cubrid_db_connection):
    con = cubrid_db_connection

    # Test for empty string
    assert con.escape_string('') == ''

    # Test for single quotes (which should be escaped)
    assert con.escape_string("O'Reilly") == "O''Reilly"

    # Test for escaping SQL percent sign and underscore
    assert con.escape_string("100% sure") == "100% sure"
    assert con.escape_string("an_underscore") == "an_underscore"

    # Test for non-ASCII characters (Unicode)
    assert con.escape_string("Unicode test: èéêëēėę") == "Unicode test: èéêëēėę"

    # Test for numeric values (which should not be altered)
    assert con.escape_string("123456") == "123456"

    # Test for SQL keywords to ensure they're not altered
    assert con.escape_string("SELECT * FROM users") == "SELECT * FROM users"


def test_invalid_sql_insert_raises_dberror(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    table_name = f'{TABLE_PREFIX}booze'
    try:
        with pytest.raises(CUBRIDdb.DatabaseError):
            cur.execute(f"insert into {TABLE_PREFIX}booze values error_sql ('Hello')")
    finally:
        cur.execute(f'drop table if exists {table_name}')


def test_invalid_sql_insert_raises_error(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    table_name = f'{TABLE_PREFIX}booze'
    try:
        with pytest.raises(CUBRIDdb.Error):
            cur.execute(f"insert into {TABLE_PREFIX}booze values ('Hello', 'hello2')")
    finally:
        cur.execute(f'drop table if exists {table_name}')


def test_commit(cubrid_db_connection):
    # The commit operation is tested to ensure it can be called without raising an exception.
    cubrid_db_connection.commit()


def test_rollback(cubrid_db_connection):
    # Test to ensure the rollback operation can be called without raising an exception.
    cubrid_db_connection.rollback()


def test_cursor(cubrid_db_cursor):
    # Since the cubrid_db_cursor fixture handles cursor creation, this test implicitly verifies
    # that a cursor can be successfully obtained and closed without errors.
    # Additional operations or assertions to test the cursor's functionality can be added here.
    pass


def test_cursor_isolation(cubrid_db_connection):
    con = cubrid_db_connection
    table_name = f'{TABLE_PREFIX}booze'

    try:
        # Make sure cursors created from the same connection have
        # the documented transaction isolation level
        cur1 = con.cursor()
        cur2 = con.cursor()

        cur1.execute(f'create table {table_name} (name varchar(20))')
        cur1.execute(f"insert into {table_name} values ('Victoria Bitter')")
        cur2.execute(f"select name from {table_name}")
        booze = cur2.fetchall()

        assert len(booze) == 1, "Expected to fetch one row"
        assert len(booze[0]) == 1, "Expected row to have one column"
        assert booze[0][0] == 'Victoria Bitter', "Expected to find 'Victoria Bitter'"
    finally:
        # Clean up: close cursors and clean the test data
        if cur1:
            cur1.execute(f'drop table if exists {table_name}')
            cur1.close()
        if cur2:
            cur2.close()


def test_rowcount(cubrid_db_cursor, booze_table):
    cur, _ = cubrid_db_cursor

    assert cur.rowcount == -1, \
        'cursor.rowcount should be -1 after executing no-result statements'

    cur.execute(f"insert into {booze_table} value ('Victoria Bitter')")
    assert cur.rowcount in (-1, 1),\
        'cursor.rowcount should == number or rows inserted, or '\
        'set to -1 after executing an insert statment'

    cur.execute(f'select name from {booze_table}')
    assert cur.rowcount in (-1, 1),\
        'cursor.rowcount should == number or rows inserted, or '\
        'set to -1 after executing an insert statment'

    table_name = f'{TABLE_PREFIX}barflys'
    try:
        # Make sure self.description gets reset
        cur.execute(f'create table {table_name} (name varchar(20))')
        assert cur.rowcount == -1, \
            'cursor.rowcount should be -1 after executing no-result statements'
    finally:
        cur.execute(f'drop table if exists {table_name}')


def test_close(cubrid_db_connection):
    con = cubrid_db_connection
    cur = con.cursor()
    con.close()

    table_name = f'{TABLE_PREFIX}booze'
    with pytest.raises(CUBRIDdb.InterfaceError):
        cur.execute(f'create table {table_name} (name varchar(20))')

    with pytest.raises(CUBRIDdb.InterfaceError):
        con.commit()


def test_insert_utf8(cubrid_db_cursor, barflys_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"insert into {barflys_table} (name) values (?)", ['Tom',])
    assert rc == 1
    rc = cur.execute(f"insert into {barflys_table} (name) values (?)", [b'Jenny',])
    assert rc == 1
    rc = cur.execute(f"insert into {barflys_table} (name) values (?)", ['小王',])
    assert rc == 1


def test_executemany(cubrid_db_cursor, booze_table):
    cur, _ = cubrid_db_cursor

    largs = [("Cooper's",), ("Boag's",)]
    cur.executemany(f'insert into {booze_table} values (?)', largs)

    cur.execute(f'select name from {booze_table}')
    res = cur.fetchall()
    assert len(res) == 2, 'cursor.fetchall returned incorrect number of rows'
    beers = [res[0][0], res[1][0]]
    assert beers == [a[0] for a in largs], \
        'cursor.fetchall retrieved incorrect data, or data inserted incorrectly'


def test_autocommit(cubrid_db_cursor, booze_table):
    cur, con = cubrid_db_cursor

    assert con.get_autocommit() is True, "autocommit must be on by default"

    con.set_autocommit(False)
    assert con.get_autocommit() is False, "autocommit must be set to off"

    cur.execute(f"insert into {booze_table} values ('Hello')")
    con.rollback()
    cur.execute(f"select * from {booze_table}")
    rows = cur.fetchall()

    # No rows affected
    assert len(rows) == 0

    con.set_autocommit(True)
    assert con.get_autocommit() is True, "autocommit must be set to on"

    cur.execute(f"insert into {booze_table} values ('Hello')")
    cur.execute(f"select * from {booze_table}")
    rows = cur.fetchall()

    # One row affected
    assert len(rows) == 1


def test_datatype(cubrid_db_cursor, datatype_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"insert into {datatype_table} values "
        "(2012, 2012.345, 20.12345, time'11:21:30 am',"
        "date'2012-10-26', datetime'2012-10-26 11:21:30 am',"
        "timestamp'11:21:30 am 2012-10-26',"
        "B'101100111', 'TESTSTR', {'a', 'b', 'c'},"
        "{'c', 'c', 'c', 'b', 'b', 'a'},"
        '\'{"a": 1, "b": 2}\''
        ")"
    )

    cur.execute(f"select * from {datatype_table}")
    row = cur.fetchone()

    datatypes = [int, float, decimal.Decimal, datetime.time,
        datetime.date, datetime.datetime, datetime.datetime,
        bytes, str, set, list, str,
    ]

    for i, t in enumerate(datatypes):
        assert isinstance(row[i], t),\
            f'incorrect data type converted from CUBRID to Python (index {i} - {t})'
        if issubclass(t, set) or issubclass(t, list):
            assert isinstance(row[i].pop(), str) # see python_cubrid.c
            # _cubrid_CursorObject_dbset_to_pyvalue returns str for all elements


def test_mixdfetch(cubrid_db_cursor, populated_booze_table):
    cur, _ = cubrid_db_cursor

    row_count = len(BOOZE_SAMPLES)

    cur.execute(f'select name from {populated_booze_table}')
    row1 = cur.fetchone()
    rows23 = cur.fetchmany(2)
    row4 = cur.fetchone()
    rows_last = cur.fetchall()
    assert cur.rowcount in (-1, row_count)
    assert len(rows23)== 2, 'fetchmany returned incorrect number of rows'
    assert len(rows_last) == max(row_count - 4, 0),\
            'fetchall returned incorrect number of rows'

    rows = [row1] + rows23 + [row4] + rows_last
    rows = [r[0] for r in rows]
    rows.sort()
    assert rows == BOOZE_SAMPLES, 'incorrect data retrieved or inserted'


def test_threadsafety():
    assert hasattr(CUBRIDdb, 'threadsafety')
    threadsafety = CUBRIDdb.threadsafety
    assert threadsafety in (0,1,2,3)


def test_binary():
    CUBRIDdb.Binary([0x10, 0x20, 0x30])


def test_date():
    CUBRIDdb.Date(2011,3,17)
    CUBRIDdb.DateFromTicks(time.mktime((2011,3,17,0,0,0,0,0,0)))


def test_time():
    CUBRIDdb.Time(10, 30, 45)
    CUBRIDdb.TimeFromTicks(time.mktime((2011,3,17,17,13,30,0,0,0)))


def test_timestamp():
    CUBRIDdb.Timestamp(2002,12,25,13,45,30)
    CUBRIDdb.TimestampFromTicks(time.mktime((2002,12,25,13,45,30,0,0,0)))


def test_attr_string():
    assert hasattr(CUBRIDdb, 'STRING'), 'module.STRING must be defined'


def test_attr_binary():
    assert hasattr(CUBRIDdb, 'BINARY'), 'module.BINARY must be defined'


def test_attr_number():
    assert hasattr(CUBRIDdb, 'NUMBER'), 'module.NUMBER must be defined'


def test_attr_datetime():
    assert hasattr(CUBRIDdb, 'DATETIME'), 'module.DATETIME must be defined'


def test_attr_rowid():
    assert hasattr(CUBRIDdb, 'ROWID'), 'module.ROWID must be defined'
