import django
from CUBRIDdb import FIELD_TYPE

if django.VERSION >= (1, 6) and django.VERSION <= (1, 8):
    from django.db.backends import BaseDatabaseIntrospection
    from django.db.backends import FieldInfo
    from django.utils.encoding import force_text
else:
    from django.db.backends.base.introspection import BaseDatabaseIntrospection
    from django.db.backends.base.introspection import FieldInfo
    from django.db.backends.base.introspection import TableInfo
    from django.db.models.indexes import Index
    from django.utils.encoding import force_text


class DatabaseIntrospection(BaseDatabaseIntrospection):
    data_types_reverse = {
        FIELD_TYPE.CHAR: 'CharField',
        FIELD_TYPE.VARCHAR: 'CharField',
        FIELD_TYPE.NCHAR: 'CharField',
        FIELD_TYPE.VARNCHAR: 'CharField',
        FIELD_TYPE.NUMERIC: 'DecimalField',
        FIELD_TYPE.INT: 'IntegerField',
        FIELD_TYPE.SMALLINT: 'SmallIntegerField',
        FIELD_TYPE.BIGINT: 'BigIntegerField',
        FIELD_TYPE.FLOAT: 'FloatField',
        FIELD_TYPE.DOUBLE: 'FloatField',
        FIELD_TYPE.DATE: 'DateField',
        FIELD_TYPE.TIME: 'TimeField',
        FIELD_TYPE.TIMESTAMP: 'DateTimeField',
        FIELD_TYPE.DATETIME: 'DateTimeField',
        FIELD_TYPE.STRING: 'CharField',
        FIELD_TYPE.SET: 'TextField',
        FIELD_TYPE.MULTISET: 'TextField',
        FIELD_TYPE.SEQUENCE: 'TextField',
        FIELD_TYPE.BLOB: 'BinaryField',
        FIELD_TYPE.CLOB: 'TextField',
    }

    def get_table_list(self, cursor):
        """Returns a list of table names in the current database."""
        if django.VERSION >= (1, 8):
            cursor.execute("SHOW FULL TABLES")
            return [TableInfo(row[0], {'BASE TABLE': 't', 'VIEW': 'v'}.get(row[1]))
                    for row in cursor.fetchall()]
        else:
            cursor.execute("SHOW TABLES")
            return [row[0] for row in cursor.fetchall()]

    def table_name_converter(self, name):
        """Table name comparison is case insensitive under CUBRID"""
        return name.lower()

    def get_table_description(self, cursor, table_name):
        """Returns a description of the table, with the DB-API cursor.description interface."""
        cursor.execute("SELECT * FROM %s LIMIT 1" % self.connection.ops.quote_name(table_name))

        if django.VERSION >= (1, 6):
            # In case of char type, django uses line[3](internal_size) as max_length
            return [FieldInfo(*((force_text(line[0]),) + line[1:3]
                    + (line[4],)  # use precision value as internal_size
                    + line[4:7]))
                    for line in cursor.description]
        else:
            return [line[:3] + (line[4],)
                    + line[4:] for line in cursor.description]

    def get_relations(self, cursor, table_name):
        """
        Returns a dictionary of {field_index: (field_index_other_table, other_table)}
        representing all relationships to the given table. Indexes are 0-based.
        """

        raise NotImplementedError

    def get_key_columns(self, cursor, table_name):
        """
        Returns a list of (column_name, referenced_table_name, referenced_column_name) for all
        key columns in given table.
        """

        raise NotImplementedError

    def get_indexes(self, cursor, table_name):
        cursor.execute("""
            SELECT db_index_key.key_attr_name, db_index.is_primary_key, db_index.is_unique
            FROM db_index_key, db_index
            WHERE db_index_key.class_name = ?
              AND db_index.class_name = ?
              AND db_index_key.key_order = 0
              AND db_index_key.index_name = db_index.index_name
              AND db_index.key_count = 1;""", [table_name, table_name])
        rows = list(cursor.fetchall())
        indexes = {}
        for row in rows:
            indexes[row[0]] = {'primary_key': (row[1] == 'YES'), 'unique': (row[2] == 'YES')}

        return indexes

    def get_constraints(self, cursor, table_name):
        def parse_create_table_stmt(stmt):
            i = 0
            while i < len(stmt):
                i_constraint = stmt.find('CONSTRAINT', i + 1)
                i_index = stmt.find('INDEX', i + 1)

                if i_constraint == -1 and i_index == -1:
                    yield stmt[i:]
                    return

                if i_constraint == -1:
                    i1 = i_index
                elif i_index == -1:
                    i1 = i_constraint
                else:
                    i1 = min(i_constraint, i_index)

                yield stmt[i:i1]
                i = i1

        def parse_columns_sql(columns_sql):
            return [column[1:-1] for column in columns_sql.split(", ")]

        def parse_constraint_sql(sql):
            name_i0 = sql.index('[')
            name_i1 = sql.index(']', name_i0)
            name = sql[name_i0 + 1 : name_i1]

            sql = sql[name_i1 + 1:]
            kind_i0 = 0
            kind_i1 = sql.index('(')
            kind = sql[:kind_i1].strip()

            sql = sql[kind_i1 + 1:]
            columns_i1 = sql.index(')')
            columns_sql = sql[:columns_i1].strip()
            columns = parse_columns_sql(columns_sql)

            attrs = {
                'columns': columns,
                'primary_key': kind == "PRIMARY KEY",
                'unique': kind == "UNIQUE KEY",
                'foreign_key': None,
                'check': False,
                'index': False,
            }

            if kind == "FOREIGN KEY":
                sql = sql[columns_i1 + 1:]
                assert sql.strip().startswith("REFERENCES")
                ref_name_i0 = sql.index('[')
                ref_name_i1 = sql.index(']')
                ref_name = sql[ref_name_i0 + 1 : ref_name_i1]

                sql = sql[ref_name_i1 + 1:]
                ref_columns_i0 = sql.index('(')
                ref_columns_i1 = sql.index(')')
                ref_columns_sql = sql[ref_columns_i0 + 1 : ref_columns_i1]
                ref_columns = parse_columns_sql(ref_columns_sql)
                assert len(ref_columns) == 1

                attrs['foreign_key'] = (ref_name, ref_columns[0])

            return name, attrs

        def parse_index_sql(sql):
            name = sql.split('[')[1].split(']')[0]
            columns_sql = sql.split('(')[1].split(')')[0]
            columns = parse_columns_sql(columns_sql)
            orders = ['DESC' if column.find('DESC') > -1 else 'ASC' for column in columns]

            attrs = {
                'columns': columns,
                'primary_key': False,
                'unique': False,
                'foreign_key': None,
                'check': False,
                'index': True,
                'orders': orders,
                'type': Index.suffix,
            }

            return name, attrs

        query = "SHOW CREATE TABLE %s" % table_name
        cursor.execute(query)
        tname, stmt = cursor.fetchone()

        constraints = {}
        l = list(parse_create_table_stmt(stmt))
        for sql in l:
            if sql.startswith("CONSTRAINT"):
                name, attrs = parse_constraint_sql(sql)
            elif sql.startswith("INDEX"):
                name, attrs = parse_index_sql(sql)
            else:
                name = None

            if name is not None:
                constraints[name] = attrs

        return constraints


