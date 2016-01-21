import sys
import types

class Cursor(object):
    """
    A base for Cursor classes. Useful attributes:

    description::
        A tuple of DB API 7-tuples describing the columns in 
        the last executed query; see PEP-249 for details.

    arraysize::
        default number of rows fetchmany() will fetch
    """

    def __init__(self, conn):
        self._cs = conn.connection.cursor()
        self.arraysize = 1
        self.rowcount = -1
        self.description = None
        
        self.charset = conn.charset
        self._cs._set_charset_name(conn.charset)

    def __del__(self):
        self.close()

    def close(self):
        """Close the cursor. No further queries will be possible."""
        try:
            self._cs.close()
            self._cs = None
        except AttributeError:   # self._cs not exists
            pass

    def _bind_params(self, args):
        if type(args) not in (tuple, list):
            args = [args,]
        args = list(args)
        for i in range(len(args)):
            if args[i] == None:
                pass
            elif isinstance(args[i], bool):
                if args[i] == True:
                    args[i] = '1'
                else:
                    args[i] = '0'
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

            self._cs.bind_param(i+1, args[i])

    def execute(self, query, args=None):
        """
        Execute a query.
        
        query -- string, query to execute on server
        args -- optional sequence or mapping, parameters to use with query.

        Returns long integer rows affected, if any
        """
        self._cs.prepare(query)

        if args != None:
            self._bind_params(args)

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

        for p in args:
            self.execute(query, *(p,))

    
    def fetchone(self):
        return self._cs.fetch_row()

    def _fetch_many(self, size):
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
        if size == None:
            size = self.arraysize
        if size <= 0:
            return []
        return self._fetch_many(size)

    def fetchall(self):
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
        return self  # iter(self.fetchone, None)

    def next(self):
        return self.__next__()

    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row

