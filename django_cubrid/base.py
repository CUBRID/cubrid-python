"""
Cubrid database backend for Django.

Requires CUBRIDdb: http://www.cubrid.org/wiki_apis
"""

import re
import sys
import django
import warnings

try:
    import CUBRIDdb as Database
    from CUBRIDdb import FIELD_TYPE
except ImportError as e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading CUBRIDdb module: %s" % e)

import django.db.utils

from django.db.backends import *
from django.db.backends.signals import connection_created
from django_cubrid.client import DatabaseClient
from django_cubrid.creation import DatabaseCreation
from django_cubrid.introspection import DatabaseIntrospection
from django_cubrid.validation import DatabaseValidation
from django.utils import timezone
from django.conf import settings
if django.VERSION >= (1, 7) and django.VERSION < (1, 8):
    from django_cubrid.schema import DatabaseSchemaEditor
elif django.VERSION >= (1, 8):
    from django_cubrid.schema import DatabaseSchemaEditor
    from django.db.backends.base.base import BaseDatabaseWrapper
    from django.db.backends.base.features import BaseDatabaseFeatures
    from django.db.backends.base.operations import BaseDatabaseOperations
    from django.utils.functional import cached_property


"""
Takes a CUBRID exception and raises the Django equivalent.
"""
def raise_django_exception(e):
    cubrid_exc_type = type(e)
    django_exc_type = getattr(django.db.utils,
        cubrid_exc_type.__name__, django.db.utils.Error)
    raise django_exc_type(*tuple(e.args))


class CursorWrapper(object):
    """
    A thin wrapper around CUBRID's normal curosr class.

    """

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, args=None):
        try:
            query = re.sub('([^%])%s', '\\1?', query)
            query = re.sub('%%', '%', query)
            return self.cursor.execute(query, args)

        except Exception as e:
            raise_django_exception(e)

    def executemany(self, query, args):
        try:
            query = re.sub('([^%])%s', '\\1?', query)
            query = re.sub('%%', '%', query)

            return self.cursor.executemany(query, args)
        except Exception as e:
            raise_django_exception(e)

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()


class DatabaseFeatures(BaseDatabaseFeatures):

    allows_group_by_pk = True

    # Can an object have a primary key of 0? MySQL says No.
    allows_primary_key_0 = True

    allow_sliced_subqueries = False

    # Does the backend prevent running SQL queries in broken transactions?
    atomic_transactions = False

    can_defer_constraint_checks = False

    # Support for the DISTINCT ON clause
    can_distinct_on_fields = False

    # CUBRID 9.3 can't retrieve foreign key info from catalog tables.
    can_introspect_foreign_keys = False

    can_return_id_from_insert = False

    can_rollback_ddl = True

    # insert into ... values(), (), ()
    has_bulk_insert = True

    # This feature is supported after 9.3
    has_select_for_update = True

    has_select_for_update_nowait = False

    # Does the database have a copy of the zoneinfo database?
    has_zoneinfo_database = False

    ignores_nulls_in_unique_constraints = False

    related_fields_match_type = True

    # When performing a GROUP BY, is an ORDER BY NULL required
    # to remove any ordering?
    requires_explicit_null_ordering_when_grouping = False

    supports_date_lookup_using_string = False

    # Can a fixture contain forward references? i.e., are
    # FK constraints checked at the end of transaction, or
    # at the end of each save operation?
    supports_forward_references = False

    # CUBRID support millisecond precision not second.
    supports_microsecond_precision = True

    supports_paramstyle_pyformat = False

    supports_regex_backreferencing = False

    supports_timezones = False

    uses_autocommit = True
    uses_savepoints = True


class DatabaseOperations(BaseDatabaseOperations):
    compiler_module = "django_cubrid.compiler"

    def date_extract_sql(self, lookup_type, field_name):
        if lookup_type == 'week_day':
            # DAYOFWEEK() returns an integer, 1-7, Sunday=1.
            # Note: WEEKDAY() returns 0-6, Monday=0.
            return "DAYOFWEEK(%s)" % field_name
        else:
            return "EXTRACT(%s FROM %s)" % (lookup_type.upper(), field_name)

    def date_trunc_sql(self, lookup_type, field_name):
        fields = [
                'year', 'month', 'day', 'hour',
                'minute', 'second', 'milisecond'
            ]
        # Use double percents to escape.
        format = (
                '%%Y-', '%%m', '-%%d', ' %%H:', '%%i', ':%%s', '.%%ms'
            )
        format_def = ('0000-', '01', '-01', ' 00:', '00', ':00', '.00')
        try:
            i = fields.index(lookup_type) + 1
        except ValueError:
            sql = field_name
        else:
            format_str = ''.join(
                [f for f in format[:i]] + [f for f in format_def[i:]])
            sql = "CAST(DATE_FORMAT(%s, '%s') AS DATETIME)" % (
                field_name, format_str)
        return sql

    def datetime_extract_sql(self, lookup_type, field_name, tzname):
        if settings.USE_TZ:
                warnings.warn("CUBRID does not support timezone conversion",
                              RuntimeWarning)

        params = []
        if lookup_type == 'week_day':
            # DAYOFWEEK() returns an integer, 1-7, Sunday=1.
            # Note: WEEKDAY() returns 0-6, Monday=0.
            return "DAYOFWEEK(%s)" % field_name, params
        else:
            return "EXTRACT(%s FROM %s)" % (lookup_type.upper(), field_name), params

    def datetime_trunc_sql(self, lookup_type, field_name, tzname):
        if settings.USE_TZ:
                warnings.warn("CUBRID does not support timezone conversion",
                              RuntimeWarning)

        params = []
        fields = ['year', 'month', 'day', 'hour', 'minute', 'second', 'milisecond']
        # Use double percents to escape.
        format = ('%%Y-', '%%m', '-%%d', ' %%H:', '%%i', ':%%s', '.%%ms')
        format_def = ('0000-', '01', '-01', ' 00:', '00', ':00', '.00')
        try:
            i = fields.index(lookup_type) + 1
        except ValueError:
            sql = field_name
        else:
            format_str = ''.join([f for f in format[:i]] + [f for f in format_def[i:]])
            sql = "CAST(DATE_FORMAT(%s, '%s') AS DATETIME)" % (field_name, format_str)
        return sql, params

    def date_interval_sql(self, sql, connector, timedelta):
        if connector.strip() == '+':
            func = "ADDDATE"
        else:
            func = "SUBDATE"

        fmt = "%s (%s, INTERVAL '%d 0:0:%d:%d' DAY_MILLISECOND)"

        return fmt % (
            func, sql, timedelta.days,
            timedelta.seconds, timedelta.microseconds / 1000)

    def drop_foreignkey_sql(self):
        return "DROP FOREIGN KEY"

    def force_no_ordering(self):
        return ["NULL"]

    def fulltext_search_sql(self, field_name):
        return 'MATCH (%s) AGAINST (%%s IN BOOLEAN MODE)' % field_name

    def quote_name(self, name):
        if name.startswith("`") and name.endswith("`"):
            # Quoting once is enough.
            return name
        return "`%s`" % name

    def no_limit_value(self):
        # 2**63 - 1
        return 9223372036854775807

    def last_insert_id(self, cursor, table_name, pk_name):
        cursor.execute("SELECT LAST_INSERT_ID()")
        result = cursor.fetchone()

        # LAST_INSERT_ID() returns Decimal type value.
        # This causes problem in django.contrib.auth test,
        # because Decimal is not JSON serializable.
        # So convert it to int if possible.
        # I think LAST_INSERT_ID should be modified
        # to return appropriate column type value.
        if result[0] < sys.maxsize:
            return int(result[0])

        return result[0]

    def random_function_sql(self):
        return 'RAND()'

    def sql_flush(self, style, tables, sequences, allow_cascade=False):
        # 'TRUNCATE x;', 'TRUNCATE y;', 'TRUNCATE z;'... style SQL statements
        # to clear all tables of all data
        # TODO: when there are FK constraints, the sqlflush command in django may be failed.
        if tables:
            sql = []
            for table in tables:
                sql.append('%s %s;' % (style.SQL_KEYWORD('TRUNCATE'), style.SQL_FIELD(self.quote_name(table))))

            # 'ALTER TABLE table AUTO_INCREMENT = 1;'... style SQL statements
            # to reset sequence indices
            sql.extend(
                ["%s %s %s %s %s;" % (style.SQL_KEYWORD('ALTER'),
                 style.SQL_KEYWORD('TABLE'),
                 style.SQL_TABLE(self.quote_name(sequence['table'])),
                 style.SQL_KEYWORD('AUTO_INCREMENT'),
                 style.SQL_FIELD('= 1'),) for sequence in sequences])
            return sql
        else:
            return []

    def value_to_db_datetime(self, value):
        if value is None:
            return None

        # Check if CUBRID supports timezones
        if timezone.is_aware(value):
            if settings.USE_TZ:
                value = value.astimezone(timezone.utc).replace(tzinfo=None)
            else:
                raise ValueError("CUBRID does not support timezone-aware datetime when USE_TZ is False.")

        return unicode(value)

    def value_to_db_time(self, value):
        if value is None:
            return None

        # Check if CUBRID supports timezones
        if value.tzinfo is not None:
            raise ValueError("CUBRID does not support timezone-aware times.")

        return unicode(value)

    def year_lookup_bounds(self, value):
        # Again, no microseconds
        first = '%s-01-01 00:00:00.00'
        second = '%s-12-31 23:59:59.99'
        return [first % value, second % value]

    def max_name_length(self):
        return 64

    if django.VERSION < (1, 9):
        def bulk_insert_sql(self, fields, num_values):
            items_sql = "(%s)" % ", ".join(["%s"] * len(fields))
            return "VALUES " + ", ".join([items_sql] * num_values)
    else:
        def bulk_insert_sql(self, fields, placeholder_rows):
            placeholder_rows_sql = (", ".join(row) for row in placeholder_rows)
            values_sql = ", ".join("({0})".format(sql) for sql in placeholder_rows_sql)
            return "VALUES " + values_sql


class DatabaseWrapper(BaseDatabaseWrapper):
    vendor = 'cubrid'
    # Operators taken from MySQL implementation.
    # Check for differences between this syntax and CUBRID's.
    operators = {
        'exact': '= %s',
        # CUBRID does not support "iexact" operator.
        # We will use "=" operator(case sensitive exact)
        # to prevent a syntax error in contrib.auth application.
        'iexact': '= %s',
        'contains': 'LIKE %s',
        'icontains': 'iLIKE %s',
        # not supported. causes syntax error.
        'regex': 'REGEXP BINARY %s',
        'iregex': 'REGEXP %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE %s',
        'endswith': 'LIKE %s',
        # not supported. causes syntax error.
        'istartswith': 'iLIKE %s',
        # not supported. causes syntax error.
        'iendswith': 'iLIKE %s',
        }
    if django.VERSION >= (1, 8):
        _data_types = {
            'AutoField': 'integer AUTO_INCREMENT',
            'BinaryField': 'blob',
            'BooleanField': 'short',
            'CharField': 'varchar(%(max_length)s)',
            'CommaSeparatedIntegerField': 'varchar(%(max_length)s)',
            'DateField': 'date',
            'DateTimeField': 'datetime',
            'DecimalField': 'numeric(%(max_digits)s, %(decimal_places)s)',
            'DurationField': 'bigint',
            'FileField': 'varchar(%(max_length)s)',
            'FilePathField': 'varchar(%(max_length)s)',
            'FloatField': 'double precision',
            'IntegerField': 'integer',
            'BigIntegerField': 'bigint',
            'IPAddressField': 'char(15)',
            'GenericIPAddressField': 'char(39)',
            'NullBooleanField': 'short',
            'OneToOneField': 'integer',
            'PositiveIntegerField': 'integer',
            'PositiveSmallIntegerField': 'smallint',
            'SlugField': 'varchar(%(max_length)s)',
            'SmallIntegerField': 'smallint',
            'TextField': 'string',
            'TimeField': 'time',
            'UUIDField': 'char(32)',
        }
        SchemaEditorClass = DatabaseSchemaEditor

    Database = Database

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        self.server_version = None
        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = DatabaseValidation(self)

    if django.VERSION >= (1, 8):
        @cached_property
        def data_types(self):
            if self.features.supports_microsecond_precision:
                return dict(self._data_types, DateTimeField='datetime', TimeField='time')
            else:
                return self._data_types

    def get_connection_params(self):
        # Backend-specific parameters
        return None

    def get_new_connection(self, conn_params):
        settings_dict = self.settings_dict

        # Connection to CUBRID database is made through connect() method.
        # Syntax:
        # connect (url[, user[password]])
        #    url - CUBRID:host:port:db_name:db_user:db_password:::
        #    user - Authorized username.
        #    password - Password associated with the username.
        url = "CUBRID"
        user = "public"
        passwd = ""

        if settings_dict['HOST'].startswith('/'):
            url += ':' + settings_dict['HOST']
        elif settings_dict['HOST']:
            url += ':' + settings_dict['HOST']
        else:
            url += ':localhost'
        if settings_dict['PORT']:
            url += ':' + settings_dict['PORT']
        if settings_dict['NAME']:
            url += ':' + settings_dict['NAME']
        if settings_dict['USER']:
            user = settings_dict['USER']
        if settings_dict['PASSWORD']:
            passwd = settings_dict['PASSWORD']

        url += ':::'

        con = Database.connect(url, user, passwd, charset='utf8')
        con.set_fetch_value_converter(django_fetch_value_converter)

        return con

    def _valid_connection(self):
        if self.connection is not None:
            return True
        return False

    def init_connection_state(self):
        pass

    def create_cursor(self):
        if not self._valid_connection():
            self.connection = self.get_new_connection(None)
            connection_created.send(sender=self.__class__, connection=self)

        cursor = CursorWrapper(self.connection.cursor())
        return cursor

    def _set_autocommit(self, autocommit):
        self.connection.autocommit = autocommit

    def is_usable(self):
        try:
            self.connection.ping()
        except Database.Error:
            return False
        else:
            return True

    def get_server_version(self):
        if not self.server_version:
            if not self._valid_connection():
                self.connection = self.get_new_connection(None)
            m = self.connection.server_version()
            if not m:
                raise Exception('Unable to determine CUBRID version')
            self.server_version = m
        return self.server_version

    def _savepoint_commit(self, sid):
        # CUBRID does not support "RELEASE SAVEPOINT xxx"
        pass

    if django.VERSION >= (1, 7) and django.VERSION < (1, 8):
        def schema_editor(self, *args, **kwargs):
            return DatabaseSchemaEditor(self, *args, **kwargs)


def django_fetch_value_converter(row, descriptor):
    # We need to convert naive datetime values to aware, if USE_TZ is true.
    if not settings.USE_TZ:
        return row

    index = 0
    for des in descriptor:
        if des[1] == FIELD_TYPE.DATETIME and timezone.is_naive(row[index]):
            row[index] = row[index].replace(tzinfo=timezone.utc)

        index = index + 1

    return row
