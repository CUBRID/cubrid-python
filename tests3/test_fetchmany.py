# pylint: disable=missing-function-docstring,missing-module-docstring
import random

import pytest

from conftest import BOOZE_SAMPLES

import CUBRIDdb


def test_fetchmany_error_no_query(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor

    # cursor.fetchmany should raise an Error if called without issuing a query
    with pytest.raises(CUBRIDdb.Error):
        cur.fetchmany(4)


def test_fetchmany_default_array_size(cubrid_db_cursor, populated_booze_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f'select name from {populated_booze_table}')
    r = cur.fetchmany() # should get 1 row
    assert len(r) == 1,\
        'cursor.fetchmany retrieved incorrect number of rows, '\
        'default of array is one.'


def _gen_random_n_numbers_with_given_sum(n, s):
    if n <= 0 or s < n:
        raise ValueError("Impossible to distribute S among N numbers "
            "with each number being at least 1")

    if n == 1:
        return [s]

    if s == n:
        return [1] * n

    # Ensure there's at least 1 for each number
    remaining_sum = s - n

    r = random.Random(0)

    # Generate N-1 random partition points within the remaining sum
    partitions = sorted(r.sample(range(1, remaining_sum + 1), n - 1))

    # Calculate numbers based on differences between partitions (plus the ends)
    numbers = [partitions[0]] + [partitions[i] - partitions[i-1]
        for i in range(1, n-1)] + [remaining_sum - partitions[-1]]

    # Add 1 back to each number to ensure the minimum value is 1
    numbers = [x + 1 for x in numbers]

    return numbers


@pytest.mark.parametrize("array_size", list(range(1, 11, 2)))
@pytest.mark.parametrize("fetch_count", list(range(1, 4)))
@pytest.mark.parametrize("attempted_row_count", [3, 6, 7, 9])
def test_fetchmany(cubrid_db_cursor, populated_booze_table,
                   array_size, fetch_count, attempted_row_count):
    cur, _ = cubrid_db_cursor

    if fetch_count > attempted_row_count:
        return

    cur.execute(f'select name from {populated_booze_table}')

    total_count = remaining_count = len(BOOZE_SAMPLES)
    row_count_list = _gen_random_n_numbers_with_given_sum(
        fetch_count, attempted_row_count)

    def check_fetch(max_count, expected_count):
        r = cur.fetchmany(max_count)
        assert len(r) == expected_count,\
            'cursor.fetchmany retrieved incorrect number of rows, '\
            f'expected {expected_count}, returned {len(r)}'

    cur.arraysize = array_size

    for row_count in row_count_list:
        expected_count = min(remaining_count, row_count)
        check_fetch(row_count, expected_count)
        remaining_count = max(remaining_count - row_count, 0)

    assert cur.rowcount in (-1, total_count)


def test_fetchmany_empty_table(cubrid_db_cursor, populated_booze_table,
                               barflys_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f'select name from {barflys_table}')
    r = cur.fetchmany()
    assert not r,\
            'cursor.fetchmany should return an empty sequence '\
            'if query retrieved no rows'
    assert cur.rowcount in (-1, 0)


def test_fetchmany_nosize(cubrid_db_cursor, fetchmany_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"select * from {fetchmany_table}")
    data = cur.fetchmany()
    assert len(data) == 1
    assert data == [(1, 21, 'myName-1')]


def test_fetchmany_negativeone(cubrid_db_cursor, fetchmany_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"select * from {fetchmany_table}")
    data = cur.fetchmany(-1)
    assert not data


def test_fetchmany_zero(cubrid_db_cursor, fetchmany_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"select * from {fetchmany_table}")
    data = cur.fetchmany(0)
    assert not data


def test_fetchmany_all(cubrid_db_cursor, fetchmany_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"select * from {fetchmany_table}")
    data = cur.fetchmany(cur.rowcount)
    assert len(data) == cur.rowcount


def test_fetchmany_overflow(cubrid_db_cursor, fetchmany_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"select * from {fetchmany_table}")
    data = cur.fetchmany(cur.rowcount + 10)
    assert len(data) == cur.rowcount
