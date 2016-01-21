"""
This module implements connections for CUBRIDdb. Presently there is
only one class: Connection. Others are unlikely. However, you might
want to make your own subclasses. In most cases, you will probably
override Connection.default_cursor with a non-standard Cursor class.

"""
from CUBRIDdb.cursors import *
import types, _cubrid


class Connection(object):
    """CUBRID Database Connection Object"""

    def __init__(self, *args, **kwargs):

        'Create a connecton to the database.'

        self._db = _cubrid.connect(*args, **kwargs)

    def __del__(self):
        pass

    def cursor(self, dictCursor = None):
        if dictCursor:
            cursorClass = DictCursor
        else:
            cursorClass = Cursor
        return cursorClass(self._db.cursor())
        
    def set_autocommit(self, value):
        if value:
            switch = 'TRUE'
        else:
            switch = 'FALSE'
        self._db.set_autocommit(switch)

    def get_autocommit(self):
        if self._db.autocommit == 'TRUE':
            return True
        else:
            return False
        
    autocommit = property(get_autocommit, set_autocommit, doc = "autocommit value for current Cubrid session")

    def commit(self):
        self._db.commit()

    def rollback(self):
        self._db.rollback()

    def close(self):
        self._db.close()

    def escape_string(self, buf):
        return self._db.escape_string(buf)
