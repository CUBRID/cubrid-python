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

    def lookup_cast(self, lookup_type, internal_type=None):
        lookup = '%s'

        # Use UPPER(x) for case-insensitive lookups.
        if lookup_type in ('iexact', 'icontains', 'istartswith', 'iendswith'):
            lookup = 'UPPER(%s)' % lookup

        return lookup

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

    def get_db_converters(self, expression):
        converters = super().get_db_converters(expression)
        internal_type = expression.output_field.get_internal_type()
        if internal_type in ["BooleanField", "NullBooleanField"]:
            converters.append(self.convert_booleanfield_value)
        return converters

    def convert_booleanfield_value(self, value, expression, connection):
        if value in (0, 1):
            value = bool(value)
        return value