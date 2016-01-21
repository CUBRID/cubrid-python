from django.db.models.sql import compiler

class SQLCompiler(compiler.SQLCompiler):
    def as_sql(self, with_limits=True, with_col_aliases=False):
        """
        Creates the SQL for this query. Returns the SQL string and list of
        parameters.

        If 'with_limits' is False, any limit/offset information is not included
        in the query.
        """
        sql, params = super(SQLCompiler, self).as_sql(with_limits=False,
                               with_col_aliases=with_col_aliases)

        if with_limits:
            if self.query.high_mark is not None:
                row_count = self.query.high_mark - self.query.low_mark
                if self.query.low_mark:
                    sql = sql + ' LIMIT %d,%d' % (self.query.low_mark, row_count)
                else:
                    sql = sql + ' LIMIT %d' % (row_count)
            else:
                val = self.connection.ops.no_limit_value()
                if val:
                    if self.query.low_mark:
                        sql = sql + ' LIMIT %d,%d' % (self.query.low_mark, val)

        return sql, params

class SQLInsertCompiler(compiler.SQLInsertCompiler, SQLCompiler):
    pass

class SQLDeleteCompiler(compiler.SQLDeleteCompiler, SQLCompiler):
    pass

class SQLUpdateCompiler(compiler.SQLUpdateCompiler, SQLCompiler):
    pass

class SQLAggregateCompiler(compiler.SQLAggregateCompiler, SQLCompiler):
    pass

class SQLDateCompiler(compiler.SQLDateCompiler, SQLCompiler):
    pass
