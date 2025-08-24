# pylint: disable=missing-function-docstring,missing-module-docstring
import re

import pytest

from conftest import (
    TABLE_PREFIX,
    _create_table,
    _drop_table,
)

import CUBRIDdb


def test_execute(cubrid_db_cursor, booze_table):
    cur, _ = cubrid_db_cursor

    res = cur.execute(f'select name from {booze_table}')
    assert res == 0, 'cur.execute should return 0 if a query retrieves no rows'

    cur.execute(f"insert into {booze_table} values ('Victoria Bitter')")
    assert cur.rowcount in (-1, 1)

    # qmark param style
    cur.execute(f'insert into {booze_table} values (?)', ("Cooper's",))

    assert cur.rowcount in (-1, 1)

    cur.execute(f'select name from {booze_table}')
    res = cur.fetchall()
    assert len(res) == 2, 'cursor.fetchall returned incorrect number of rows'
    beers = [res[0][0], res[1][0]]
    beers.sort()
    assert beers[0] == "Cooper's",\
        'cursor.fetchall retrieved incorrect data, or data inserted incorrectly'
    assert beers[1] == "Victoria Bitter",\
        'cursor.fetchall retrieved incorrect data, or data inserted incorrectly'


def test_execute_select_version(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    cur.execute("SELECT VERSION()")
    row = cur.fetchone()
    assert re.match(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]{4}', row[0])


def test_execute_insert(cubrid_db_cursor, exc_table):
    cur, _ = cubrid_db_cursor
    rc = cur.execute(f"insert into {exc_table}(a,b,c) values (1,'foo_data', systimestamp)")
    assert rc == 1


def test_execute_select(cubrid_db_cursor, exc_table):
    cur, _ = cubrid_db_cursor
    for n in range(100):
        rc = cur.execute(f"insert into {exc_table}(a,b,c) values ({n} ,'foo_data', systimestamp)")
        assert rc == 1

    cur.execute(f"select count(*) from {exc_table} where a >= 0")
    row = cur.fetchone()
    assert row[0] == '100'


def test_execute_update(cubrid_db_cursor, exc_table):
    cur, _ = cubrid_db_cursor
    rc = cur.execute(f"insert into {exc_table}(a,b,c) values (1,'foo_data', systimestamp)")
    assert rc == 1

    rc = cur.execute(f"update {exc_table} set b = 'foo_data_new' where a = 1")
    assert rc == 1

    cur.execute(f"select * from {exc_table} where a = 1")
    row = cur.fetchone()
    assert row[1] == 'foo_data_new'


def test_execute_delete(cubrid_db_cursor, exc_table):
    cur, _ = cubrid_db_cursor
    rc = cur.execute(f"insert into {exc_table}(a) values (1),(2),(3),(4),(5)")
    assert rc == 5

    rc = cur.execute(f"delete from {exc_table} where a = 1")
    assert rc == 1

    cur.execute(f"select count(*) from {exc_table} where a >= 0")
    row = cur.fetchone()
    assert row[0] == '4'


def test_execute_error_statement(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    with pytest.raises(CUBRIDdb.ProgrammingError, match = r'-493'):
        cur.execute("error information")


def test_execute_empty_statement(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    with pytest.raises(TypeError, match = r"missing 1 required positional argument"):
        cur.execute()

    with pytest.raises(CUBRIDdb.DatabaseError, match = r'-424'):
        cur.execute("")


def test_create_table_no_column(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    with pytest.raises(CUBRIDdb.ProgrammingError, match = r'-493'):
        cur.execute("create table nocolumn()")


def test_select_from_empty_table(cubrid_db_cursor, exc_issue_table):
    cur, _ = cubrid_db_cursor
    with pytest.raises(CUBRIDdb.ProgrammingError, match = r'-493'):
        cur.execute(f"select from {exc_issue_table}")


def test_select_wrong_param_value(cubrid_db_cursor, exc_issue_table):
    cur, _ = cubrid_db_cursor

    with pytest.raises(CUBRIDdb.IntegrityError, match = r'-494'):
        cur.execute(f"insert into {exc_issue_table} values(?,?,?)",(8,'58aaa','aaaa'))


def test_index_select_single(cubrid_db_cursor, exc_index_tables):
    cur, _ = cubrid_db_cursor
    t, _ = exc_index_tables

    cur.execute(f"select * from {t} use index (_t_id) where id < 2")
    row = cur.fetchone()
    assert row[0] == 1


def test_index_select_recompile(cubrid_db_cursor, exc_index_tables):
    cur, _ = cubrid_db_cursor
    t, _ = exc_index_tables

    cur.execute(f"select /*+ recompile */ * from {t} use index (_t_id) where id > 1;")
    cur.fetchall()

    cur.execute(f"select /*+ recompile */ count(*) from {t} use index (_t_id) where id > 1;")
    row = cur.fetchone()
    assert row[0] == '3'


def test_index_select_join(cubrid_db_cursor, exc_index_tables):
    cur, _ = cubrid_db_cursor
    t, u = exc_index_tables

    cur.execute(f"select /*+ recompile */ * from {t} force index (_t_val) inner join {u} use "
                f"index (_u_id) on {t}.fk = {u}.id where right(text, 2) < 'zz' and {u}.id < 100")
    cur.fetchall()

    cur.execute(f"select /*+ recompile */ count(*) from {t} force index (_t_val) inner join {u} "
                f"use index (_u_id) on {t}.fk = {u}.id where right(text, 2) < 'zz' and "
                f"{u}.id < 100")
    row = cur.fetchone()
    assert row[0] == '5'


def test_index_select_subselect(cubrid_db_cursor, exc_index_tables):
    cur, _ = cubrid_db_cursor
    t, u = exc_index_tables

    cur.execute(f"select /*+ recompile */ * from {t} force index (_t_val) inner join (select * "
                f"from {u} force index (_u_id) where right(text, 2) < 'zz') x on {t}.fk = x.id ")
    cur.fetchall()

    cur.execute(f"select /*+ recompile */ count(*) from {t} force index (_t_val) inner join "
                f"(select * from {u} force index (_u_id) where right(text, 2) < 'zz') x on "
                f"{t}.fk = x.id")
    row = cur.fetchone()
    assert row[0] == '5'


def test_index_update(cubrid_db_cursor, exc_index_tables):
    cur, _ = cubrid_db_cursor
    t, _ = exc_index_tables

    rc = cur.execute(f"update {t} use index (_t_id, _t_val) set val = 1000 where id <4")
    assert rc == 3

    cur.execute(f"select * from {t}")
    cur.fetchall()

    cur.execute(f"select count(*) from {t} where val=1000")
    row = cur.fetchone()
    assert row[0] == '3'


def test_index_delete(cubrid_db_cursor, exc_index_tables):
    cur, _ = cubrid_db_cursor
    t, _ = exc_index_tables

    cur.executemany(f"delete from {t} use index (_t_id, _t_val) where id =?",((1),(4),(3)))
    cur.execute(f"select * from {t}")
    row = cur.fetchone()
    assert row[0] == 2


def test_partition_select_empty_table(cubrid_db_cursor, exc_part_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"select count(*) from {exc_part_table}")
    row = cur.fetchone()
    assert row[0] == '0'

    cur.execute(f"select max(id) from {exc_part_table}")
    row = cur.fetchone()
    assert row[0] is None


def test_partition_alter(cubrid_db_cursor, exc_part_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"ALTER TABLE {exc_part_table} PARTITION BY LIST (test_char) "
        "(PARTITION p0 VALUES IN ('aaa','bbb','ddd'),PARTITION p1 VALUES IN "
        "('fff','ggg','hhh',NULL),PARTITION p2 VALUES IN ('kkk','lll','mmm') )")
    assert rc == 0


def test_partition_insert(cubrid_db_cursor, exc_part_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"ALTER TABLE {exc_part_table} PARTITION BY LIST (test_char) "
        "(PARTITION p0 VALUES IN ('aaa','bbb','ddd'),PARTITION p1 VALUES IN "
        "('fff','ggg','hhh',NULL),PARTITION p2 VALUES IN ('kkk','lll','mmm') )")
    assert rc == 0

    rc = cur.execute(f"insert into {exc_part_table} values(1,'aaa','aaa',B'1',B'1011',"
        "N'aaa',N'aaa','aaaaaaaaaa','2006-03-01 09:00:00')")
    assert rc == 1
    rc = cur.execute(f"insert into {exc_part_table} values(5,'ggg','ggg',B'101',B'1111',"
        "N'ggg',N'ggg','gggggggggg','2006-03-01 09:00:00')")
    assert rc == 1


def test_partition_select(cubrid_db_cursor, exc_part_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"ALTER TABLE {exc_part_table} PARTITION BY LIST (test_char) "
        "(PARTITION p0 VALUES IN ('aaa','bbb','ddd'),PARTITION p1 VALUES IN "
        "('fff','ggg','hhh',NULL),PARTITION p2 VALUES IN ('kkk','lll','mmm') )")
    assert rc == 0

    rc = cur.execute(f"insert into {exc_part_table} values(1,'aaa','aaa',B'1',B'1011',"
        "N'aaa',N'aaa','aaaaaaaaaa','2006-03-01 09:00:00')")
    assert rc == 1

    rc = cur.execute(f"insert into {exc_part_table} values(5,'ggg','ggg',B'101',B'1111',"
        "N'ggg',N'ggg','gggggggggg','2006-03-01 09:00:00')")
    assert rc == 1

    rc = cur.execute(f"insert into {exc_part_table} values(10, 'kkk',null,null,null,null,"
        "null,null,'2007-01-01 09:00:00');")
    assert rc == 1

    cur.execute(f"select * from {exc_part_table}__p__p0 order by id;")
    row = cur.fetchone()
    assert row[1] == 'aaa                                               '


def test_partition_delete(cubrid_db_cursor, exc_part_table):
    cur, _ = cubrid_db_cursor

    rc = cur.execute(f"ALTER TABLE {exc_part_table} PARTITION BY LIST (test_char) "
        "(PARTITION p0 VALUES IN ('aaa','bbb','ddd'),PARTITION p1 VALUES IN "
        "('fff','ggg','hhh',NULL),PARTITION p2 VALUES IN ('kkk','lll','mmm') )")
    assert rc == 0

    rc = cur.execute(f"insert into {exc_part_table} values(1,'aaa','aaa',B'1',B'1011',"
        "N'aaa',N'aaa','aaaaaaaaaa','2006-03-01 09:00:00')")
    assert rc == 1

    rc = cur.execute(f"insert into {exc_part_table} values(5,'ggg','ggg',B'101',B'1111',"
        "N'ggg',N'ggg','gggggggggg','2006-03-01 09:00:00')")
    assert rc == 1

    rc = cur.execute(f"insert into {exc_part_table} values(10, 'kkk',null,null,null,null,"
        "null,null,'2007-01-01 09:00:00');")
    assert rc == 1

    rc = cur.execute(f"delete from {exc_part_table} where id = 1")
    assert rc == 1

    cur.execute(f"select count(*) from {exc_part_table} where id >= 0")
    row = cur.fetchone()
    assert row[0] == '2'


def test_primary_insert(cubrid_db_cursor, exc_primary_tables):
    pass # insertion already done by exc_primary_tables fixture


def test_primary_select(cubrid_db_cursor, exc_primary_tables):
    cur, _ = cubrid_db_cursor
    ptb, ftb = exc_primary_tables

    cur.execute(f"select title from {ptb} where id like ?", ('001%',))
    row = cur.fetchone()
    assert row[0] == 'aaaa'

    cur.execute(f"select song from {ftb} where dsk=?", (6,))
    row = cur.fetchone()
    assert row[0] == '6767'


def test_primary_update(cubrid_db_cursor, exc_primary_tables):
    cur, _ = cubrid_db_cursor
    ptb, ftb = exc_primary_tables

    rc = cur.execute(f"update {ptb} set id = 'changeid11' where id like '004%'")
    assert rc == 1

    cur.execute(f"select * from {ptb} where id like 'change%'")
    row = cur.fetchone()
    assert row[2] == 'dddd'


    rc = cur.execute(f"update {ftb} set song = 'changesong' where album like '003%'")
    assert rc == 2

    cur.execute(f"select * from {ftb}  where album like '003%'")
    row = cur.fetchone()
    assert row[1] == 5

    row = cur.fetchone()
    assert row[1] == 6


def test_primary_delete(cubrid_db_cursor, exc_primary_tables):
    cur, _ = cubrid_db_cursor
    ptb, ftb = exc_primary_tables

    rc = cur.execute(f"delete from {ptb}  where id like '004%'")
    assert rc == 1

    cur.execute(f"select count(*) from {ptb} ")
    row = cur.fetchone()
    assert row[0] == '4'

    rc = cur.execute(f"delete from {ftb} where album like '003%'")
    assert rc == 2

    cur.execute(f"select count(*) from {ftb}")
    row = cur.fetchone()
    assert row[0] == '4'


def test_rollback(cubrid_db_cursor, exc_rollback_table):
    cur, con = cubrid_db_cursor

    cur.execute(f"INSERT INTO {exc_rollback_table} (name,nameid,age) "
        "VALUES('forrollback',6,66)")
    cur.execute(f"select * from {exc_rollback_table} where nameid=6")
    row = cur.fetchone()
    assert row[1] == 66

    con.rollback()

    cur.execute(f"select * from {exc_rollback_table} where nameid=6")
    rows = cur.fetchall()
    assert not rows


def test_rollback_extra_argument_error(cubrid_db_cursor, exc_rollback_table):
    cur, con = cubrid_db_cursor
    cur.execute(f"INSERT INTO {exc_rollback_table} (name,nameid,age) "
        "VALUES('forrollback',6,66)")

    with pytest.raises(TypeError, match = r'takes 1 positional argument but 2 were given'):
        con.rollback("pass a parameter")


def test_select_calculate_subselect(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor

    table_name = f"{TABLE_PREFIX}sctb"

    try:
        _drop_table(cubrid_db_cursor, table_name)
        _create_table(cubrid_db_cursor, "sctb",
            "nameid int primary key ,name VARCHAR(40)")

        cur.execute(f"INSERT INTO {table_name} (name,nameid) "
            "VALUES('Mike',1),('John',2),('Bill',3)")
        cur.execute(f"SELECT * FROM ( SELECT * FROM {table_name} ) WHERE Name in ('John')")
        row = cur.fetchone()
        assert row[0] == 2
    finally:
        _drop_table(cubrid_db_cursor, table_name)


def test_select_calculate(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor

    cur.execute("SELECT 4 + '5.2'")
    row = cur.fetchone()
    assert row[0] == 9.1999999999999993

    cur.execute("select date'2001-02-03' - datetime'2001-02-02 12:00:00 am'")
    row = cur.fetchone()
    assert row[0] == '86400000'

    cur.execute("SELECT date'2002-01-01' + '10'")
    row = cur.fetchone()
    assert row[0].isoformat() == '2002-01-11'

    cur.execute("SELECT '1'+'1'")
    row = cur.fetchone()
    assert row[0] == '11'

    cur.execute("SELECT '3'*'2'")
    row = cur.fetchone()
    assert row[0] == 6.0000000000000000

    cur.execute("select BIT_LENGTH('CUBRID')")
    row = cur.fetchone()
    assert row[0] == 48

    cur.execute("select BIT_LENGTH(B'010101010')")
    row = cur.fetchone()
    assert row[0] == 9

    cur.execute("SELECT LENGTH('')")
    row = cur.fetchone()
    assert row[0] == 0

    cur.execute("SELECT CHR(68) || CHR(68-2)")
    row = cur.fetchone()
    assert row[0] == 'DB'

    cur.execute("SELECT INSTR ('12345abcdeabcde','b', -1)")
    row = cur.fetchone()
    assert row[0] == 12


def test_trigger(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor

    hi = f"{TABLE_PREFIX}hi"
    tt1 = f"{TABLE_PREFIX}tt1"

    try:
        _drop_table(cubrid_db_cursor, hi)
        _drop_table(cubrid_db_cursor, tt1)
        _create_table(cubrid_db_cursor, "hi", "a int , b string")
        _create_table(cubrid_db_cursor, "tt1", "a int , b string")

        cur.execute(f"create trigger tt1_insert after insert on {tt1} execute "
            f"insert into {hi}(a, b) values( obj.a ,to_char(obj.a))")

        cur.execute(f"insert into {tt1}(a,b) values(1, 'test')")
        cur.execute(f"select * from {hi}")
        rows = cur.fetchall()
        assert rows == [(1, '1')]

        cur.execute(f"select * from {tt1}")
        rows = cur.fetchall()
        assert rows == [(1, 'test')]
    finally:
        _drop_table(cubrid_db_cursor, hi)
        _drop_table(cubrid_db_cursor, tt1)


def test_view_select(cubrid_db_cursor, exc_view_v, exc_view_table):
    cur, _ = cubrid_db_cursor
    vtb = exc_view_table

    cur.execute(f"select * from {exc_view_v}")
    row = cur.fetchone()
    assert row[2] == 150

    cur.execute(f"SHOW CREATE VIEW {exc_view_v}")
    row = cur.fetchone()
    assert row[1] == (f'select [dba.{vtb}].[qty], [dba.{vtb}].[price], '
        f'[dba.{vtb}].[qty]*[dba.{vtb}].[price] from [dba.{vtb}] [dba.{vtb}]')


def test_view_alter(cubrid_db_cursor, exc_view_b, exc_view_a_table):
    cur, _ = cubrid_db_cursor

    cur.execute(f"ALTER VIEW {exc_view_b} ADD QUERY "
        f"SELECT * FROM {exc_view_a_table} WHERE id IN (1,2)")
    cur.execute(f"select * from {exc_view_b}")
    rows = cur.fetchall()
    assert rows == [(1, '111-1111'), (2, '222-2222'), (3, '333-3333'),
                    (1, '111-1111'), (2, '222-2222')]


def test_view_update(cubrid_db_cursor, exc_view_b):
    cur, _ = cubrid_db_cursor

    with pytest.raises(CUBRIDdb.IntegrityError, match = r'-494'):
        cur.execute(f"UPDATE {exc_view_b} SET phone=NULL")
