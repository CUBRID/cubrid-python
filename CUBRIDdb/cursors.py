import sys
from CUBRIDdb import FIELD_TYPE
from CUBRIDdb import InterfaceError
from datetime import date, time, datetime
from decimal import Decimal

INT_MIN = -2147483648
INT_MAX = +2147483647


def is_iterable(obj):
    """Returns whether an object is iterable"""
    if isinstance(obj, (bytes, str)):
        return False
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def bytes_to_binary_string(bytes_value):
    """Converts from bytes to a binary string containing only 1 or 0"""
    binary_string = ''
    for byte in bytes_value:
        binary_string += bin(byte)[2:].zfill(8)
    return binary_string


def get_set_element_type(iterable):
    """
    Determine the homogeneous data type of elements in an iterable.

    This function iterates over each element in the provided iterable and
    determines its data type based on predefined type categories. The categories
    include INT for integers, FLOAT for floating point numbers, MONETARY for Decimal,
    DATE for date objects, TIME for time objects, DATETIME for datetime objects,
    VARBIT for bytes, and VARCHAR for strings. These categories are represented by
    field_type attributes.

    The function checks the type of each element and assigns it to one of the
    predefined categories. If all elements are of the same type, it returns
    that type. If the iterable contains elements of different types, the function
    raises a TypeError.

    Parameters:
    iterable (iterable): The iterable to check the data types of its elements.

    Returns:
    FIELD_TYPE: The type category of the elements in the iterable if they are homogeneous.

    Raises:
    TypeError: If the iterable contains elements of different types.

    Example:
    >>> get_set_element_type([1, 2, 3])
    FIELD_TYPE.INT

    >>> get_set_element_type([1, 2.5, 'text'])
    TypeError: Iterable contains elements of different types: FIELD_TYPE.VARCHAR != FIELD_TYPE.INT
    """
    chosen_type = None
    for obj in iterable:
        if isinstance(obj, int):
            t = FIELD_TYPE.INT
        elif isinstance(obj, float):
            t = FIELD_TYPE.FLOAT
        elif isinstance(obj, Decimal):
            t = FIELD_TYPE.NUMERIC
        elif isinstance(obj, date):
            t = FIELD_TYPE.DATE
        elif isinstance(obj, time):
            t = FIELD_TYPE.TIME
        elif isinstance(obj, datetime):
            t = FIELD_TYPE.DATETIME
        elif isinstance(obj, bytes):
            t = FIELD_TYPE.VARBIT
        elif isinstance(obj, str):
            t = FIELD_TYPE.VARCHAR

        if chosen_type is None:
            chosen_type = t
        elif t is not chosen_type:
            raise TypeError(f"Iterable contains elements of different types: {t} != {chosen_type}")

    return chosen_type


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
        if self._cs is None:
            raise InterfaceError("Bad connection, invalid cursor")

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
            raise InterfaceError("The cursor has been closed. No operation is allowed any more.")

    def close(self):
        """Close the cursor, and no further queries will be possible."""

        self.__check_state()
        self._cs.close()
        self._cs = None

    def _prepare(self, query):
        if not isinstance(query, (bytes, bytearray)):
            stmt = query.encode(self.charset)
        else:
            stmt = query

        if sys.version_info >= (3, 0):
            stmt = stmt.decode()

        self._cs.prepare(stmt)

    def _bind_params(self, args, set_type=None):
        """
        Bind parameters to a command statement in a database cursor.

        This method processes the provided arguments (args) and binds them to a command
        statement associated with the database cursor. It handles different types of
        arguments including booleans, iterables, bytes, and other data types by converting
        or processing them appropriately before binding.

        For each argument in 'args':
        - If the argument is None, it is skipped.
        - If the argument is a boolean, it is converted to '1' or '0' string.
        - If the argument is an iterable (except strings and bytes), its element type
        is determined using 'get_set_element_type', and then it's bound as a set.
        - If the argument is a bytes object, it is converted to a binary string using
        'bytes_to_binstr' and bound with type 'field_type.VARBIT'.
        - For strings and other data types, the argument is bound directly or after
        converting to string, respectively.

        The method uses 'self.__check_state()' to ensure that the cursor is in an appropriate
        state for binding parameters.

        Parameters:
        args (any): The argument or a sequence of arguments to be bound to the command statement.
                    If 'args' is not an iterable, it is wrapped in a list.
        set_type (any): The type of the set argument. If not provided, the type of the set argument is determined by the elements of the set.
                        If provided, the type of the set argument is determined by the type of the set argument.

        Raises:
        TypeError: If the iterable 'args' contains elements of different types when binding
                an iterable argument.
        """

        self.__check_state()

        if not is_iterable(args):
            args = [args,]

        for i, arg in enumerate(args, start=1):
            if arg is None:
                continue

            if isinstance(arg, bool):
                self._cs.bind_param(i, 1 if arg else 0)
            elif isinstance(arg, int):
                if arg < INT_MIN or arg > INT_MAX:
                    self._cs.bind_param(i, arg, FIELD_TYPE.BIGINT)
                else:
                    self._cs.bind_param(i, arg)
            elif isinstance(arg, (float, str, date, time, datetime, Decimal)) or \
                 (sys.version_info < (3, 0) and isinstance(arg, unicode)):
                self._cs.bind_param(i, arg)
            elif isinstance(arg, bytes):
                self._cs.bind_param(i, arg, FIELD_TYPE.VARBIT)
            elif is_iterable(arg):
                element_type = None
                if set_type is not None:
                    if isinstance(set_type, (list, tuple)):
                        try:
                            element_type = set_type[i-1]
                        except IndexError:
                            pass
                    else:
                        element_type = set_type

                self._bind_set(i, arg, element_type)
            else:
                arg = str(arg)
                self._cs.bind_param(i, arg)

    def _bind_set(self, i, set_arg, element_type=None):
        """
        Bind a set argument and perform the appropriate adaptations
        for the set elements, to be accepted by _cubrid imports() and bind_set()
        """
        if element_type is None:
            element_type = get_set_element_type(set_arg)

        if element_type is None:
            element_type = FIELD_TYPE.VARCHAR

        s = self.con.connection.set()

        adapt = str
        if element_type == FIELD_TYPE.VARBIT:
            adapt = bytes_to_binary_string

        s.imports(tuple(map(adapt, set_arg)), element_type)
        self._cs.bind_set(i, s)

    def execute(self, query, args=None, set_type=None):
        """
        Execute a query.

        query -- string, query to execute on server
        args -- optional sequence or mapping, parameters to use with query.

        Returns long integer rows affected, if any
        """
        self.__check_state()

        self._prepare(query)

        if args is not None:
            self._bind_params(args, set_type)

        r = self._cs.execute()
        self.rowcount = self._cs.rowcount
        self.description = self._cs.description
        return r

    def executemany(self, query, args_list):
        """
        Execute a multi-row query.

        query -- string, query to execute on server

        args_list -- Sequence of sequences or mappings, parameters to use with query

        This method improves performance on multiple-row INSERT and REPLACE.
        Otherwise it is equivalent to looping over args with execute().
        """
        self.__check_state()

        self._prepare(query)

        for args in args_list:
            self._bind_params(args)
            self._cs.execute()

        self.rowcount = self._cs.rowcount
        self.description = self._cs.description

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
