# pylint: disable=missing-function-docstring,missing-module-docstring

def test_enum_01_insert(cubrid_db_cursor, enum_01_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"insert into {enum_01_table} "
        "values(1,1,1),(2,'Tuesday','No'), (3, 'Wednesday','Cancel')")
    assert rc == 3


def test_enum_01_select_cast(cubrid_db_cursor, enum_01_table):
    cur, _ = cubrid_db_cursor

    cur.execute("select cast(working_days as int), "
        f"cast(answers as int) from {enum_01_table}")
    rows = cur.fetchall()
    assert rows == [(1, 1), (2, 2), (3, 3)]


def test_enum_01_select(cubrid_db_cursor, enum_01_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"select count(*) from {enum_01_table}")
    row = cur.fetchone()
    assert row[0] == 3


def test_enum_02_insert(cubrid_db_cursor, enum_02_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"insert into {enum_02_table} values(1,1,1)")
    assert rc == 1


def test_enum_02_select(cubrid_db_cursor, enum_02_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"select count(*) from {enum_02_table}")
    row = cur.fetchone()
    assert row[0] == 1


def test_enum_03_insert(cubrid_db_cursor, enum_03_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"insert into {enum_03_table} values(1,1,1),"
        "(2,'Tuesday','No'), (3, 'Wednesday','Cancel')")
    assert rc == 3


def test_enum_03_update(cubrid_db_cursor, enum_03_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"insert into {enum_03_table} values(1,1,1),"
        "(2,'Tuesday','No'), (3, 'Wednesday','Cancel')")
    assert rc == 3

    rc = cur.execute(f"update {enum_03_table} set answers=1")
    assert rc == 3


def test_enum_03_select(cubrid_db_cursor, enum_03_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"select count(*) from {enum_03_table}")
    row = cur.fetchone()
    assert row[0] == 0


def test_enum_04_update_1(cubrid_db_cursor, enum_04_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"update {enum_04_table} set e1=cast(e2 as int) where e2 < 3")
    assert rc == 4

    cur.execute(f"select * from {enum_04_table}")
    rows = cur.fetchall()
    assert rows == [('a', 'Yes'), ('b', 'No'), ('a', 'Cancel'),
                    ('a', 'Yes'), ('b', 'No'), ('b', 'Cancel')]


def test_enum_04_update_2(cubrid_db_cursor, enum_04_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"update {enum_04_table} set e2=e1 + 1")
    assert rc == 6

    cur.execute(f"select * from {enum_04_table}")
    rows = cur.fetchall()
    assert rows == [('a', 'No'), ('a', 'No'), ('a', 'No'),
                    ('b', 'Cancel'), ('b', 'Cancel'), ('b', 'Cancel')]


def test_enum_04_update_3(cubrid_db_cursor, enum_04_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"update {enum_04_table} set e1='b', e2='No'")
    assert rc == 6

    cur.execute(f"select * from {enum_04_table}")
    rows = cur.fetchall()
    assert rows == [('b', 'No'), ('b', 'No'), ('b', 'No'),
                    ('b', 'No'), ('b', 'No'), ('b', 'No')]
