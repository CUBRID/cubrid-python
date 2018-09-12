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
