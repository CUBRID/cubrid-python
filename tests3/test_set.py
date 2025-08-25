# pylint: disable=missing-function-docstring,missing-module-docstring
from conftest import TABLE_PREFIX


def _test_set_prepare(cur, columns_sql, samples, sample_size):
    table_name = f'{TABLE_PREFIX}set_prepare'
    cur.execute(f'drop table if exists {table_name}')
    try:
        placeholders = ",".join(["?"] * sample_size)
        cur.execute(f"create table if not exists {table_name} ({columns_sql})")
        cur.executemany(f"insert into {table_name} values ({placeholders})", samples)
        assert cur.rowcount == 1

        cur.execute(f"select * from {table_name}")
        return cur.fetchall()
    finally:
        cur.execute(f'drop table if exists {table_name}')


def test_set_prepare_int(cubrid_db_cursor):
    samples = [((1, 2, 3, 4), (5, 6, 7))]
    inserted = _test_set_prepare(cubrid_db_cursor[0],
        'col_1 set(int), col_2 set(int)', samples, 2)
    assert inserted == [({'1', '2', '3', '4'}, {'5', '6', '7'})]


def test_set_prepare_char_int(cubrid_db_cursor):
    samples = [(('a','b','c','d'), (5, 6, 7))]
    inserted = _test_set_prepare(cubrid_db_cursor[0],
        'col_1 set(char), col_2 set(int)', samples, 2)
    assert inserted == [({'a', 'b', 'c', 'd'}, {'5', '6', '7'})]


def test_set_prepare_char(cubrid_db_cursor):
    samples = [(('a','b','c','d'),)]
    inserted = _test_set_prepare(cubrid_db_cursor[0], 'col_1 set(CHAR)', samples, 1)
    assert inserted == [({'a', 'b', 'c', 'd'},)]


def test_set_prepare_string(cubrid_db_cursor):
    samples = [(('abc','bcd','ceee','dddddd'),)]
    inserted = _test_set_prepare(cubrid_db_cursor[0], 'col_1 set(varchar)', samples, 1)
    assert inserted == [({'abc','bcd','ceee','dddddd'},)]


def test_set_prepare_bit(cubrid_db_cursor):
    samples = [((b'\x14', b'\x12\x90'),)]
    inserted = _test_set_prepare(cubrid_db_cursor[0], 'col_1 set(bit(16))', samples, 1)
    assert inserted == [({'1400', '1290'},)]
