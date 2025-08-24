"""
This module contains a collection of tests for the extended _cubrid Python module, which provides
a Pythonic interface to the CUBRID database. These tests aim to ensure that the extended
functionalities of the _cubrid module, including advanced database operations and custom
extensions, work as expected and adhere to the Python DB API 2.0 specification where applicable.

Tests cover a range of operations including, but not limited to, connection management, cursor
operations, transaction handling, schema manipulation, and data retrieval and manipulation. The
tests utilize pytest fixtures for setup and teardown, ensuring a clean state for each test and
facilitating the testing of database interactions in isolation.

Specifically, the tests include:
- Connection and cursor creation and management
- Transaction begin, commit, and rollback
- Executing SQL statements with parameter binding
- Schema creation, modification, and deletion
- Data insertion, updating, selection, and deletion
- Specialized database operations unique to the _cubrid module

The test suite is designed for maintainability and ease of extension, allowing for straightforward
addition of new tests as the _cubrid module evolves.

Prerequisites:
- A running CUBRID database server
- The _cubrid Python module installed and configured to connect to the database server
- pytest and pytest-cov for running the tests and generating coverage reports

Usage:
Run the tests using pytest from the command line. For example:
`pytest test_cubrid.py`
To generate a coverage report, add the `--cov=_cubrid` option.
"""
# pylint: disable=missing-function-docstring

import datetime
import os
import re

import pytest

import _cubrid


@pytest.fixture
def db_names_table(cubrid_cursor):
    cursor, connection = cubrid_cursor

    # Create the test table using the cursor
    cursor.prepare("create table if not exists test_cubrid (name varchar(20))")
    cursor.execute()

    yield cursor, connection  # Yield both cursor and connection to the test

    # Cleanup: drop the test table using the cursor
    cursor.prepare("drop table if exists test_cubrid")
    cursor.execute()


def _create_table(cursor, columns_sql, samples, bind_type = None):
    # Create the test table using the cursor
    cursor.prepare(f"create table if not exists test_cubrid ({columns_sql})")
    cursor.execute()

    if not samples:
        return

    # Insert sample data
    placeholders = ','.join(['(?)'] * len(samples))
    insert_query = f"insert into test_cubrid values {placeholders}"
    cursor.prepare(insert_query)
    for i, sample in enumerate(samples, start=1):
        if bind_type is None:
            cursor.bind_param(i, sample)
        else:
            cursor.bind_param(i, sample, bind_type)
    cursor.execute()


def _cleanup_table(cursor):
    # Cleanup: drop the test table using the cursor
    cursor.prepare("drop table if exists test_cubrid")
    cursor.execute()


@pytest.fixture
def db_sample_names_table(cubrid_cursor):
    cursor, connection = cubrid_cursor

    names = [
        'Carlton Cold', 'Carlton Draft', 'Mountain Goat',
        'Redback', 'Victoria Bitter', 'XXXX'
    ]

    _create_table(cursor, 'name varchar(20)', names)

    yield cursor, connection

    _cleanup_table(cursor)


@pytest.fixture
def db_collection_table(cubrid_cursor):
    cursor, connection = cubrid_cursor

    _create_table(cursor, 'a set of int, b multiset of int , c list of int', [])

    yield cursor, connection

    _cleanup_table(cursor)


@pytest.fixture
def db_int_table(cubrid_cursor):
    cursor, connection = cubrid_cursor

    _create_table(cursor, 'id integer auto_increment, val integer', [])

    cursor.prepare('insert into test_cubrid (val) values (?)')
    for i in range(0, 10):
        cursor.bind_param(1, str(i))
        cursor.execute()

    yield cursor, connection

    _cleanup_table(cursor)


def test_cubrid_connection(cubrid_connection):
    assert cubrid_connection is not None, "Connection to CUBRID failed"


def test_server_version(cubrid_connection):
    # Assuming server_version() returns a version string from the database connection
    version = cubrid_connection.server_version()
    assert version is not None, "The server version should not be None"

    # Verify the version format (major.minor.patch.build)
    version_pattern = r'^\d+\.\d+\.\d+\.\d+$'
    assert re.match(version_pattern, version), \
        f"Version '{version}' does not match the expected format 'major.minor.patch.build'"


def test_client_version(cubrid_connection):
    # Assuming client_version() returns a version string or object from the database connection
    version = cubrid_connection.client_version()
    assert version is not None, "The client version should not be None"

    # Define a pattern to match the Python driver version format: major.minor.patch.build
    # This matches the format defined in version.h (e.g., "11.2.1.0062")
    version_pattern = r'^\d+\.\d+\.\d+\.\d+$'

    # Use re.match to check if the version matches the expected pattern
    assert re.match(version_pattern, version), f"Version '{version}' does not match the "\
        f"expected Python driver version format 'major.minor.patch.build'"


def test_db_api_exceptions_hierarchy():
    # Base exceptions
    assert hasattr(_cubrid, 'Error'), "'Error' exception is missing"

    # Subclasses of Error
    for exc in ['InterfaceError', 'DatabaseError']:
        assert hasattr(_cubrid, exc), f"'{exc}' exception is missing"
        assert issubclass(getattr(_cubrid, exc), _cubrid.Error), \
            f"'{exc}' does not subclass 'Error'"

    # Subclasses of DatabaseError
    for exc in ['DataError', 'OperationalError', 'IntegrityError', 'InternalError',
                'ProgrammingError', 'NotSupportedError']:
        assert hasattr(_cubrid, exc), f"'{exc}' exception is missing"
        assert issubclass(getattr(_cubrid, exc), _cubrid.DatabaseError), \
            f"'{exc}' does not subclass 'DatabaseError'"


def test_commit(cubrid_connection):
    # The commit operation is tested to ensure it can be called without raising an exception.
    cubrid_connection.commit()


def test_rollback(cubrid_connection):
    # Test to ensure the rollback operation can be called without raising an exception.
    cubrid_connection.rollback()


def test_cursor(cubrid_cursor):
    # Since the cubrid_cursor fixture handles cursor creation, this test implicitly verifies
    # that a cursor can be successfully obtained and closed without errors.
    # Additional operations or assertions to test the cursor's functionality can be added here.
    pass


def _fetchall(cursor, fetch_type = 0):
    results = []
    row = cursor.fetch_row(fetch_type)
    while row:
        results.append(row)
        row = cursor.fetch_row(fetch_type)
    return results


def test_cursor_no_charset(cubrid_connection):
    cur = cubrid_connection.cursor()
    try:
        cur.prepare('drop table if exists test_cubrid')
        cur.execute()
        cur.prepare('create table if not exists test_cubrid (name varchar(20))')
        cur.execute()
        cur.prepare("insert into test_cubrid values ('Blair'), ('Țărână'), ('흙')")
        cur.execute()
        cur.prepare('select * from test_cubrid')
        cur.execute()
        results = _fetchall(cur)
        assert results == [('Blair',), ('Țărână',), ('흙',)]
    finally:
        cur.prepare('drop table if exists test_cubrid')
        cur.execute()
        cur.close()


def test_cursor_isolation(cubrid_connection):
    # Ensure cursors are closed after the test
    cur1 = cur2 = None
    try:
        # Cursors created from the same connection should have the same transaction isolation level
        cur1 = cubrid_connection.cursor()
        cur2 = cubrid_connection.cursor()

        cur1.prepare('drop table if exists test_cubrid')
        cur1.execute()

        # Perform operations with cur1
        cur1.prepare('create table if not exists test_cubrid (name varchar(20))')
        cur1.execute()
        cur1.prepare("insert into test_cubrid values ('Blair')")
        cur1.execute()
        assert cur1.rowcount == 1, "Affected rows should be 1 after insert"

        # Perform operations with cur2
        cur2.prepare('select * from test_cubrid')
        cur2.execute()
        results = _fetchall(cur2)
        assert len(results) == 1, "Number of rows should be 1"
    finally:
        # Clean up: close cursors and clean the test data
        if cur1:
            cur1.prepare('drop table if exists test_cubrid')
            cur1.execute()
            cur1.close()
        if cur2:
            cur2.close()


def test_description(db_names_table):
    cur, _ = db_names_table  # Provided by the db_names_table fixture

    # Test cursor's description attribute after creating a table
    assert cur.description is None, (
        "cursor.description should be None after executing a statement that "
        "can return no rows (such as create)"
    )

    # Test the cursor's description after selecting from the table
    cur.prepare("select name from test_cubrid")
    cur.execute()
    assert cur.description is not None, "cursor.description should not be None after select"
    assert len(cur.description) == 1, "cursor.description describes too many columns"
    assert len(cur.description[0]) == 7, "cursor.description tuple should have 7 elements"
    assert cur.description[0][0].lower() == 'name', "cursor.description[x][0] "\
        "must return column name"


def test_rowcount(db_names_table):
    cur, _ = db_names_table  # Provided by the db_names_table fixture

    # Testing rowcount after a no-result statement (table creation)
    assert cur.rowcount == -1, (
        "cursor.rowcount should be -1 after executing "
        "no-result statements"
    )

    # Testing rowcount after an insert statement
    cur.prepare("insert into test_cubrid values ('Blair')")
    cur.execute()
    assert cur.rowcount in (-1, 1), (
        "cursor.rowcount should equal the number of rows inserted, or "
        "be set to -1 after executing an insert statement"
    )

    # Testing rowcount after a select statement
    cur.prepare("select name from test_cubrid")
    cur.execute()
    # Assuming the cursor's rowcount reflects the number of rows after execute
    assert cur.rowcount in (-1, 1), (
        "cursor.rowcount should equal the number of rows that can be fetched, or "
        "be set to -1 after executing a select statement"
    )


def test_isolation_level(cubrid_connection):
    # Set the isolation level using the connection object provided by the fixture
    cubrid_connection.set_isolation_level(_cubrid.CUBRID_REP_CLASS_COMMIT_INSTANCE)

    # Assert that the isolation level is set correctly
    assert cubrid_connection.isolation_level == 'CUBRID_REP_CLASS_COMMIT_INSTANCE', (
        "connection.set_isolation_level does not work"
    )


def test_autocommit(cubrid_connection):
    # Check the default state of autocommit
    assert cubrid_connection.autocommit is True, "connection.autocommit default is True"

    # Enable autocommit and verify
    cubrid_connection.set_autocommit(True)
    assert cubrid_connection.autocommit is True, "connection.autocommit should be TRUE after set on"

    # Disable autocommit and verify
    cubrid_connection.set_autocommit(False)
    assert cubrid_connection.autocommit is False, \
        "connection.autocommit should be FALSE after set off"


def test_ping_connected(cubrid_connection):
    # Test ping when the connection is active
    assert cubrid_connection.ping() == 1, "connection.ping should return 1 when connected"


def test_schema_info(cubrid_connection):
    # Assuming CUBRID_SCH_TABLE is a constant defined in the _cubrid module or similar
    schema_info = cubrid_connection.schema_info(_cubrid.CUBRID_SCH_TABLE, "db_class")

    # Verify the schema information received is as expected
    assert schema_info[0] == 'db_class', (
        "connection.schema_info got incorrect result for table name"
    )
    assert schema_info[1] == 0, (
        "connection.schema_info got incorrect result for table info"
    )


def test_insert_id(cubrid_cursor):
    cur, con = cubrid_cursor  # Provided by the cubrid_cursor fixture

    # Create a table with an auto_increment column
    t_insert_id = '''
    create table if not exists test_cubrid (
        id numeric auto_increment(1000000000000, 2),
        name varchar(20)
    )
    '''
    cur.prepare(t_insert_id)
    cur.execute()

    # Insert a row into the table
    cur.prepare("insert into test_cubrid(name) values ('Blair')")
    cur.execute()

    # Retrieve the last insert ID
    insert_id = con.insert_id()  # Assuming insert_id is available on the connection object
    assert insert_id == 1000000000000, "connection.insert_id() got incorrect result"

    # Cleanup: drop the table to clean up the database
    cur.prepare("drop table test_cubrid")
    cur.execute()


def test_affected_rows(db_sample_names_table):
    cur, _ = db_sample_names_table

    # Verify affected rows after insert
    assert cur.affected_rows() in (-1, 6), "Affected rows should be 6"

    # Verify num_fields and num_rows without select statement
    assert cur.num_fields() is None, "cursor.num_fields() should be None "\
        "when not execute select statement"
    assert cur.num_rows() is None, "cursor.num_rows() should be None "\
        "when not execute select statement"


def test_data_seek(db_sample_names_table):
    cur, _ = db_sample_names_table

    # Select data to setup cursor for data_seek tests
    cur.prepare("select * from test_cubrid")
    cur.execute()

    # Verify num_fields and rowcount
    assert cur.num_fields() == 1, "cursor.num_fields() get incorrect result"
    assert cur.num_rows() == cur.rowcount, "cursor.num_rows() get incorrect result"

    # Test data_seek
    cur.data_seek(3)
    assert cur.row_tell() == 3, "cursor.data_seek get incorrect cursor"


def test_row_seek(db_sample_names_table):
    cur, _ = db_sample_names_table

    # Prepare and execute select to setup cursor for row_seek tests
    cur.prepare("select * from test_cubrid")
    cur.execute()

    # Set cursor position and test row_seek
    cur.data_seek(3)
    cur.row_seek(-2)
    assert cur.row_tell() == 1, "cursor.row_seek return incorrect cursor"

    cur.row_seek(4)
    assert cur.row_tell() == 5, "cursor.row_seek move forward error"


def _test_bind(cursor, columns_sql, samples, bind_type = None):
    n_samples = len(samples)
    try:
        # Create table and insert samples
        _create_table(cursor, columns_sql, samples, bind_type)
        assert cursor.affected_rows() in (-1, n_samples)

        # Get the rows and verify they match the samples
        cursor.prepare("select * from test_cubrid")
        cursor.execute()
        inserted = []
        row = cursor.fetch_row()
        while row:
            inserted.append(row[0])
            row = cursor.fetch_row()
        return inserted
    finally:
        _cleanup_table(cursor)


def test_bind_int(cubrid_cursor):
    cursor, _ = cubrid_cursor
    numbers = ['100', '200', '300', '400']
    numbers_int = [100, 200, 300, 400]
    inserted = _test_bind(cursor, 'id int', numbers)
    assert inserted == numbers_int
    inserted = _test_bind(cursor, 'id int', numbers)
    assert inserted == numbers_int


def test_bind_bigint(cubrid_cursor):
    cursor, _ = cubrid_cursor
    numbers_bigint = ['-9223372036854775808', '9223372036854775807', '567890987654321012']
    bt_bigint = 21
    inserted = _test_bind(cursor, 'id bigint', numbers_bigint, bt_bigint)
    str_inserted = [str(x) for x in inserted]
    assert str_inserted == numbers_bigint


def test_bind_float(cubrid_cursor):
    cursor, _ = cubrid_cursor
    numbers = ['3.14']
    numbers_float = [3.14]
    inserted = _test_bind(cursor, 'id float', numbers)
    assert inserted == numbers_float
    inserted = _test_bind(cursor, 'id float', numbers)
    assert inserted == numbers_float


def test_bind_date_e(cubrid_cursor):
    cursor, _ = cubrid_cursor

    dates = ["2011-2-31"]
    try:
        with pytest.raises(_cubrid.DatabaseError):
            _create_table(cursor, 'birthday date', dates)
    finally:
        _cleanup_table(cursor)


def test_bind_date(cubrid_cursor):
    cursor, _ = cubrid_cursor
    dates = ["1987-10-29"]
    dates_dt = [datetime.datetime.strptime(x, "%Y-%m-%d").date() for x in dates]
    inserted = _test_bind(cursor, 'birthday date', dates)
    assert inserted == dates_dt
    inserted = _test_bind(cursor, 'birthday date', dates)
    assert inserted == dates_dt


def test_bind_time(cubrid_cursor):
    cursor, _ = cubrid_cursor
    times = ["11:30:29"]
    times_dt = [datetime.datetime.strptime(x, "%H:%M:%S").time() for x in times]
    inserted = _test_bind(cursor, 'lunch time', times)
    assert inserted == times_dt
    inserted = _test_bind(cursor, 'lunch time', times)
    assert inserted == times_dt


def test_bind_datetime(cubrid_cursor):
    cursor, _ = cubrid_cursor
    times = ["1987-10-29 11:30:29"]
    times_dt = [datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in times]
    inserted = _test_bind(cursor, 'xdt datetime', times)
    assert inserted == times_dt
    inserted = _test_bind(cursor, 'xdt datetime', times)
    assert inserted == times_dt


def test_bind_timestamp(cubrid_cursor):
    cursor, _ = cubrid_cursor
    times = ["2011-5-3 11:30:29"]
    times_dt = [datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in times]
    inserted = _test_bind(cursor, 'lunch timestamp', times)
    assert inserted == times_dt
    inserted = _test_bind(cursor, 'lunch timestamp', times)
    assert inserted == times_dt


def test_bind_datetime_now(cubrid_cursor):
    cursor, _ = cubrid_cursor
    now = datetime.datetime.now()
    formatted_now = now.strftime("%Y-%m-%d %H:%M:%S.%f")
    inserted = _test_bind(cursor, 'now datetime', [formatted_now])
    formatted_ins = inserted[0].strftime("%Y-%m-%d %H:%M:%S.%f")
    assert formatted_now[:-3] == formatted_ins[:-3]
    inserted = _test_bind(cursor, 'now datetime', [formatted_now])
    formatted_ins = inserted[0].strftime("%Y-%m-%d %H:%M:%S.%f")
    assert formatted_now[:-3] == formatted_ins[:-3]


def test_row_to_tuple(cubrid_cursor, db_int_table):
    cur, _ = cubrid_cursor

    cur.prepare("select * from test_cubrid")
    cur.execute()

    rows = _fetchall(cur)
    assert rows == [(1, 0), (2, 1), (3, 2), (4, 3), (5, 4),
                    (6, 5), (7, 6), (8, 7), (9, 8), (10, 9)]


def test_row_to_dict(cubrid_cursor, db_int_table):
    cur, _ = cubrid_cursor

    cur.prepare("select * from test_cubrid")
    cur.execute()

    rows = _fetchall(cur, 1)
    assert rows == [{'id': 1, 'val': 0}, {'id': 2, 'val': 1}, {'id': 3, 'val': 2},
                    {'id': 4, 'val': 3}, {'id': 5, 'val': 4}, {'id': 6, 'val': 5},
                    {'id': 7, 'val': 6}, {'id': 8, 'val': 7}, {'id': 9, 'val': 8},
                    {'id': 10, 'val': 9}]


def test_collection(cubrid_cursor, db_collection_table):
    cur, _ = cubrid_cursor

    cur.prepare("insert into test_cubrid "
        "values( {},{},{}),(null,null,null),( {1,1},{1,1},{1,1}),"
        "({1,2,3},{1,2,3},{1,2,3}),( {-1,-2,-3},{-1,-2,-3},{-1,-2,-3})")
    cur.execute()
    cur.prepare("select * from test_cubrid where a seteq {'1'} order by 1,2")
    cur.execute()

    rows = _fetchall(cur)
    assert rows == [(['1'], ['1', '1'], ['1', '1'])]


def test_collection_2(cubrid_cursor, db_collection_table):
    cur, _ = cubrid_cursor

    cur.prepare("insert into test_cubrid "
        "values({},{},{}),(null,null,null),( {1,1},{1,1},{1,1})")
    cur.execute()
    cur.prepare("select * from test_cubrid where a seteq {'1'} order by 1,2")
    cur.execute()

    rows = _fetchall(cur)
    assert rows == [(['1'], ['1', '1'], ['1', '1'])]


def _are_files_identical(file1_path, file2_path, chunk_size=4096):
    with open(file1_path, 'rb') as file1, open(file2_path, 'rb') as file2:
        while True:
            file1_chunk = file1.read(chunk_size)
            file2_chunk = file2.read(chunk_size)

            if file1_chunk != file2_chunk:
                return False

            if not file1_chunk:
                return True


def test_lob_file(cubrid_cursor):
    cur, con = cubrid_cursor

    base_dir = os.path.dirname(__file__)
    fp1 = os.path.join(base_dir, 'cubrid_logo.png')
    fp2 = os.path.join(base_dir, 'lob_out.png')

    try:
        cur.prepare('drop table if exists test_cubrid')
        cur.execute()

        cur.prepare('create table test_cubrid (picture blob)')
        cur.execute()

        cur.prepare('insert into test_cubrid values (?)')
        lob = con.lob()
        lob.imports(fp1)
        cur.bind_lob(1, lob)
        cur.execute()
        lob.close()

        cur.prepare('select * from test_cubrid')
        cur.execute()
        lob_fetch = con.lob()
        cur.fetch_lob(1, lob_fetch)
        lob_fetch.export(fp2)
        lob_fetch.close()

        assert _are_files_identical(fp1, fp2)
    finally:
        _cleanup_table(cur)

        if os.path.exists(fp2):
            os.remove(fp2)


def test_lob_string(cubrid_cursor):
    cur, con = cubrid_cursor

    try:
        cur.prepare('create table test_cubrid (content clob)')
        cur.execute()

        cur.prepare('insert into test_cubrid values (?)')
        lob = con.lob()
        lob.write('hello world', 'C')
        cur.bind_lob(1, lob)
        cur.execute()
        lob.close()

        cur.prepare('select * from test_cubrid')
        cur.execute()
        lob_fetch = con.lob()
        cur.fetch_lob(1, lob_fetch)
        assert lob_fetch.read() == 'hello world', 'lob.read() get incorrect result'
        assert lob_fetch.seek(0, _cubrid.SEEK_SET) == 0
        lob_fetch.close()
    finally:
        _cleanup_table(cur)


def test_result_info(cubrid_cursor):
    cur, _ = cubrid_cursor

    try:
        cur.prepare('create table test_cubrid (id int primary key, name varchar(20))')
        cur.execute()

        cur.prepare("insert into test_cubrid values (?,?)")
        cur.bind_param(1, '1000')
        cur.prepare('select * from test_cubrid')
        cur.execute()
        info = cur.result_info()

        assert len(info) == 2, 'the length of cursor.result_info must be 2'
        assert info[0][10] == 1, 'the first colnum of cursor.result should be primary key'

        info = cur.result_info(1)
        assert len(info) == 1, 'the length of cursor.result_info must be 1'
        assert info[0][4] == 'id', 'cursor.result has just one colname and the name is "name"'
    finally:
        _cleanup_table(cur)
