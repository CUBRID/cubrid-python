import sys
from CUBRIDdb import FIELD_TYPE


class BaseCursor(object):
    """
    A base for Cursor classes. Useful attributes:

    description::
        A tuple of DB API 7-tuples describing the columns in 
        the last executed query; see PEP-249 for details.

    arraysize::
        default number of rows fetchmany() will fetch
    """

    def __init__(self, conn):
        self.con = conn
        self._cs = conn.connection.cursor()
        self.arraysize = 1
        self.rowcount = -1
        self.description = None

        self.charset = conn.charset
        self._cs._set_charset_name(conn.charset)

    def __del__(self):
        try:
            if self._cs is not None:
                self.close()
        except AttributeError:   # self._cs not exists
            pass

    def __check_state(self):
        if self._cs is None:
            raise Exception("The cursor has been closed. No operation is allowed any more.")

    def close(self):
        """Close the cursor, and no further queries will be possible."""

        self.__check_state()
        self._cs.close()
        self._cs = None

    def _bind_params(self, args,set_type=None):
        self.__check_state()
        if type(args) not in (tuple, list):
            args = [args,]
        args = list(args)
        for i in range(len(args)):
            if args[i] is None:
                pass
            elif isinstance(args[i], bool):
                if args[i] == True:
                    args[i] = '1'
                else:
                    args[i] = '0'
            elif isinstance(args[i], tuple):
                 args[i] = args[i]
            else:
                # Python3.X dosen't support unicode keyword.
                try:
                    mytest = unicode
                except NameError:
                    if isinstance(args[i], str):
                        pass
                    elif isinstance(args[i], bytes):
                        args[i] = args[i].decode(self.charset)
                    else:
                        args[i] = str(args[i])
                else:
                    if isinstance(args[i], unicode):
                        args[i] = args[i].encode(self.charset)
                    else:
                        args[i] = str(args[i])

            if type(args[i]) != tuple:
                self._cs.bind_param(i+1, args[i])
            else:
                if set_type is None:
                    data_type = int(FIELD_TYPE.CHAR)
                else:
                    if type(set_type) != tuple:
                        set_type = [set_type,]
                    data_type = set_type[i]

                s = self.con.connection.set()
                s.imports(args[i], data_type)
                self._cs.bind_set(i+1, s)

    def execute(self, query, args=None, set_type=None):
        """
        Execute a query.

        query -- string, query to execute on server
        args -- optional sequence or mapping, parameters to use with query.

        Returns long integer rows affected, if any
        """
        self.__check_state()

        if not isinstance(query, (bytes, bytearray)):
            stmt = query.encode(self.charset)
        else:
            stmt = query

        if sys.version_info >= (3, 0):
            stmt = stmt.decode()

        self._cs.prepare(stmt)

        if args is not None:
            self._bind_params(args, set_type)

        r = self._cs.execute()
        self.rowcount = self._cs.rowcount
        self.description = self._cs.description
        return r

    def executemany(self, query, args):
        """
        Execute a multi-row query.

        query -- string, query to execute on server

        args -- Sequence of sequences or mappings, parameters to use with query

        Returns long integer rows affected, if any.

        This method improves performance on multiple-row INSERT and REPLACE.
        Otherwise it is equivalent to looping over args with execute().

        """

        self.__check_state()
        for p in args:
            self.execute(query, *(p,))

    def _fetch_row(self):
        self.__check_state()
        return self._cs.fetch_row(self._fetch_type)

    def fetchone(self):
        """
        Fetch the next row of a query result set, returning a single sequence, or None when no more data is available.
        """
        self.__check_state()

        row = self._fetch_row()

        if row and self.con.fetch_value_converter:
            # user defined value converter
            return self.con.fetch_value_converter(row, self._cs.description)

        return row

    def _fetch_many(self, size):
        self.__check_state()
        rlist = []
        i = 0
        while size < 0 or i < size:
            r = self.fetchone()
            if not r:
                break
            rlist.append(r)
            i = i+1
        return rlist

    def fetchmany(self, size=None):
        """
        Fetch the next set of rows of a query result, returning a sequence of sequences (e.g. a list of tuples). An empty sequence is returned when no more rows are available.
        The number of rows to fetch per call is specified by the parameter. If it is not given, the cursor's arraysize determines the number of rows to be fetched.
        The method should try to fetch as many rows as indicated by the size parameter. If this is not possible due to the specified number of rows not being available, fewer rows may be returned.
        """
        self.__check_state()
        if size is None:
            size = self.arraysize
        if size <= 0:
            return []
        return self._fetch_many(size)

    def fetchall(self):
        """
        Fetch all (remaining) rows of a query result, returning them as a sequence of sequences (e.g. a list of tuples).
        Note that the cursor's arraysize attribute can affect the performance of this operation.
        """
        self.__check_state()
        return self._fetch_many(-1)

    def setinputsizes(self, *args):
        """Does nothing, required by DB API."""
        pass

    def setoutputsizes(self, *args):
        """Does nothing, required by DB API."""
        pass

    def nextset(self):
        """Advance to the next result set.
        Returns None if there are no more result sets."""
        pass

    def callproc(self, procname, args=()):
        """
        Execute stored procedure procname with args

        procname -- string, name of procedure to execute on server

        args -- Sequence of parameters to use with procedure

        Returns the original args.

        """
        pass

    def __iter__(self):
        """
        Iteration over the result set which calls self.fetchone()
        and returns the next row.
        """
        self.__check_state()
        return self  # iter(self.fetchone, None)

    def next(self):
        """
        Return the next row from the currently executing SQL statement using the same semantics as fetchone().
        A StopIteration exception is raised when the result set is exhausted for Python versions 2.2 and later.
        """
        self.__check_state()
        return self.__next__()

    def __next__(self):
        self.__check_state()
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row


class CursorTupleRowsMixIn(object):

    _fetch_type = 0


class CursorDictTupleMixIn(object):

    _fetch_type = 1


class Cursor(CursorTupleRowsMixIn, BaseCursor):
    '''
    This is the standard Cursor class that returns rows as tuples
    and stores the result set in the client.
    '''


class DictCursor(CursorDictTupleMixIn, BaseCursor):
    '''
    This is a Cursor class that returns rows as dictionaries and
    stores the result set in the client.
    '''
