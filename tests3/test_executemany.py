# pylint: disable=missing-function-docstring,missing-module-docstring
import pytest

import CUBRIDdb


def test_insert(cubrid_db_cursor, exc_many_table):
    cur, _ = cubrid_db_cursor

    cur.executemany(f"insert into {exc_many_table} values(?,?)",
        (('name1','category1'),('name2','category2')))

    cur.execute(f"select count(*) from {exc_many_table}")
    row = cur.fetchone()
    assert row[0] == '2'


def test_select(cubrid_db_cursor, exc_many_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"INSERT INTO {exc_many_table} (name, category) "
        "VALUES('snake', 'reptile'),('frog', 'amphibian'),"
        "('frog2', 'fish'),('racoon', 'mammal') ")
    assert rc == 4

    cur.executemany(f"select * from {exc_many_table} where name like ?",
        (('sn%'),('fr%'),('rac%')))
    rows = cur.fetchall()
    assert rows == [('racoon', 'mammal')]


def test_update(cubrid_db_cursor, exc_many_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"INSERT INTO {exc_many_table} (name, category) "
        "VALUES('snake', 'reptile'),('frog', 'amphibian'),"
        "('tuna', 'fish'),('racoon', 'mammal') ")
    assert rc == 4

    cur.executemany(f" UPDATE {exc_many_table} SET category =? WHERE name =? ",
        (('update1', 'snake'), ('update2','frog')))

    cur.execute(f"SELECT name, category FROM {exc_many_table}")
    rows = cur.fetchall()
    assert rows == [('snake', 'update1'), ('frog', 'update2'),
                    ('tuna', 'fish'), ('racoon', 'mammal')]


def test_delete(cubrid_db_cursor, exc_many_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"INSERT INTO {exc_many_table} (name, category) "
        "VALUES('snake', 'reptile'),('frog', 'amphibian'),('tuna', 'fish'),"
        "('racoon', 'mammal') ,('name1','category1'),('name2','category2')")
    assert rc == 6

    cur.executemany(f"delete from {exc_many_table} where name like ?",
        (('sna%'),('fro%')))

    cur.execute(f"select * from {exc_many_table}")
    rows = cur.fetchall()
    assert rows == [('tuna', 'fish'), ('racoon', 'mammal'),
                    ('name1', 'category1'), ('name2', 'category2')]


def test_primary_insert_select(cubrid_db_cursor, exc_primary_tables):
    cur, _ = cubrid_db_cursor
    ptb, ftb = exc_primary_tables

    cur.execute(f"select * from {ptb}")
    rows = [(row[0].strip(), row[1], row[2]) for row in cur.fetchall()]
    assert rows == [('001', 'aaaa', 'aaaa'), ('002', 'bbbb', 'bbbb'), ('003', 'cccc', 'cccc'),
                    ('004', 'dddd', 'dddd'), ('005', 'eeee', 'eeee')]

    cur.execute(f"select count(*) from {ftb}")
    row = cur.fetchone()
    assert row[0] == '6'


def test_primary_update(cubrid_db_cursor, exc_primary_tables):
    cur, _ = cubrid_db_cursor
    ptb, ftb = exc_primary_tables

    cur.executemany(f"update {ptb} set title=? where id like ?",
        (('change1','001%'), ('change2','002%')))
    cur.execute(f"select * from {ptb} where title like 'change%'")
    rows = [(row[0].strip(), row[1], row[2]) for row in cur.fetchall()]
    assert rows == [('001', 'change1', 'aaaa'), ('002', 'change2', 'bbbb')]

    cur.executemany(f"update {ftb} set song=? where album like ?",
        (('song1','001%'), ('song2','002%')))
    cur.execute(f"select * from {ftb} where song like 'song%'")
    rows = [(row[0].strip(), row[1], row[2], row[3]) for row in cur.fetchall()]
    assert rows == [('001', 1, 1, 'song1'), ('001', 2, 2, 'song1'),
                    ('002', 3, 3, 'song2'), ('002', 4, 4, 'song2')]


def test_primary_delete(cubrid_db_cursor, exc_primary_tables):
    cur, _ = cubrid_db_cursor
    ptb, ftb = exc_primary_tables

    with pytest.raises(CUBRIDdb.IntegrityError, match = r'-924'):
        cur.executemany(f"delete from {ptb} where id like ?",(('001%'),('002%'),('003%')))

    cur.execute(f"select * from {ptb}")
    rows = [(row[0].strip(), row[1], row[2]) for row in cur.fetchall()]
    assert rows == [('001', 'aaaa', 'aaaa'), ('002', 'bbbb', 'bbbb'), ('003', 'cccc', 'cccc'),
                    ('004', 'dddd', 'dddd'), ('005', 'eeee', 'eeee')]

    cur.executemany(f"delete from {ftb} where album like  ?",( ('001%'),('002%')))
    cur.execute(f"select * from {ftb} ")
    rows = [(row[0].strip(), row[1], row[2], row[3]) for row in cur.fetchall()]
    assert rows == [('003', 5, 5, '5656'), ('003', 6, 6, '6767')]
