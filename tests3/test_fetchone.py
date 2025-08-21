# pylint: disable=missing-function-docstring,missing-module-docstring

import pytest

from conftest import BOOZE_SAMPLES

import CUBRIDdb


def test_fetchone_error_before_select(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor

    # cursor.fetchone should raise an Error if called before
    # executing a select-type query
    with pytest.raises(CUBRIDdb.Error):
        cur.fetchone()


@pytest.mark.xfail(reason="CCI does not return error when fetchone cannot return rows")
def test_fetchone_error_no_rows(cubrid_db_cursor, booze_table):
    cur, _ = cubrid_db_cursor

    # cursor.fetchone should raise an Error if called after
    # executing a query that cannnot return rows
    # like the create table query performed by booze_table
    with pytest.raises(CUBRIDdb.Error):
        cur.fetchone()

    # or the insert query
    cur.execute(f"insert into {booze_table} values ('Victoria Bitter')")
    with pytest.raises(CUBRIDdb.Error):
        cur.fetchone()


def test_fetchone_return_none_no_rows(cubrid_db_cursor, booze_table):
    cur, _ = cubrid_db_cursor
    cur.execute(f'select name from {booze_table}')
    assert cur.fetchone() is None,\
        'cursor.fetchone should return None if a query retrieves no rows'
    assert cur.rowcount in (-1, 0)


def test_fetchone(cubrid_db_cursor, booze_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"insert into {booze_table} values ('Victoria Bitter')")
    cur.execute(f"select name from {booze_table}")
    r = cur.fetchone()
    assert len(r) == 1, 'cursor.fetchone should have retrieved a single column'

    assert r[0] == 'Victoria Bitter', 'cursor.fetchone retrieved incorrect data'

    assert cur.fetchone() is None,\
        'cursor.fetchone should return None if no more rows available'
    assert cur.rowcount in (-1, 1)


def test_fetchone_multi(cubrid_db_cursor, populated_booze_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"select name from {populated_booze_table}")
    r = cur.fetchone()
    l = [r[0]]
    while r is not None:
        r = cur.fetchone()
        if r is None:
            break
        assert len(r) == 1, 'cursor.fetchone should have retrieved a single column'
        l.append(r[0])

    assert l == BOOZE_SAMPLES
