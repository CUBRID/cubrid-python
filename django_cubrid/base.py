"""
Cubrid database backend for Django.

Requires CUBRIDdb: http://www.cubrid.org/wiki_apis
"""

import re
import sys
import django
import uuid
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
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.base.features import BaseDatabaseFeatures
from django.db.backends.base.operations import BaseDatabaseOperations

from django_cubrid.schema import DatabaseSchemaEditor
from django_cubrid.client import DatabaseClient
from django_cubrid.creation import DatabaseCreation
from django_cubrid.introspection import DatabaseIntrospection
from django_cubrid.validation import DatabaseValidation
from django_cubrid.operations import DatabaseOperations

from django.conf import settings
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.encoding import force_text


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

    can_introspect_small_integer_field = True

    can_return_id_from_insert = False

    can_rollback_ddl = True

    closed_cursor_error_class = django.db.utils.InterfaceError

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

    requires_literal_defaults = True

    supports_date_lookup_using_string = False

    # Can a fixture contain forward references? i.e., are
    # FK constraints checked at the end of transaction, or
    # at the end of each save operation?
    supports_forward_references = False

    supports_paramstyle_pyformat = False

    supports_regex_backreferencing = False

    supports_timezones = False

    uses_autocommit = True

    uses_savepoints = True


class DatabaseWrapper(BaseDatabaseWrapper):
    vendor = 'cubrid'
    # Operators taken from PosgreSQL implementation.
    # Check for differences between this syntax and CUBRID's.
    operators = {
        'exact': '= %s',
        'iexact': '= UPPER(%s)',
        'contains': 'LIKE %s',
        'icontains': 'LIKE UPPER(%s)',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE %s',
        'endswith': 'LIKE %s',
        'istartswith': 'LIKE UPPER(%s)',
        'iendswith': 'LIKE UPPER(%s)',
        'regex': 'REGEXP BINARY %s',
        'iregex': 'REGEXP %s',
    }
    # Patterns taken from other backend implementations.
    # The patterns below are used to generate SQL pattern lookup clauses when
    # the right-hand side of the lookup isn't a raw string (it might be an expression
    # or the result of a bilateral transformation).
    # In those cases, special characters for LIKE operators (e.g. \, *, _) should be
    # escaped on database side.
    #
    # Note: we use str.format() here for readability as '%' is used as a wildcard for
    # the LIKE operator.
    pattern_esc = r"REPLACE(REPLACE(REPLACE({}, '\\', '\\\\'), '%%', '\%%'), '_', '\_')"
    pattern_ops = {
        'contains': "LIKE '%%' || {} || '%%'",
        'icontains': "LIKE '%%' || UPPER({}) || '%%'",
        'startswith': "LIKE {} || '%%'",
        'istartswith': "LIKE UPPER({}) || '%%'",
        'endswith': "LIKE '%%' || {}",
        'iendswith': "LIKE '%%' || UPPER({})",
    }

    _data_types = {
        'AutoField': 'integer AUTO_INCREMENT',
        'BigAutoField': 'bigint AUTO_INCREMENT',
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
    client_class = DatabaseClient
    creation_class = DatabaseCreation
    features_class = DatabaseFeatures
    introspection_class = DatabaseIntrospection
    ops_class = DatabaseOperations
    validation_class = DatabaseValidation

    Database = Database

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        self.server_version = None


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

        return con

    def _valid_connection(self):
        if self.connection is not None:
            return True
        return False

    def init_connection_state(self):
        pass

    def create_cursor(self, name=None):
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
