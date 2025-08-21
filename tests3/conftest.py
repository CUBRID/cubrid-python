"""
This module provides pytest fixtures for establishing a connection and creating a cursor
for interacting with a CUBRID database in a testing environment. It encapsulates the
database connection parameters and setup logic, offering a simplified interface for
database interactions within test cases.
"""
# pylint: disable=missing-function-docstring

import pytest

import _cubrid
import CUBRIDdb


def _get_connect_args():
    ip = "test-db-server"
    port = "33000"
    dbname = "demodb"
    user = "dba"
    password = ""

    return {
        'dsn': f"CUBRID:{ip}:{port}:{dbname}:::",
        'user': user,
        'password': password,
    }


@pytest.fixture
def cubrid_connection():
    args = _get_connect_args()
    conn = _cubrid.connect(args['dsn'], args['user'], args['password'])
    yield conn

    conn.close()


@pytest.fixture
def cubrid_cursor(cubrid_connection):
    # Obtain a cursor from the database connection provided by the cubrid_connection fixture
    cursor = cubrid_connection.cursor()
    yield cursor, cubrid_connection

    # Ensure the cursor is closed after the test
    cursor.close()


@pytest.fixture
def cubrid_db_connection():
    args = _get_connect_args()
    conn = CUBRIDdb.connect(args['dsn'], args['user'], args['password'])
    yield conn
    conn.close()


@pytest.fixture
def cubrid_db_cursor(cubrid_db_connection):
    # Obtain a cursor from the database connection provided by the cubrid_connection fixture
    cursor = cubrid_db_connection.cursor()
    yield cursor, cubrid_db_connection

    # Ensure the cursor is closed after the test
    cursor.close()


TABLE_PREFIX = 'dbapi20test_'


def _create_table(cdb_cur, name_suffix, columns_sql):
    cur, _ = cdb_cur
    table_name = f'{TABLE_PREFIX}{name_suffix}'
    cur.execute(f'drop table if exists {table_name}')
    cur.execute(f'create table {table_name} ({columns_sql})')
    return table_name

def _drop_table(cdb_cur, table_name):
    cur, _ = cdb_cur
    cur.execute(f'drop table if exists {table_name}')


@pytest.fixture
def booze_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'booze', 'name varchar(20)')
    yield table_name
    _drop_table(cubrid_db_cursor, table_name)


@pytest.fixture
def barflys_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'barflys', 'name varchar(20)')
    yield table_name
    _drop_table(cubrid_db_cursor, table_name)


@pytest.fixture
def datatype_table(cubrid_db_cursor):
    columns_sql = ('col1 int, col2 float, col3 numeric(12,3), '
        'col4 time, col5 date, col6 datetime, col7 timestamp, '
        'col8 bit varying(100), col9 varchar(100), col10 set(char(1)), '
        'col11 list(char(1)), col12 json')
    table_name = _create_table(cubrid_db_cursor, 'datatype', columns_sql)
    yield table_name
    _drop_table(cubrid_db_cursor, table_name)


BOOZE_SAMPLES = [
    'Carlton Cold',
    'Carlton Draft',
    'Mountain Goat',
    'Redback',
    'Victoria Bitter',
    'XXXX'
]


@pytest.fixture
def populated_booze_table(cubrid_db_cursor, booze_table):
    cur, _ = cubrid_db_cursor
    cur.executemany(f'insert into {booze_table} values (?)', BOOZE_SAMPLES)
    yield booze_table


@pytest.fixture
def fetchmany_table(cubrid_db_cursor):
    cur, _ = cubrid_db_cursor
    table_name = _create_table(cubrid_db_cursor, 'fetchmany',
        "id NUMERIC AUTO_INCREMENT(1, 1), age int, name varchar(50)")
    cur.executemany(f"insert into {table_name} values (?, ?, ?)",
        [(None, 20 + i % 30, f'myName-{i}') for i in range(1, 100)])
    yield table_name
    _drop_table(cubrid_db_cursor, table_name)


@pytest.fixture
def desc_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'description',
        "c_int int, c_short short,c_numeric numeric,c_float float,"
        "c_double double,c_monetary monetary,"
        "c_date date, c_time time, c_datetime datetime, c_timestamp timestamp,"
        "c_bit bit(8),c_varbit bit varying(8),"
        "c_char char(4),c_varchar varchar(4),c_string string,"
        "c_set set,c_multiset multiset, c_sequence sequence"
        )
    yield table_name
    _drop_table(cubrid_db_cursor, table_name)


@pytest.fixture
def exc_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'execute',
        "a int primary key, b varchar(20), c timestamp")
    yield table_name
    _drop_table(cubrid_db_cursor, table_name)


@pytest.fixture
def exc_issue_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'execute_issue',
        "nameid int primary key ,age int,name VARCHAR(40)")
    cur, _ = cubrid_db_cursor
    cur.execute(f"INSERT INTO {table_name} (name,nameid,age) "
                "VALUES('Mike',1,30),('John',2,28),('Bill',3,45)")
    yield table_name
    _drop_table(cubrid_db_cursor, table_name)


@pytest.fixture
def exc_index_tables(cubrid_db_cursor):
    t = _create_table(cubrid_db_cursor, 'index_t', "id int, val int, fk int")
    u = _create_table(cubrid_db_cursor, 'index_u', "id int, val int,text string")

    cur, _ = cubrid_db_cursor

    cur.execute(f"create index _t_id on {t}(id)")
    cur.execute(f"create index _t_val on {t}(val)")
    cur.execute(f"create index _u_id on {u}(id)")
    cur.execute(f"create index _u_val on {u}(val)")
    cur.execute(f"create index _u_r_text on {u}(text)")
    cur.execute(f"insert into {t} values (1, 100, 1),(2, 200, 1),(3, 300, 2),(4, 300, 3)")
    cur.execute(f"insert into {u} values (1, 1000, '1000 text'),(2, 2000, '2000 text'),"
                "(3, 3000, '3000 text'),(3, 3001, '3001 text')")

    yield t, u

    _drop_table(cubrid_db_cursor, t)
    _drop_table(cubrid_db_cursor, u)


@pytest.fixture
def exc_part_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'partition',
        "id int not null, test_char char(50),test_varchar varchar(2000), test_bit bit(16),"
        "test_varbit bit varying(20),test_nchar nchar(50),test_nvarchar nchar varying(2000),"
        "test_string string,test_datetime timestamp, primary key (id, test_char)")
    yield table_name
    _drop_table(cubrid_db_cursor, table_name)


@pytest.fixture
def exc_primary_tables(cubrid_db_cursor):
    # Avoid drop error if primary_table is dropped first
    ftb = f'{TABLE_PREFIX}foreign_table'
    _drop_table(cubrid_db_cursor, ftb)

    # Create tables
    ptb = _create_table(cubrid_db_cursor, 'primary_table',
        "id CHAR(10) PRIMARY KEY, title VARCHAR(100), artist VARCHAR(100)")
    ftb = _create_table(cubrid_db_cursor, 'foreign_table',
        "album CHAR(10),dsk INTEGER,posn INTEGER,song VARCHAR(255),"
        f"FOREIGN KEY (album) REFERENCES {ptb}(id) ON UPDATE RESTRICT")

    # Insert data
    cur, _ = cubrid_db_cursor
    rc = cur.execute(f"insert into {ptb} values ('001','aaaa', 'aaaa'), "
        "('002','bbbb', 'bbbb'),('003','cccc', 'cccc'),('004','dddd', 'dddd'),"
        "('005','eeee', 'eeee')")
    assert rc == 5

    rc = cur.execute(f"insert into {ftb} values ( '001' , 1,1,'1212'),"
        "( '001' , 2,2,'2323'), ( '002' , 3,3,'3434'),( '002' , 4,4,'4545'), "
        "( '003' , 5,5,'5656'), ( '003' , 6,6,'6767')")
    assert rc == 6

    yield ptb, ftb

    _drop_table(cubrid_db_cursor, ftb)
    _drop_table(cubrid_db_cursor, ptb)


@pytest.fixture
def exc_rollback_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'rollback',
        "nameid int primary key ,age int,name VARCHAR(40)")

    cur, con = cubrid_db_cursor
    cur.execute(f"INSERT INTO {table_name} (name,nameid,age) VALUES('Mike',1,30),"
        "('John',2,28),('Bill',3,45)")

    con.set_autocommit(False)

    yield table_name

    con.set_autocommit(True)

    _drop_table(cubrid_db_cursor, table_name)


VIEW_PREFIX = 'dbapi20testview_'


def _create_view(cdb_cur, name_suffix, view_sql):
    cur, _ = cdb_cur
    view_name = f'{TABLE_PREFIX}{name_suffix}'
    cur.execute(f'drop view if exists {view_name}')
    cur.execute(f'create view {view_name} AS {view_sql}')
    return view_name

def _drop_view(cdb_cur, view_name):
    cur, _ = cdb_cur
    cur.execute(f'drop view if exists {view_name}')


@pytest.fixture
def exc_view_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'viewtbl', "qty INT, price INT")

    cur, _ = cubrid_db_cursor
    rc = cur.execute(f"INSERT INTO {table_name} VALUES (3,50)")
    assert rc == 1

    yield table_name
    _drop_table(cubrid_db_cursor, table_name)


@pytest.fixture
def exc_view_a_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'view_py_a',
        "id INT NOT NULL,phone VARCHAR(10)")

    cur, _ = cubrid_db_cursor
    rc = cur.execute(f"INSERT INTO {table_name} VALUES(1,'111-1111'), (2,'222-2222'), "
        "(3, '333-3333'), (4, NULL), (5, NULL)")
    assert rc == 5

    yield table_name
    _drop_table(cubrid_db_cursor, table_name)


@pytest.fixture
def exc_view_v(cubrid_db_cursor, exc_view_table):
    view_name = _create_view(cubrid_db_cursor, 'v',
        f'SELECT qty, price, qty*price AS "value" FROM {exc_view_table}')
    yield view_name
    _drop_view(cubrid_db_cursor, view_name)


@pytest.fixture
def exc_view_b(cubrid_db_cursor, exc_view_a_table):
    view_name = _create_view(cubrid_db_cursor, 'b',
        f"SELECT * FROM {exc_view_a_table} WHERE phone IS NOT NULL WITH CHECK OPTION")
    yield view_name
    _drop_view(cubrid_db_cursor, view_name)


@pytest.fixture
def exc_many_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'executemany',
        "name VARCHAR(40),category VARCHAR(40)")
    yield table_name
    _drop_table(cubrid_db_cursor, table_name)


@pytest.fixture
def enum_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'enum01',
        "i INT, working_days ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'), "
        "answers ENUM('Yes', 'No', 'Cancel')")

    yield table_name

    _drop_table(cubrid_db_cursor, table_name)


@pytest.fixture
def enum_01_table(cubrid_db_cursor, enum_table):
    cur, _ = cubrid_db_cursor
    cur.execute(f"insert into {enum_table} values"
        "(1,1,1),(2,'Tuesday','No'), (3, 'Wednesday','Cancel')")
    yield enum_table


@pytest.fixture
def enum_02_table(cubrid_db_cursor, enum_table):
    cur, _ = cubrid_db_cursor
    cur.execute(f"insert into {enum_table} values(1,1,1)")
    yield enum_table


@pytest.fixture
def enum_03_table(cubrid_db_cursor, enum_table):
    yield enum_table


@pytest.fixture
def enum_04_table(cubrid_db_cursor):
    table_name = _create_table(cubrid_db_cursor, 'enum01',
        "e1 enum('a', 'b'), e2 enum('Yes', 'No', 'Cancel')")

    cur, _ = cubrid_db_cursor
    cur.execute(f"insert into {table_name} values "
        "(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)")

    yield table_name

    _drop_table(cubrid_db_cursor, table_name)
