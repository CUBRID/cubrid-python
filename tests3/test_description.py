# pylint: disable=missing-function-docstring,missing-module-docstring

from conftest import TABLE_PREFIX

import CUBRIDdb


def test_description(cubrid_db_cursor, booze_table):
    cur, _ = cubrid_db_cursor

    assert cur.description is None, \
        'cursor.descripton should be none after executing a'\
        'statement that can return no rows (such as DDL)'

    cur.execute(f'select name from {booze_table}')
    nc = len(cur.description)
    assert nc == 1, f'cursor.description describes {nc} columns'

    assert len(cur.description[0]) == 7, 'cursor.description[x] tuples must have 7 elements'
    assert cur.description[0][0].lower() == 'name',\
        'cursor.description[x][0] must return column name'
    assert cur.description[0][1] == CUBRIDdb.STRING,\
        f'cursor.description[x][1] must return column type. Got {cur.description[0][1]:r}'

    table_name = f'{TABLE_PREFIX}barflys'
    try:
        # Make sure self.description gets reset
        cur.execute(f'create table {table_name} (name varchar(20))')
        assert cur.description is None,\
            'cursor.description not being set to None when executing '\
            'no-result statments (eg. DDL)'
    finally:
        cur.execute(f'drop table if exists {table_name}')


def _test_description(cubrid_db_cursor, description_table, expected):
    cur, _ = cubrid_db_cursor
    column_name = expected[0]
    cur.execute(f"SELECT {column_name} from {description_table}")
    assert cur.description[0] == expected


def test_description_int(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_int', 8, 0, 0, 10, 0, 1))


def test_description_short(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_short', 9, 0, 0, 5, 0, 1))


def test_description_numeric(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_numeric', 7, 0, 0, 15, 0, 1))


def test_description_float(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_float', 11, 0, 0, 7, 0, 1))


def test_description_double(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_double', 12, 0, 0, 15, 0, 1))


def test_description_monetary(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_monetary', 10, 0, 0, 15, 0, 1))


def test_description_date(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_date', 13, 0, 0, 10, 0, 1))


def test_description_time(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_time', 14, 0, 0, 8, 0, 1))


def test_description_datetime(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_datetime', 22, 0, 0, 23, 3, 1))


def test_description_timestamp(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_timestamp', 15, 0, 0, 19, 0, 1))


def test_description_bit(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_bit', 5, 0, 0, 8, 0, 1))


def test_description_varbit(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_varbit', 6, 0, 0, 8, 0, 1))


def test_description_char(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_char', 1, 0, 0, 4, 0, 1))


def test_description_varchar(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_varchar', 2, 0, 0, 4, 0, 1))


def test_description_string(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_string', 2, 0, 0, 1073741823, 0, 1))


def test_description_set(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_set', 32, 0, 0, 0, 0, 1))


def test_description_multiset(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_multiset', 64, 0, 0, 0, 0, 1))


def test_description_sequence(cubrid_db_cursor, desc_table):
    _test_description(cubrid_db_cursor, desc_table, ('c_sequence', 96, 0, 0, 0, 0, 1))
