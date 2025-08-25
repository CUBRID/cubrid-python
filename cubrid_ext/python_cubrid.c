#include "python_cubrid.h"
#include <fcntl.h>
#include "version.h"

/* Loading dynamic library need this header. */
#ifdef MS_WINDOWS
#include <windows.h>
#else
#include <dlfcn.h>

#ifndef O_BINARY
#define O_BINARY 0
#endif
#endif

#ifndef Py_TYPE
#define Py_TYPE(ob) (((PyObject*)(ob))->ob_type)
#endif

#ifdef MS_WINDOWS
#define write(fd, buf, size) _write(fd, buf, size)
#define read(fd, buf, size) _read(fd, buf, size)
#define unlink(file) _unlink(file)
#define open(file, flag, mode) _open(file, flag, mode)
#endif

#define CUBRID_CLOB 'C'
#define CUBRID_BLOB 'B'
#define CUBRID_LOB_BUF_SIZE 4096
#define CUBRID_ER_MSG_LEN 1024

static PyObject *_cubrid_error;
static PyObject *_cubrid_interface_error;
static PyObject *_cubrid_database_error;
static PyObject *_cubrid_data_error;
static PyObject *_cubrid_operational_error;
static PyObject *_cubrid_integrity_error;
static PyObject *_cubrid_internal_error;
static PyObject *_cubrid_programming_error;
static PyObject *_cubrid_not_supported_error;

static PyObject *_func_Decimal;

static struct _cubrid_isolation
{
  int level;
  char *isolation;
} cubrid_isolation[] =
{
  {
  TRAN_REP_CLASS_COMMIT_INSTANCE, "CUBRID_REP_CLASS_COMMIT_INSTANCE"},
  {
  TRAN_REP_CLASS_REP_INSTANCE, "CUBRID_REP_CLASS_REP_INSTANCE"},
  {
  TRAN_SERIALIZABLE, "CUBRID_SERIALIZABLE"},
  {
  0, "CUBRID_TRAN_UNKNOWN_ISOLATION"}
};

static struct _error_message
{
  int err;
  char *msg;
} cubrid_err_msgs[] =
{
  {
  CUBRID_ER_NO_MORE_MEMORY, "Memory allocation error"},
  {
  CUBRID_ER_INVALID_SQL_TYPE, "Invalid API call"},
  {
  CUBRID_ER_CANNOT_GET_COLUMN_INFO, "Cannot get column info"},
  {
  CUBRID_ER_INIT_ARRAY_FAIL, "Array initializing error"},
  {
  CUBRID_ER_UNKNOWN_TYPE, "Unknown column type"},
  {
  CUBRID_ER_INVALID_PARAM, "Invalid parameter"},
  {
  CUBRID_ER_INVALID_ARRAY_TYPE, "Invalid array type"},
  {
  CUBRID_ER_NOT_SUPPORTED_TYPE, "Invalid type"},
  {
  CUBRID_ER_OPEN_FILE, "File open error"},
  {
  CUBRID_ER_CREATE_TEMP_FILE, "Temporary file open error"},
  {
  CUBRID_ER_INVALID_CURSOR_POS, "Invalid cursor position"},
  {
  CUBRID_ER_SQL_UNPREPARE, "SQL statement not prepared"},
  {
  CUBRID_ER_PARAM_UNBIND, "Some parameter not binded"},
  {
  CUBRID_ER_SCHEMA_TYPE, "Invalid schema type"},
  {
  CUBRID_ER_READ_FILE, "Can not read file"},
  {
  CUBRID_ER_WRITE_FILE, "Can not write file"},
  {
  CUBRID_ER_LOB_NOT_EXIST, "LOB not exist"},
  {
  CUBRID_ER_INVALID_CURSOR,
      "The cursor has been closed. No operation is allowed any more."},
  {
  0, ""}
};

static void *libcascci = NULL;
typedef int (*CCI_GET_LAST_INSERT_ID) (int con, void *buff,
				       T_CCI_ERROR * err_buf);
static CCI_GET_LAST_INSERT_ID cci_get_last_insert_id_fp = NULL;


#if (PY_MAJOR_VERSION == 2 && PY_MINOR_VERSION <= 4)
typedef int Py_ssize_t;
#endif

static PyObject *
_cubrid_return_PyUnicode_FromString (const char *buf, Py_ssize_t size,
				     const char *encoding, const char *errors)
{
  return PyUnicode_Decode (buf, size, encoding, errors);
}

static PyObject *
_cubrid_return_PyString_FromString (const char *buf)
{
#if PY_MAJOR_VERSION >= 3
  return PyUnicode_FromString (buf);
#else
  return PyString_FromString (buf);
#endif
}

static PyObject *
_cubrid_return_PyInt_FromLong (long n)
{
#if PY_MAJOR_VERSION >= 3
  return PyLong_FromLong (n);
#else
  return PyInt_FromLong (n);
#endif
}

static PyObject *
_cubrid_return_PyLong_FromLongLong (long long n)
{
#if PY_MAJOR_VERSION >= 3 && PY_MINOR_VERSION >= 2
  return PyLong_FromLongLong (n);
#else
  return PyLong_FromLong (n);
#endif
}

static PyObject *
_cubrid_return_PyBool_FromLong (long n)
{
  return PyBool_FromLong (n);
}

static PyObject *
_cubrid_return_PyString_FromStringAndSize (const char *buf, Py_ssize_t size)
{
#if PY_MAJOR_VERSION >= 3
  return PyBytes_FromStringAndSize (buf, size);
#else
  return PyString_FromStringAndSize (buf, size);
#endif
}

static const char *
_cubrid_return_PyString_AsString (PyObject *buf)
{
#if PY_MAJOR_VERSION >= 3
  return PyUnicode_AsUTF8 (buf);
#else
  return PyString_AsString (buf);
#endif
}

static int
get_error_msg (int err_code, char *err_msg)
{
  int i;

  if (err_code > CCI_ER_END)
    {
      return cci_get_err_msg (err_code, err_msg, CUBRID_ER_MSG_LEN);
    }

  for (i = 0;; i++)
    {
      if (!cubrid_err_msgs[i].err)
	break;
      if (cubrid_err_msgs[i].err == err_code)
	{
	  snprintf (err_msg, CUBRID_ER_MSG_LEN, "%s", cubrid_err_msgs[i].msg);
	  return 0;
	}
    }
  return -1;
}

PyObject *
handle_error (int e, T_CCI_ERROR * error)
{
  PyObject *t, *exception = NULL;
  int err_code;
  char msg[CUBRID_ER_MSG_LEN] = { '0' };
  char err_msg[CUBRID_ER_MSG_LEN] = { '\0' }, *facility_msg;

  exception = _cubrid_error;

  if (e == CCI_ER_DBMS)
    {
      facility_msg = "DBMS";
      if (error)
	{
	  err_code = error->err_code;
	  switch (err_code)
	    {
	      /* programming error list */
	    case -493:
	      exception = _cubrid_programming_error;
	      break;

	      /* operational error list */
	    case -669:
	    case -673:
	    case -677:
	    case -1069:
	    case -1071:
	      exception = _cubrid_operational_error;
	      break;

	      /* integrity error list */
	    case -205:		/* not null constraint violation... */
	    case -494:		/* semantic error - not null constraint violation... */
	    case -631:
	    case -670:
	    case -886:
	    case -919:
	    case -920:
	    case -921:
	    case -922:
	    case -923:
	    case -924:
	    case -1063:
	    case -1067:
	      exception = _cubrid_integrity_error;
	      break;

	    default:
	      exception = _cubrid_database_error;
	      break;
	    }

	  snprintf (err_msg, CUBRID_ER_MSG_LEN, "%s", error->err_msg);
	}
      else
	{
	  err_code = 0;
	  snprintf (err_msg, CUBRID_ER_MSG_LEN, "Unknown DBMS Error");
	  exception = _cubrid_not_supported_error;
	}
    }
  else
    {
      exception = _cubrid_interface_error;

      if (get_error_msg (e, err_msg) < 0)
	{
	  snprintf (err_msg, CUBRID_ER_MSG_LEN, "Unknown Error");
	}
      err_code = e;

      if (e > CAS_ER_IS)
	{
	  facility_msg = "CAS";
	}
      else if (e > CCI_ER_END)
	{
	  facility_msg = "CCI";
	}
      else if (e > CUBRID_ER_END)
	{
	  facility_msg = "CLIENT";
	}
      else
	{
	  facility_msg = "UNKNOWN";
	}
    }

  snprintf (msg, CUBRID_ER_MSG_LEN, "ERROR: %s, %d, %s", facility_msg,
	    err_code, err_msg);

  if (!(t = PyTuple_New (2)))
    return NULL;

  PyTuple_SetItem (t, 0, _cubrid_return_PyInt_FromLong ((long) err_code));
  PyTuple_SetItem (t, 1, _cubrid_return_PyString_FromString (msg));

  PyErr_SetObject (exception, t);
  Py_DECREF (t);

  return NULL;
}

static char _cubrid_connect__doc__[] = "connect(url[,user[,password]])\n\
Establish the environment for connecting to your server by using\n\
connection information passed with a url string argument. If the\n\
HA feature is enabled in CUBRID, you must specify the connection\n\
information of the standby server, which is used for failover when\n\
failure occurs, in the url string argument of this function. If\n\
the user name and password is not given, then the \"PUBLIC\"\n\
connection will be made by default. Exclusive use of keyword\n\
parameters strongly recommended. Consult the CUBRID CCI\n\
documentation for more details.\n\
Parameters::\n\
  <url> ::= <host>:<db_name>:<db_user>:<db_password>:[?<properties>]\n\
      <properties> ::= <property> [&<property>]\n\
      <property> ::= althosts=<alternative_hosts> [&rctime=<time>]\n\
      <alternative_hosts> ::= <standby_broker1_host>:<port>\n\
             [,<standby_broker2_host>:<port>]\n\
      <host> := HOSTNAME | IP_ADDR\n\
      <time> := SECOND\n\
\n\
    host : A host name or IP address of the master database\n\
    db_name : A name of the database\n\
    db_user : A name of the database user\n\
    db_password : A database user password\n\
    alhosts: Specifies the broker information of the standby server,\n\
      which is used for failover when it is impossible to connect to\n\
      the active server. You can specify multiple brokers for failover,\n\
      and the connection to the brokers is attempted in the order listed\n\
      in alhosts\n\
    rctime : An interval between the attempts to connect to the active\n\
      broker in which failure occurred. After a failure occurs, the\n\
      system connects to the broker specified by althosts (failover),\n\
      terminates the transaction, and then attempts to connect to the\n\
      active broker of the master database at every rctime. The default\n\
      value is 600 seconds.\n\
\n\
Return a connection object.";

static PyObject *
_cubrid_connect (PyObject * self, PyObject * args, PyObject * kwargs)
{
  return PyObject_Call ((PyObject *) & _cubrid_ConnectionObject_type, args,
			kwargs);
}

static char _cubrid_escape_string__doc__[] = "escape_string()\n\
Escape special characters in a string for use in an SQL statement";

static PyObject *
_cubrid_escape_string (PyObject * self, PyObject * args, PyObject * kwargs)
{
  static char *kwList[] = { "escape_string", "no_backslash_escapes", NULL };
  int no_backslash_escapes = -1;
  char *unescape_string = NULL, *escape_string = NULL;
  Py_ssize_t len = -1;
  int res;
  T_CCI_ERROR error;

  PyObject *op;

  if (!PyArg_ParseTupleAndKeywords (args, kwargs,
				    "s#|i", kwList, &unescape_string, &len,
				    &no_backslash_escapes))
    {
      return NULL;
    }

  if (len < 0)
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
    }

  if (no_backslash_escapes == 0)
    {
      no_backslash_escapes = CCI_NO_BACKSLASH_ESCAPES_FALSE;
    }
  else
    {
      no_backslash_escapes = CCI_NO_BACKSLASH_ESCAPES_TRUE;
    }

  escape_string = (char *) malloc (len * 2 + 16);

  if (!escape_string)
    {
      return handle_error (CUBRID_ER_NO_MORE_MEMORY, NULL);
    }

  memset (escape_string, 0, len * 2 + 16);

  if ((res = cci_escape_string (no_backslash_escapes,
				escape_string, unescape_string, len,
				&error)) < 0)
    {
      free (escape_string);
      return handle_error (res, &error);
    }
#if PY_MAJOR_VERSION >= 3
  op = PyUnicode_FromStringAndSize (escape_string, res);
#else
  op = PyString_FromStringAndSize (escape_string, res);
#endif

  free (escape_string);

  return op;
}

static PyObject *
_cubrid_ConnectionObject_new (PyTypeObject * type, PyObject * args,
			      PyObject * kwargs)
{
  _cubrid_ConnectionObject *self;

  self = (_cubrid_ConnectionObject *) type->tp_alloc (type, 0);
  if (!self)
    {
      return NULL;
    }

  return (PyObject *) self;
}

static int
_cubrid_ConnectionObject_init (_cubrid_ConnectionObject * self,
			       PyObject * args, PyObject * kwargs)
{
  static char *kwList[] = { "url", "user", "passwd", NULL };
  char *url = NULL;
  char *user = "public";
  char *passwd = "";
  char buf[1024] = { '\0' };
  int con, res, level, autocommit, lock_timeout, max_string_len;
  T_CCI_ERROR error;

  if (!PyArg_ParseTupleAndKeywords (args, kwargs,
				    "s|ss", kwList, &url, &user, &passwd))
    {
      return -1;
    }

  self->handle = 0;
  self->url = NULL;
  self->user = NULL;
  self->passwd = NULL;

  snprintf (buf, 1024, "cci:%s", url);

  con = cci_connect_with_url_ex (buf, user, passwd, &error);
  if (con < 0)
    {
      handle_error (con, &error);
      return -1;
    }

  self->handle = con;
  res = cci_set_autocommit (self->handle, CCI_AUTOCOMMIT_TRUE);
  if (res < 0)
    {
      handle_error (res, &error);
      return -1;
    }
  self->url = strdup (url);
  self->user = strdup (user);

  res =
    cci_get_db_parameter (con, CCI_PARAM_LOCK_TIMEOUT, (void *) &lock_timeout,
			  &error);
  if (res < 0)
    {
      handle_error (res, &error);
      return -1;
    }

  self->lock_timeout = _cubrid_return_PyInt_FromLong (lock_timeout);

  res =
    cci_get_db_parameter (con, CCI_PARAM_MAX_STRING_LENGTH,
			  (void *) &max_string_len, &error);
  if (res < 0)
    {
      //handle_error (res, &error);
      //return -1;
      max_string_len = 0;
    }

  self->max_string_len = _cubrid_return_PyInt_FromLong (max_string_len);

  res =
    cci_get_db_parameter (con, CCI_PARAM_ISOLATION_LEVEL, (void *) &level,
			  &error);
  if (res < 0)
    {
      handle_error (res, &error);
      return -1;
    }

  res =
    cci_get_db_parameter (con, CCI_PARAM_AUTO_COMMIT, (void *) &autocommit,
			  &error);
  if (res < 0)
    {
      handle_error (res, &error);
      return -1;
    }

  if (level - 1 < TRAN_REP_CLASS_COMMIT_INSTANCE
      || level - 1 > TRAN_SERIALIZABLE)
    {
      level = TRAN_SERIALIZABLE + 1;
    }

  self->isolation_level =
    _cubrid_return_PyString_FromString (cubrid_isolation
					[level - 4].isolation);
  if (autocommit == CCI_AUTOCOMMIT_TRUE)
    {
      self->autocommit = _cubrid_return_PyBool_FromLong (1);
    }
  else
    {
      self->autocommit = _cubrid_return_PyBool_FromLong (0);
    }
  res = cci_end_tran (con, CCI_TRAN_COMMIT, &error);
  if (res < 0)
    {
      handle_error (res, &error);
      return -1;
    }

  return 0;
};

static char _cubrid_ConnectionObject_cursor__doc__[] = "cursor()\n\
Get the cursor class. Return a new Cursor Object.\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect(\"CUBRID:localhost:33000:demodb:::\", \"public\")\n\
  cur = con.cursor()\n\
  ...\n\
  other operations\n\
  ...\n\
  cur.close()\n\
  con.close()";

static PyObject *
_cubrid_ConnectionObject_cursor (_cubrid_ConnectionObject * self,
				 PyObject * args)
{
  PyObject *arg, *cursor;

  if (!self->handle)
    {
      handle_error (CCI_ER_CON_HANDLE, NULL);
      return NULL;
    }

  arg = PyTuple_New (1);
  if (!arg)
    {
      return NULL;
    }

  Py_INCREF (self);
  PyTuple_SET_ITEM (arg, 0, (PyObject *) self);

  cursor =
    PyObject_Call ((PyObject *) & _cubrid_CursorObject_type, arg, NULL);

  Py_DECREF (arg);

  return cursor;
}

static char _cubrid_ConnectionObject_lob__doc__[] = "lob()\n\
Create a large object. Return a new lob object.\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect(\"CUBRID:localhost:33000:demodb:::\", \"public\")\n\
  cur = con.cursor()\n\
  cur.prepare('insert into test_lob(image) values (?)')\n\
  lob = con.lob()\n\
  lob.imports('123.jpg')\n\
  cur.bind_lob(1, lob)\n\
  cur.execute()\n\
  lob.close()\n\
  cur.close()\n\
  con.close()";

static PyObject *
_cubrid_ConnectionObject_lob (_cubrid_ConnectionObject * self,
			      PyObject * args)
{
  PyObject *arg, *lob;

  if (!self->handle)
    {
      handle_error (CCI_ER_REQ_HANDLE, NULL);
      return NULL;
    }

  arg = PyTuple_New (1);
  if (!arg)
    {
      return NULL;
    }

  Py_INCREF (self);
  PyTuple_SET_ITEM (arg, 0, (PyObject *) self);

  lob = PyObject_Call ((PyObject *) & _cubrid_LobObject_type, arg, NULL);

  Py_DECREF (arg);

  return lob;
}

static char _cubrid_ConnectionObject_set__doc__[] =
  "Create a LIST/SET/MULTISET object. Return a new LIST/SET/MULTISET object.\n\
\n\
    Example::\n\
    con = _cubrid.connect('CUBRID:localhost:30000:demodb:dba::')\n\
    c = con.cursor()\n\
    s = con.set()\n\
    value = ('1','2')\n\
    s.imports(value ,CUBRIDdb.CCI_U_TYPE_INT)\n\
    c.prepare('''INSERT INTO set_tbl_int VALUES(?);''')\n\
    c.bind_set(1,s)\n\
    c.execute()\n\
    con.commit()\n\
    c.close()\n\
    con.close()";

static PyObject *
_cubrid_ConnectionObject_set (_cubrid_ConnectionObject * self,
			      PyObject * args)
{
  PyObject *arg, *set;

  if (!self->handle)
    {
      handle_error (CCI_ER_REQ_HANDLE, NULL);
      return NULL;
    }

  arg = PyTuple_New (1);
  if (!arg)
    {
      return NULL;
    }

  Py_INCREF (self);
  PyTuple_SET_ITEM (arg, 0, (PyObject *) self);

  set = PyObject_Call ((PyObject *) & _cubrid_SetObject_type, arg, NULL);

  Py_DECREF (arg);

  return set;
}

static PyObject *
_cubrid_ConnectionObject_end_tran (_cubrid_ConnectionObject * self, int type)
{
  int res;
  T_CCI_ERROR error;

  res = cci_end_tran (self->handle, type, &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_ConnectionObject_commit__doc__[] = "commit()\n\
Commit any pending transaction to the database.\n\
CUBRID can be set to perform automatic commits at each operation,\n\
set_autocommit() and set_isolation_level().\n";

static PyObject *
_cubrid_ConnectionObject_commit (_cubrid_ConnectionObject * self,
				 PyObject * args)
{
  if (!PyArg_ParseTuple (args, ""))
    {
      return NULL;
    }

  return _cubrid_ConnectionObject_end_tran (self, CCI_TRAN_COMMIT);
}

static char _cubrid_ConnectionObject_rollback__doc__[] = "rollback()\n\
Roll back the start of any pending transaction to database. Closing\n\
a connection without committing the changes first will cause an\n\
implicit rollback to be performed.";

static PyObject *
_cubrid_ConnectionObject_rollback (_cubrid_ConnectionObject * self,
				   PyObject * args)
{
  if (!PyArg_ParseTuple (args, ""))
    {
      return NULL;
    }

  return _cubrid_ConnectionObject_end_tran (self, CCI_TRAN_ROLLBACK);
}

static char _cubrid_ConnectionObject_server_version__doc__[] =
  "server_version()\n\
This function returns a string that represents the CUBRID server version.\n\
Returns a string that represents the server version number.\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect(\"CUBRID:localhost:33000:demodb:::\", \"public\")\n\
  print con.server_version()\n\
  con.close()";

static PyObject *
_cubrid_ConnectionObject_server_version (_cubrid_ConnectionObject * self,
					 PyObject * args)
{
  int res;
  char db_ver[16];

  if (!PyArg_ParseTuple (args, ""))
    {
      return NULL;
    }

  res = cci_get_db_version (self->handle, db_ver, sizeof (db_ver));
  if (res < 0)
    {
      return handle_error (res, NULL);
    }

  return _cubrid_return_PyString_FromString (db_ver);
}

static char _cubrid_ConnectionObject_client_version__doc__[] =
  "client_version()\n\
This function returns a string that represents the Python driver version.\n\
\n\
Return a string that represents the CUBRID Python driver version\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect(\"CUBRID:localhost:33000:demodb:::\", \"public\")\n\
  print con.client_version()\n\
  con.close()";

static PyObject *
_cubrid_ConnectionObject_client_version (_cubrid_ConnectionObject * self,
					 PyObject * args)
{
  if (!PyArg_ParseTuple (args, ""))
    {
      return NULL;
    }

  // Return the Python driver version instead of CCI version
  return _cubrid_return_PyString_FromString (_CUBRID_VERSION_);
}

static char _cubrid_ConnectionObject_set_autocommit__doc__[] =
  "set_autocommit(mode)\n\
This function set the autocommit mode.\n\
It can enable/disable the transaction management.\n\
\n\
mode: bool. It will be True/False\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect(\"CUBRID:localhost:33000:demodb:::\", \"public\")\n\
  con.set_autocommit(True)\n\
  print con.autocommit\n\
  con.close()";

static PyObject *
_cubrid_ConnectionObject_set_autocommit (_cubrid_ConnectionObject * self,
					 PyObject * args)
{
  PyObject *autocommit_obj;
  int mode;
  int res;

  if (!PyArg_ParseTuple (args, "O!", &PyBool_Type, &autocommit_obj))
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
    }
  mode = PyObject_IsTrue (autocommit_obj);
  if (mode != 0)
    {
      res = cci_set_autocommit (self->handle, CCI_AUTOCOMMIT_TRUE);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}

      self->autocommit = _cubrid_return_PyBool_FromLong (1);
    }
  else
    {
      res = cci_set_autocommit (self->handle, CCI_AUTOCOMMIT_FALSE);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}

      self->autocommit = _cubrid_return_PyBool_FromLong (0);
    }

  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_ConnectionObject_set_isolation_level__doc__[] =
  "set_isolation(isolation_level)\n\
Set the transaction isolation level for the current session.\n\
The level defines the different phenomena can happen in the\n\
database between concurrent transactions.\n\
\n\
isolation_level maybe::\n\
  CUBRID_REP_CLASS_COMMIT_INSTANCE\n\
  CUBRID_REP_CLASS_REP_INSTANCE\n\
  CUBRID_SERIALIZABLE\n\
\n\
Example::\n\
  import _cubrid\n\
  form _cubrid import *\n\
  con = _cubrid.connect(\"CUBRID:localhost:33000:demodb:::\", \"public\")\n\
  con.set_isolation_level(CUBRID_REP_CLASS_REP_INSTANCE)\n\
  print con.isolation_level\n\
  con.close()";

static PyObject *
_cubrid_ConnectionObject_set_isolation_level (_cubrid_ConnectionObject * self,
					      PyObject * args)
{
  int level, res;
  T_CCI_ERROR error;

  if (!PyArg_ParseTuple (args, "i", &level))
    {
      return NULL;
    }

  res = cci_set_isolation_level (self->handle, level, &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  self->isolation_level =
    _cubrid_return_PyString_FromString (cubrid_isolation
					[level - 4].isolation);

  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_ConnectionObject_ping__doc__[] = "ping()\n\
Checks whether or not the connection to the server is working. This \n\
function can be used by clients that remain idle for a long while,\n\
to check whether or not the server has closed the connection and reconnect\n\
if necessary.\n\
\n\
Return values::\n\
  1 when connected\n\
  0 when not connect\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect(\"CUBRID:localhost:33000:demodb:::\", \"public\")\n\
  print con.ping()\n\
  con.close()";

static PyObject *
_cubrid_ConnectionObject_ping (_cubrid_ConnectionObject * self,
			       PyObject * args)
{
  int res;
  T_CCI_ERROR error;
  char *query = "select 1+1 from db_root";
  int req_handle = 0, result = 0, ind = 0;
  int connected = 0;

  if (!PyArg_ParseTuple (args, ""))
    {
      return NULL;
    }

  res = cci_prepare (self->handle, query, 0, &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  req_handle = res;

  res = cci_execute (req_handle, 0, 0, &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  while (1)
    {
      res = cci_cursor (req_handle, 1, CCI_CURSOR_CURRENT, &error);
      if (res == CCI_ER_NO_MORE_DATA)
	{
	  break;
	}
      if (res < 0)
	{
	  return handle_error (res, &error);
	}

      res = cci_fetch (req_handle, &error);
      if (res < 0)
	{
	  return handle_error (res, &error);
	}

      res = cci_get_data (req_handle, 1, CCI_A_TYPE_INT, &result, &ind);
      if (res < 0)
	{
	  return handle_error (res, &error);
	}

      if (result == 2)
	{
	  connected = 1;
	}
    }

  cci_close_req_handle (req_handle);
  return _cubrid_return_PyInt_FromLong (connected);
}

static char *
_cubrid_dup_buf (char *src_buf, int size)
{
  int len = 0;
  char *temp_buf = NULL;

  if (src_buf != NULL)
    {
      len = strlen (src_buf);
    }
  else
    {
      len = size;
    }
  if (len <= 0)
    {
      return NULL;
    }
  temp_buf = (char *) malloc (len + 1);
  if (NULL == temp_buf)
    {
      return NULL;
    }
  memset (temp_buf, 0, len + 1);
  if (NULL != src_buf)
    memcpy (temp_buf, src_buf, len);

  return temp_buf;
}

static char *
_cubrid_get_data_buf (int type, int num)
{
  switch (type)
    {
    case CCI_U_TYPE_BIT:
    case CCI_U_TYPE_VARBIT:
      return _cubrid_dup_buf (NULL, sizeof (T_CCI_BIT) * (num + 1));
    default:
      return _cubrid_dup_buf (NULL, sizeof (void *) * (num + 1));
    }
}

static char _cubrid_ConnectionObject_batch_execute__doc__[] = "batch_execute()\n\
 The api can execute more than one sql statement in the same time\n\
\n\
Return values::\n\
  Tuple: ({'err_no': 0, 'err_msg': 'success'},)\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect(\"CUBRID:localhost:33000:demodb:::\", \"public\")\n\
  sql = (\"insert into test value('1');\", \"insert into test value('2');\")\n\
  err = con.batch_execute(sql)\n\
  con.close()";


static PyObject *
_cubrid_ConnectionObject_batch_execute (_cubrid_ConnectionObject * self,
			       PyObject * args)
{
  int count, err_code, i, n_executed;
  char **sql;
  T_CCI_QUERY_RESULT *result;
  T_CCI_ERROR cci_error;
  PyObject *p_tube;
  PyObject *p_value;
  PyDictObject *p_result;
  PyTupleObject *p_batch_result;
  
  if (!PyArg_ParseTuple (args, "O", &p_tube))
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
    }
  if (!PyTuple_Check (p_tube))    
    {      
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);    
    }  
  count = PyTuple_GET_SIZE (p_tube);
  if (count <= 0)
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);  
    }
  sql = (char **) _cubrid_get_data_buf (CCI_U_TYPE_CHAR, count + 1);
  if (NULL == sql)
    {
      return handle_error (CUBRID_ER_NO_MORE_MEMORY, NULL);
    }
  for (i = 0; i < count; ++i)
    {
      p_value = PyTuple_GET_ITEM (p_tube, i);
      sql[i] = _cubrid_return_PyString_AsString (p_value);
    }
  n_executed = cci_execute_batch (self->handle, count, sql, &result, &cci_error);
  if (n_executed < 0)
    {
      free(sql);
      return handle_error (n_executed, &cci_error);
    }
  free(sql);
  p_batch_result = PyTuple_New(n_executed);
  for (i = 0; i < n_executed; ++i)
    {
      p_result = PyDict_New();    
      err_code = PyDict_SetItemString(
        p_result, "err_no", _cubrid_return_PyInt_FromLong(result[i].err_no));
      if (result[i].err_no >= 0)
        {
          PyDict_SetItemString(
            p_result, "err_msg", _cubrid_return_PyString_FromString("success"));        
        }
      else
        {
          PyDict_SetItemString(
            p_result, "err_msg", _cubrid_return_PyString_FromString(result[i].err_msg));
        }

      PyTuple_SetItem(p_batch_result, i, p_result);
    }
  
  err_code = cci_query_result_free (result, n_executed);    
  if (err_code < 0)    
    {     
      return handle_error (err_code, NULL);  
    } 
  return p_batch_result;
}


static char _cubrid_ConnectionObject_last_insert_id__doc__[] = "insert_id()\n\
This function returns the value with the IDs generated or the\n\
AUTO_INCREMENT columns that were updated by the previous INSERT\n\
query. It returns None if the previous query does not generate\n\
new rows.\n\
\n\
Returns the value with the IDs generated for the AUTO_INCREMENT\n\
columns that were updated by the previous INSERT query.\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect(\"CUBRID:localhost:33000:demodb:::\", \"public\")\n\
  cur = con.curosr()\n\
  cur.prepare(\"create table test_cubrid(id NUMERIC\n\
          AUTO_INCREMENT(10300, 1), name VARCHAR(50))\")\n\
  cur.execute()\n\
  cur.prepare(\"insert into test_cubrid(name) values ('Lily')\")\n\
  cur.execute()\n\
  print con.insert_id()\n\
  cur.close()\n\
  con.close()";

static PyObject *
_cubrid_ConnectionObject_last_insert_id (_cubrid_ConnectionObject * self,
					 PyObject * args)
{
  char *name = NULL;
  char ret[1024] = { '\0' };
  int res;
  T_CCI_ERROR error;

  /* cci_last_id set last_id as allocated string */
  res = cci_get_last_insert_id (self->handle, &name, &error);

  if (res < 0)
    {
      return handle_error (res, &error);
    }

  if (!name)
    {
      Py_INCREF (Py_None);
      return Py_None;
    }
  else
    {
      strncpy (ret, name, sizeof (ret) - 1);
    }

  return PyLong_FromString (ret, NULL, 10);
}

static PyObject *
_cubrid_ConnectionObject_schema_to_pyvalue (_cubrid_ConnectionObject * self,
					    int request, int type, int index)
{
  int res, ind;
  PyObject *val, *tmpval;
  char *buffer;
  int num;

  switch (type)
    {
    case CCI_U_TYPE_INT:
    case CCI_U_TYPE_SHORT:
      res = cci_get_data (request, index, CCI_A_TYPE_INT, &num, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
      if (ind < 0)
	{
	  Py_INCREF (Py_None);
	  return Py_None;
	}
      else
	{
	  val = _cubrid_return_PyInt_FromLong (num);
	}
      break;
    default:
      res = cci_get_data (request, index, CCI_A_TYPE_STR, &buffer, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
      if (ind < 0)
	{
	  Py_INCREF (Py_None);
	  return Py_None;
	}
      else
	{
	  val = _cubrid_return_PyString_FromString (buffer);
	}
      break;
    }

  return val;
}

static PyObject *
_cubrid_ConnectionObject_fetch_schema (_cubrid_ConnectionObject * self,
				       int request, T_CCI_COL_INFO * col_info,
				       int col_count)
{
  int type;
  PyObject *val, *row;
  int i;

  row = PyList_New (col_count);

  for (i = 0; i < col_count; i++)
    {
      type = CCI_GET_RESULT_INFO_TYPE (col_info, i + 1);
      val =
	_cubrid_ConnectionObject_schema_to_pyvalue (self, request, type,
						    i + 1);

      PyList_SetItem (row, i, val);
    }

  return row;
}

static char _cubrid_ConnectionObject_schema_info__doc__[] =
  "schema_info(schema_type[,class_name[,attr_name]])\n\
This function is used to get the requested schema information from\n\
database. You have to designate class_name, if you want to get\n\
information on certain class, attr_name, if you want to get\n\
information on certain attribute (can be used only with\n\
CUBRID_SCH_COLUMN_PRIVILEGE).\n\
The following tables shows types of schema and the column structure\n\
of the result::\n\
 ----------------------------------------------------------------------\n\
 Schema                      Col Number  Col Name        Value\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_TABLE                1       NAME\n\
                                 2       TYPE            0:system table\n\
                                                         1:viem\n\
                                                         2:table\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_VIEW                 1       NAME\n\
                                 2       TYPE            1:view\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_QUERY_SPEC           1       QUERY_SPEC\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_ATTRIBUTE            1       ATTR_NAME\n\
 CUBRID_SCH_TABLE_ATTRIBUTE      2       DOMAIN\n\
                                 3       SCALE\n\
                                 4       PRECISION\n\
                                 5       INDEXED         1:indexed\n\
                                 6       NOT NULL        1:not null\n\
                                 7       SHARED          1:shared\n\
                                 8       UNIQUE          1:uniqe\n\
                                 9       DEFAULT\n\
                                 10      ATTR_ORDER      1:base\n\
                                 11      TABLE_NAME\n\
                                 12      SOURCE_CLASS\n\
                                 13      IS_KEY          1:key\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_METHOD               1       NAME\n\
 CUBRID_SCH_TABLE_METHOD         2       RET_DOMAIN\n\
                                 3       ARG_DOMAIN\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_METHOD_FILE          1       METHOD_FILE\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_SUPERTABLE           1       TABLE_NAME\n\
 CUBRID_SCH_SUBTABLE             2       TYPE            0:system table\n\
 CUBRID_SCH_DIRECT_SUPER_TABLE                           1:view\n\
                                                         2:table\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_CONSTRAINT           1       TYPE            0:unique\n\
                                                         1:index\n\
                                                         2:reverse unique\n\
                                                         3:reverse index\n\
                                 2       NAME\n\
                                 3       ATTR_NAME\n\
                                 4       NUM_PAGES\n\
                                 5       NUM_KEYS\n\
                                 6       PRIMARY_KEY     1:primary key\n\
                                 7       KEY_ORDER       1:base\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_TRIGGER              1       NAME\n\
                                 2       STATUS\n\
                                 3       EVENT\n\
                                 4       TARGET_TABLE\n\
                                 5       TARGET_ATTR\n\
                                 6       ACTION_TIME\n\
                                 7       ACTION\n\
                                 8       PRIORITY\n\
                                 9       CONDITION_TIME\n\
                                 10      CONDITION\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_TABLE_PRIVILEGE      1       TABLE_NAME\n\
                                 2       PRIVILEGE\n\
                                 3       GRANTABLE\n\
 ----------------------------------------------------------------------\n\
 CCI_SCH_ATTR_PRIVILEGE          1       ATTR_NAME\n\
                                 2       PRIVILEGE\n\
                                 3       GRANTABLE\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_PRIMARY_KEY          1       TABLE_NAME\n\
                                 2       ATTR_NAME\n\
                                 3       KEY_SEQ         1:base\n\
                                 4       KEY_NAME\n\
 ----------------------------------------------------------------------\n\
 CUBRID_SCH_IMPORTED_KEYS        1       PKTABLE_NAME\n\
 CUBRID_SCH_EXPORTED_KEYS        2       PKCOLUMN_NAME\n\
 CUBRID_SCH_CROSS_REFERENCE      3       FKTABLE_NAME    1:base\n\
                                 4       FKCOLUMN_NAME\n\
                                 5       KEY_SEQ\n\
                                 6       UPDATE_ACTION   0:cascade\n\
                                                         1:restrict\n\
                                                         2:no action\n\
                                                         3:set null\n\
                                 7       DELETE_ACTION   0:cascade\n\
                                                         1:restrict\n\
                                                         2:no action\n\
                                                         3:set null\n\
                                 8       FK_NAME\n\
                                 9       PK_NAME\n\
 ----------------------------------------------------------------------\n\
\n\
Parameters::\n\
  schema_type: schema type in the table\n\
  table_name: string, table you want to know the schema of\n\
  attr_name: string, attribute you want to know the schema of\n\
\n\
Return values::\n\
  A tuple that contains the schema information when success\n\
  None when fail\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
  print con.schema_info(_cubrid.CUBRID_SCH_TABLE, 'test_cubrid')\n\
  con.close()";

static PyObject *
_cubrid_ConnectionObject_schema_info (_cubrid_ConnectionObject * self,
				      PyObject * args)
{
  int flag = 0, request, res, type;
  T_CCI_ERROR error;
  char *class_name = NULL;
  char *attr_name = NULL;
  PyObject *result;
  T_CCI_COL_INFO *col_info;
  T_CCI_CUBRID_STMT sql_type;
  int col_count;

  if (!PyArg_ParseTuple (args, "is|s", &type, &class_name, &attr_name))
    {
      return NULL;
    }

  if (type > CCI_SCH_LAST || type < CCI_SCH_FIRST)
    {
      return handle_error (CUBRID_ER_SCHEMA_TYPE, NULL);
    }

  switch (type)
    {
    case CCI_SCH_CLASS:
    case CCI_SCH_VCLASS:
      flag = CCI_CLASS_NAME_PATTERN_MATCH;
      break;
    case CCI_SCH_ATTRIBUTE:
    case CCI_SCH_CLASS_ATTRIBUTE:
      flag = CCI_ATTR_NAME_PATTERN_MATCH;
      break;
    default:
      flag = 0;
      break;
    }

  res =
    cci_schema_info (self->handle, type, class_name, attr_name, (char) flag,
		     &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  request = res;

  col_info = cci_get_result_info (request, &sql_type, &col_count);
  if (!col_info)
    {
      return handle_error (CUBRID_ER_CANNOT_GET_COLUMN_INFO, NULL);
    }

  res = cci_cursor (request, 1, CCI_CURSOR_CURRENT, &error);
  if (res == CCI_ER_NO_MORE_DATA)
    {
      Py_INCREF (Py_None);
      return Py_None;
    }
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  res = cci_fetch (request, &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  result =
    _cubrid_ConnectionObject_fetch_schema (self, request, col_info,
					   col_count);

  res = cci_cursor (request, 1, CCI_CURSOR_CURRENT, &error);
  if (res < 0 && res != CCI_ER_NO_MORE_DATA)
    {
      return handle_error (res, &error);
    }

  cci_close_req_handle (request);

  return result;
}

static char _cubrid_ConnectionObject_escape_string__doc__[] =
  "escape_string()\n\
Escape special characters in a string for use in an SQL statement";

static PyObject *
_cubrid_ConnectionObject_escape_string (_cubrid_ConnectionObject * self,
					PyObject * args)
{
  char *unescape_string = NULL, *escape_string = NULL;
  Py_ssize_t len = -1;
  int res;
  PyObject *op;
  T_CCI_ERROR error;

  if (!PyArg_ParseTuple (args, "s#", &unescape_string, &len))
    {
      return NULL;
    }

  if (len < 0)
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
    }

  escape_string = (char *) malloc (len * 2 + 16);

  if (!escape_string)
    {
      return handle_error (CUBRID_ER_NO_MORE_MEMORY, NULL);
    }

  memset (escape_string, 0, len * 2 + 16);

  if ((res = cci_escape_string (self->handle,
				escape_string, unescape_string, len,
				&error)) < 0)
    {
      free (escape_string);
      return handle_error (res, &error);
    }

#if PY_MAJOR_VERSION >= 3
  op = PyUnicode_FromStringAndSize (escape_string, res);
#else
  op = PyString_FromStringAndSize (escape_string, res);
#endif

  free (escape_string);

  return op;
}

static char _cubrid_ConnectionObject_close__doc__[] = "close()\n\
Close the connection now.";

static PyObject *
_cubrid_ConnectionObject_close (_cubrid_ConnectionObject * self,
				PyObject * args)
{
  T_CCI_ERROR error;
  int err_code;
  if(self->handle <= 0)
    {
      Py_INCREF (Py_None);
      return Py_None;
    }
  err_code = cci_disconnect (self->handle, &error);
  if (err_code < 0)
    {
      return handle_error (err_code, &error);
    }
  self->handle = 0;
  if (self->url)
    {
      free (self->url);
      self->url = NULL;
    }

  if (self->user)
    {
      free (self->user);
      self->user = NULL;
    }

  if (self->isolation_level)
    {
      Py_DECREF (self->isolation_level);
      self->isolation_level = NULL;
    }

  if (self->autocommit)
    {
      Py_DECREF (self->autocommit);
      self->autocommit = NULL;
    }

  Py_INCREF (Py_None);
  return Py_None;
}

static void
_cubrid_ConnectionObject_dealloc (_cubrid_ConnectionObject * self)
{
  PyObject *o;

  o = _cubrid_ConnectionObject_close (self, NULL);
  Py_XDECREF (o);

  Py_TYPE (self)->tp_free ((PyObject *) self);
}

static PyObject *
_cubrid_CursorObject_new (PyTypeObject * type, PyObject * args,
			  PyObject * kwargs)
{
  _cubrid_CursorObject *self;

  self = (_cubrid_CursorObject *) type->tp_alloc (type, 0);
  if (!self)
    {
      return NULL;
    }

  return (PyObject *) self;
}

static int
_cubrid_CursorObject_init (_cubrid_CursorObject * self, PyObject * args,
			   PyObject * kwargs)
{
  _cubrid_ConnectionObject *conn;

  if (!PyArg_ParseTuple (args, "O!", &_cubrid_ConnectionObject_type, &conn))
    {
      return -1;
    }

  Py_INCREF (conn);

  self->state = CURSOR_STATE_OPENED;
  self->handle = 0;
  self->connection = conn->handle;
  Py_INCREF (Py_None);
  self->description = Py_None;
  self->bind_num = -1;
  self->col_count = -1;
  self->sql_type = 0;
  self->row_count = -1;
  self->cursor_pos = 0;

  memset (self->charset, 0, sizeof (self->charset));
  strncpy(self->charset, "utf8", sizeof (self->charset) - 1);

  return 0;
}

static char _cubrid_CursorObject__set_charset_name__doc__[] =
  "Only used internally. This function should not be used by user.";

static PyObject *
_cubrid_CursorObject__set_charset_name (_cubrid_CursorObject * self,
					PyObject * args)
{
  char *charset = NULL;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, "s", &charset))
    {
      return NULL;
    }

  if (charset != NULL && *charset != '\0')
    {
      snprintf (self->charset, sizeof (self->charset), "%s", charset);
    }

  Py_INCREF (Py_None);
  return Py_None;

}


static void
_cubrid_CursorObject_reset (_cubrid_CursorObject * self)
{
  if (self->handle)
    {
      cci_close_req_handle (self->handle);
      self->handle = 0;

      if (self->description)
	{
	  Py_DECREF (self->description);
	  self->description = NULL;
	}
      self->bind_num = -1;
      self->col_count = -1;
      self->sql_type = 0;
      self->row_count = -1;
      self->cursor_pos = 0;
    }
}

static char _cubrid_CursorObject_prepare__doc__[] = "prepare(sql)\n\
This function creates a prepared statement. A prepared statement is a\n\
server-side object that can be used to optimize performance. You can \n\
use this statement effectively to execute repeatedly or to process \n\
long data. Only a single statement can be used. The SQL statement can \n\
contain zero or more question mark (?) parameter markers for which real \n\
values will be substituted when the statement is executed. Add a \n\
parameter when you bind a value in the VALUES clause of INSERT statement \n\
or in the WHERE clause.\n\
\n\
sql: string, the sql statement you want to execute.";

static PyObject *
_cubrid_CursorObject_prepare (_cubrid_CursorObject * self, PyObject * args)
{
  int res;
  T_CCI_ERROR error;
  char *stmt = "";

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, "s", &stmt))
    {
      return NULL;
    }

  _cubrid_CursorObject_reset (self);
  res = cci_prepare (self->connection, stmt, 0, &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }
  self->handle = res;
  self->bind_num = cci_get_bind_num (res);
  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_CursorObject_bind_param__doc__[] =
  "bind_param(index, value, bind_type=None)\n\
This function is used to bind a value to a prepared statement variable. It supports\n\
binding of various Python data types, including int, float, str (encoded as bytes),\n\
date, time, and datetime objects, in addition to handling BLOB/CLOB types.\n\
\n\
In a CUBRID shard environment, specifying the bind_type is recommended for\n\
optimal performance and compatibility.\n\
\n\
Supported Python types for binding include:\n\
  - int (mapped to CUBRID INT or BIGINT based on size)\n\
  - float (mapped to CUBRID FLOAT or DOUBLE)\n\
  - decimal.Decimal (mapped to CUBRID NUMERIC)\n\
  - str (encoded as UTF-8 bytes, mapped to CUBRID CHAR or STRING types)\n\
  - bytes (directly mapped to CUBRID BIT or BIT VARYING based on bind_type)\n\
  - date (mapped to CUBRID DATE)\n\
  - time (mapped to CUBRID TIME)\n\
  - datetime (mapped to CUBRID TIMESTAMP)\n\
\n\
The function automatically determines the appropriate CUBRID data type based on\n\
the Python type of the value argument, unless the bind_type is explicitly specified.\n\
\n\
Parameters:\n\
  index (int): The index of the variable in the prepared statement to bind the value to.\n\
  value: The Python object to bind to the variable. Supported types include int, float,\n\
         decimal.Decimal, str, bytes, date, time, and datetime.\n\
  bind_type (optional): The CUBRID column type to bind the value as. This parameter\n\
                        is optional and is recommended for use in specific scenarios\n\
                        where the automatic type resolution needs to be overridden.\n\
\n\
Returns:\n\
  None: This function does not return a value.\n\
\n\
Raises:\n\
  ValueError: If an unsupported type is passed or if the function encounters\n\
              an error while binding the value.\n";

static PyObject *
_cubrid_CursorObject_bind_param (_cubrid_CursorObject * self, PyObject * args)
{
  int res, index = -1;
  PyObject *temp_bytes = NULL;
  PyObject *temp_str = NULL;
  PyObject *value_obj = NULL;
  Py_buffer value_view = {NULL, NULL};
  int bind_type = 0;
  void *bind_value;
  int u_type = CCI_U_TYPE_CHAR;
  int a_type = CCI_A_TYPE_STR;
  long long_value;
  int64_t int64_value;
  double double_value;
  char *str_value = NULL;
  T_CCI_DATE date_value;
  T_CCI_BIT bit_value;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!self->handle)
    {
      return handle_error (CUBRID_ER_SQL_UNPREPARE, NULL);
    }

  if (!PyArg_ParseTuple(args, "iO|i", &index, &value_obj, &bind_type))
    {
      return NULL;
    }

  if (bind_type != 0)
    {
      u_type = bind_type;
    }

  #if PY_MAJOR_VERSION >= 3
  if (PyLong_Check(value_obj))
  #else
  if (PyInt_Check(value_obj) || PyLong_Check(value_obj))
  #endif
    {
      if (u_type == CCI_U_TYPE_BIGINT)
        {
          int64_value = PyLong_AsLongLong(value_obj);
          if (int64_value == -1 && PyErr_Occurred())
            {
              PyErr_SetString(PyExc_OverflowError, "Python int out of range of C int64_t");
              return NULL;
            }
          bind_value = &int64_value;
          a_type = CCI_A_TYPE_BIGINT;
        }
      else
        {
          long_value = PyLong_AsLong(value_obj);
          if (long_value == -1 && PyErr_Occurred())
            {
              PyErr_SetString(PyExc_OverflowError, "Python int out of range of C long");
              return NULL;
            }
          bind_value = &long_value;
          u_type = CCI_U_TYPE_INT;
          a_type = CCI_A_TYPE_INT;
        }
    }
  else if (PyFloat_Check(value_obj))
    {
      double_value = PyFloat_AsDouble(value_obj);
      bind_value = &double_value;
      a_type = CCI_A_TYPE_DOUBLE;
      u_type = CCI_U_TYPE_DOUBLE;
    }
  else if (PyObject_IsInstance(value_obj, _func_Decimal))
    {
      temp_str = PyObject_Str(value_obj);
      if (!temp_str)
        {
          return NULL;
        }
      temp_bytes = PyUnicode_AsEncodedString(temp_str, "utf-8", "strict");
      if (!temp_bytes)
        {
          Py_DECREF(temp_str);
          return NULL;
        }
      str_value = PyBytes_AsString(temp_bytes);
      if (!str_value)
        {
          Py_DECREF(temp_str);
          Py_DECREF(temp_bytes);
          return NULL;
        }
      bind_value = str_value;
      u_type = CCI_U_TYPE_NUMERIC;
      a_type = CCI_A_TYPE_STR;
    }
  else if (PyDate_Check(value_obj) || PyTime_Check(value_obj) || PyDateTime_Check(value_obj))
    {
      if (PyDate_Check(value_obj) || PyDateTime_Check(value_obj))
        {
          date_value.yr = PyDateTime_GET_YEAR(value_obj);
          date_value.mon = PyDateTime_GET_MONTH(value_obj);
          date_value.day = PyDateTime_GET_DAY(value_obj);
        }

      if (PyDateTime_Check(value_obj))
        {
          date_value.hh = PyDateTime_DATE_GET_HOUR(value_obj);
          date_value.mm = PyDateTime_DATE_GET_MINUTE(value_obj);
          date_value.ss = PyDateTime_DATE_GET_SECOND(value_obj);
          date_value.ms = PyDateTime_DATE_GET_MICROSECOND(value_obj) / 1000;
        }
      else if (PyTime_Check(value_obj))
        {
          date_value.hh = PyDateTime_TIME_GET_HOUR(value_obj);
          date_value.mm = PyDateTime_TIME_GET_MINUTE(value_obj);
          date_value.ss = PyDateTime_TIME_GET_SECOND(value_obj);
          date_value.ms = PyDateTime_TIME_GET_MICROSECOND(value_obj) / 1000;
        }

      bind_value = &date_value;
      a_type = CCI_A_TYPE_DATE;
      if (PyDate_Check(value_obj))
        {
          u_type = CCI_U_TYPE_DATE;
        }
      if (PyTime_Check(value_obj))
        {
          u_type = CCI_U_TYPE_TIME;
        }
      if (PyDateTime_Check(value_obj))
        {
          u_type= CCI_U_TYPE_DATETIME;
        }
    }
  else if (PyUnicode_Check(value_obj))
    {
      temp_bytes = PyUnicode_AsEncodedString(value_obj, "utf-8", "strict");
      if (!temp_bytes)
        {
          return NULL;
        }
      if (PyObject_GetBuffer(temp_bytes, &value_view, PyBUF_SIMPLE) != 0)
        {
          Py_DECREF(temp_bytes);
          return NULL;
        }

      bind_value = value_view.buf;
    }
  else if (PyBytes_Check(value_obj))
    {
      if (PyObject_GetBuffer(value_obj, &value_view, PyBUF_SIMPLE) != 0)
        {
          return NULL;
        }

      if (u_type == CCI_U_TYPE_BIT || u_type == CCI_U_TYPE_VARBIT)
        {
          bit_value.size = value_view.len;
          bit_value.buf = value_view.buf;
          bind_value = &bit_value;
          a_type = CCI_A_TYPE_BIT;
        }
      else
        {
          bind_value = value_view.buf;
        }
    }
  else
    {
      return NULL;
    }

  res = cci_bind_param(self->handle, index, a_type, bind_value, u_type, 0);

  PyBuffer_Release(&value_view);

  if (temp_bytes)
    {
      Py_DECREF (temp_bytes);
    }

  if (temp_str)
    {
      Py_DECREF (temp_str);
    }

  if (res < 0)
    {
      return handle_error (res, NULL);
    }

  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_CursorObject_bind_lob__doc__[] = "bind_lob(n, lob)\n\
bind BLOB/CLOB type in prepare() variable.\n\
\n\
Parameters::\n\
  index: string, actual value for binding\n\
  lob: LOB Object\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
  cur = con.cursor()\n\
  \n\
  cur.prepare('create table test_blob(image BLOB)')\n\
  cur.execute()\n\
  cur.prepare('create table test_clob(image CLOB)')\n\
  cur.execute()\n\
  \n\
  lob = con.lob()\n\
  \n\
  cur.prepare('insert into test_blob values (?)')\n\
  lob.imports('123.jpg') # or lob.imports('123.jpg', 'B')\n\
  cur.bind_lob(1, lob)\n\
  cur.execute()\n\
  lob.close()\n\
  \n\
  cur.prepare('insert into test_clob values (?)')\n\
  lob.imports('123.jpg', 'C')\n\
  cur.bind_lob(1, lob)\n\
  cur.execute()\n\
  lob.close()\n\
  \n\
  cur.close()\n\
  con.close()";

static PyObject *
_cubrid_CursorObject_bind_lob (_cubrid_CursorObject * self, PyObject * args)
{
  _cubrid_LobObject *lob;
  int index, res;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, "iO!", &index, &_cubrid_LobObject_type, &lob))
    {
      return NULL;
    }

  if (lob->type == CUBRID_BLOB)
    {
      res =
	cci_bind_param (self->handle, index, CCI_A_TYPE_BLOB,
			(void *) lob->blob, CCI_U_TYPE_BLOB, CCI_BIND_PTR);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
    }
  else
    {
      res =
	cci_bind_param (self->handle, index, CCI_A_TYPE_CLOB,
			(void *) lob->clob, CCI_U_TYPE_CLOB, CCI_BIND_PTR);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
    }

  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_CursorObject_bind_set__doc__[] = "bind_set(index,data)\n\
bind_set LIST/SET/MULTISET data. To use this function.\n\
index:actual value for binding\n\
data:tuple object \n\
\n\
    Example::\n\
    con = _cubrid.connect('CUBRID:localhost:30000:demodb:dba::')\n\
    c = con.cursor()\n\
    s = con.set()\n\
    value = ('1','2')\n\
    s.imports(value ,CUBRIDdb.CCI_U_TYPE_INT)\n\
    c.prepare('''INSERT INTO set_tbl_int VALUES(?);''')\n\
    c.bind_set(1,s)\n\
    c.execute()\n\
    con.commit()\n\
    c.close()\n\
    con.close()";

static PyObject *
_cubrid_CursorObject_bind_Set (_cubrid_CursorObject * self, PyObject * args)
{
  _cubrid_SetObject *set;
  int index, res;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, "iO!", &index, &_cubrid_SetObject_type, &set))
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
    }

  res =
    cci_bind_param (self->handle, index, CCI_A_TYPE_SET,
		    (void *) set->data, CCI_U_TYPE_SET, CCI_BIND_PTR);
  if (res < 0)
    {
      return handle_error (res, NULL);
    }

  Py_INCREF (Py_None);
  return Py_None;
}

static int
_cubrid_CursorObject_set_description (_cubrid_CursorObject * self)
{
  PyObject *desc, *item;
  int i;
  int datatype, precision, scale, nullable;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (self->col_count == 0)
    {
      Py_XDECREF (self->description);
      self->description = PyTuple_New (0);
      return 1;
    }

  desc = (PyObject *) PyTuple_New (self->col_count);

  for (i = 1; i <= self->col_count; i++)
    {
      char *colName = NULL;

      item = PyTuple_New (7);

      colName = CCI_GET_RESULT_INFO_NAME (self->col_info, i);
      precision = CCI_GET_RESULT_INFO_PRECISION (self->col_info, i);
      scale = CCI_GET_RESULT_INFO_SCALE (self->col_info, i);
      nullable =
	(CCI_GET_RESULT_INFO_IS_NON_NULL (self->col_info, i)) ? 0 : 1;
      datatype = CCI_GET_RESULT_INFO_TYPE (self->col_info, i);

      PyTuple_SetItem (item, 0, _cubrid_return_PyString_FromString (colName));
      PyTuple_SetItem (item, 1, _cubrid_return_PyInt_FromLong (datatype));
      PyTuple_SetItem (item, 2, _cubrid_return_PyInt_FromLong (0));
      PyTuple_SetItem (item, 3, _cubrid_return_PyInt_FromLong (0));
      PyTuple_SetItem (item, 4, _cubrid_return_PyInt_FromLong (precision));
      PyTuple_SetItem (item, 5, _cubrid_return_PyInt_FromLong (scale));
      PyTuple_SetItem (item, 6, _cubrid_return_PyInt_FromLong (nullable));

      PyTuple_SetItem (desc, i - 1, item);
    }

  Py_XDECREF (self->description);
  self->description = desc;

  return 1;
}

static char _cubrid_CursorObject_result_info__doc__[] = "result_info(n)\n\
returns a sequence of 15-item sequences.\n\
Each of these sequence contails information describing one result column::\n\
 (datatype,\n\
  scale,\n\
  precision,\n\
  col_name,\n\
  attr_name,\n\
  class_name,\n\
  not_null,\n\
  default_value,\n\
  auto_increment,\n\
  unique_key,\n\
  primary_key,\n\
  foreign_key,\n\
  reverse_index,\n\
  reverse_unique,\n\
  shared)\n\
values of datatype will map the following::\n\
  char                 1\n\
  string,varchar       2\n\
  nchar                3\n\
  varnchar             4\n\
  bit                  5\n\
  varbit               6\n\
  numeric              7\n\
  int                  8\n\
  short                9\n\
  monetary             10\n\
  float                11\n\
  double               12\n\
  date                 13\n\
  time                 14\n\
  timestamp            15\n\
  object               19\n\
  set                  32\n\
  multiset             64\n\
  sequence             96\n\
This function will return none if there is no result set.\n\
If user not specifies the parameter row, it will return all\n\
column's information.\n\
If user specify row, it will return the specified column's information.\n\
\n\
row: int, the column you want to get the information.\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
  cur = con.cursor()\n\
  cur.prepare('select * from test_cubrid')\n\
  cur.execute()\n\
  infos = cur.result_info()\n\
  for info in infos:\n\
      print info\n\
  print cur.result_info(1)\n\
  cur.close()\n\
  con.close()";

static PyObject *
_cubrid_CursorObject_result_info (_cubrid_CursorObject * self,
				  PyObject * args)
{
  PyObject *result, *item;
  int i, j, n = 0, len = 0;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, "|i", &n))
    {
      return NULL;
    }

  if (self->col_count == 0)
    {
      Py_INCREF (Py_None);
      return Py_None;
    }

  if (n < 0 || n > self->col_count)
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
    }

  if (n != 0)
    {
      i = n;
      len = n;
    }
  else
    {
      i = 1;
      len = self->col_count;
    }

  result = (PyObject *) PyTuple_New (len - i + 1);

  for (j = 0; i <= len; i++, j++)
    {
      char *col_name = NULL, *real_attr = NULL;
      char *class_name = NULL, *default_value = NULL;
      int type, precision, scale, not_null, auto_increment, unique_key,
	primary_key, foreign_key, reverse_index, resverse_unique, shared;

      item = PyTuple_New (15);

      type = CCI_GET_RESULT_INFO_TYPE (self->col_info, i);
      not_null = CCI_GET_RESULT_INFO_IS_NON_NULL (self->col_info, i);
      scale = CCI_GET_RESULT_INFO_SCALE (self->col_info, i);
      precision = CCI_GET_RESULT_INFO_PRECISION (self->col_info, i);
      col_name = CCI_GET_RESULT_INFO_NAME (self->col_info, i);
      real_attr = CCI_GET_RESULT_INFO_ATTR_NAME (self->col_info, i);
      class_name = CCI_GET_RESULT_INFO_CLASS_NAME (self->col_info, i);
      default_value = CCI_GET_RESULT_INFO_DEFAULT_VALUE (self->col_info, i);
      auto_increment =
	CCI_GET_RESULT_INFO_IS_AUTO_INCREMENT (self->col_info, i);
      unique_key = CCI_GET_RESULT_INFO_IS_UNIQUE_KEY (self->col_info, i);
      primary_key = CCI_GET_RESULT_INFO_IS_PRIMARY_KEY (self->col_info, i);
      foreign_key = CCI_GET_RESULT_INFO_IS_FOREIGN_KEY (self->col_info, i);
      reverse_index =
	CCI_GET_RESULT_INFO_IS_REVERSE_INDEX (self->col_info, i);
      resverse_unique =
	CCI_GET_RESULT_INFO_IS_REVERSE_UNIQUE (self->col_info, i);
      shared = CCI_GET_RESULT_INFO_IS_SHARED (self->col_info, i);

      PyTuple_SetItem (item, 0, _cubrid_return_PyInt_FromLong (type));
      PyTuple_SetItem (item, 1, _cubrid_return_PyInt_FromLong (not_null));
      PyTuple_SetItem (item, 2, _cubrid_return_PyInt_FromLong (scale));
      PyTuple_SetItem (item, 3, _cubrid_return_PyInt_FromLong (precision));
      PyTuple_SetItem (item, 4,
		       _cubrid_return_PyString_FromString (col_name));
      PyTuple_SetItem (item, 5,
		       _cubrid_return_PyString_FromString (real_attr));
      PyTuple_SetItem (item, 6,
		       _cubrid_return_PyString_FromString (class_name));
      PyTuple_SetItem (item, 7,
		       _cubrid_return_PyString_FromString (default_value));
      PyTuple_SetItem (item, 8,
		       _cubrid_return_PyInt_FromLong (auto_increment));
      PyTuple_SetItem (item, 9, _cubrid_return_PyInt_FromLong (unique_key));
      PyTuple_SetItem (item, 10, _cubrid_return_PyInt_FromLong (primary_key));
      PyTuple_SetItem (item, 11, _cubrid_return_PyInt_FromLong (foreign_key));
      PyTuple_SetItem (item, 12,
		       _cubrid_return_PyInt_FromLong (reverse_index));
      PyTuple_SetItem (item, 13,
		       _cubrid_return_PyInt_FromLong (resverse_unique));
      PyTuple_SetItem (item, 14, _cubrid_return_PyInt_FromLong (shared));

      PyTuple_SetItem (result, j, item);
    }

  return result;
}

static char _cubrid_CursorObject_execute__doc__[] =
  "execute([option[,max_col_size]])\n\
Executes a prepared Query.\n\
A option can be used when retrieving the query result from the server.\n\
A option can be classified as synchronous or asynchronous. \n\
If the option is set to CUBRID_EXEC_QUERY_ALL, a synchronous mode(sync_mode) \n\
is used to retrieve query results immediately after executing prepared queries. \n\
If it is set to CUBRID_EXEC_ASYNC, an asynchronous mode (async_mode) is used to\n\
retrieve the result immediately each time a query result is created.\n\
The option is set to CUBRID_EXEC_QUERY_ALL by default, and in such\n\
cases the following rules are applied:\n\
  - The return value is the result of the first query.\n\
  - If an error occurs in any query, the execution is processed\n\
    as a failure.\n\
  - For a query composed of in a query composed of q1 q2 q3\n\
    if an error occurs in q2 after q1 succeeds the execution,\n\
    the result of q1 remains valid. That is, the previous successful\n\
    query executions are not rolled back when an error occurs.\n\
  - If a query is executed successfully, the result of the second\n\
    query can be obtained using next_result().\n\
max_col is a value that is used to determine the size of the column\n\
to be transferred to the client when the type of the column of the\n\
prepared query is CHAR, VARCHAR, NCHAR, VARNCHAR, BIT or VARBIT.\n\
If it is set to 0, all data is transferred.\n\
\n\
Parameters::\n\
  option: Exec option, option maybe the following values:\n\
    CUBRID_EXEC_ASYNC\n\
    CUBRID_EXEC_QUERY_ALL\n\
    CUBRID_EXEC_QUERY_INFO\n\
    CUBRID_EXEC_ONLY_QUERY_PLAN\n\
    CUBRID_EXEC_THREAD\n\
\n\
Return values::\n\
  SELECT: Returns the number of results in sync mode,\n\
          returns 0 in asynchronism mode.\n\
  INSERT, UPDATE: Returns the number of tuples reflected.\n\
  Others queries: 0\n";

static PyObject *
_cubrid_CursorObject_execute (_cubrid_CursorObject * self, PyObject * args)
{
  int res, option = 0, max_col_size = 0;
  T_CCI_ERROR error;
  T_CCI_COL_INFO *res_col_info;
  T_CCI_SQLX_CMD res_sql_type;
  int res_col_count;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, "|ii", &option, &max_col_size))
    {
      return NULL;
    }

  res = cci_execute (self->handle, option, max_col_size, &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  res_col_info =
    cci_get_result_info (self->handle, &res_sql_type, &res_col_count);
  if (res_sql_type == SQLX_CMD_SELECT && !res_col_info)
    {
      return handle_error (CUBRID_ER_CANNOT_GET_COLUMN_INFO, NULL);
    }

  self->col_info = res_col_info;
  self->sql_type = res_sql_type;
  self->col_count = res_col_count;

  switch (res_sql_type)
    {
    case SQLX_CMD_SELECT:
    case SQLX_CMD_INSERT:
    case SQLX_CMD_UPDATE:
    case SQLX_CMD_DELETE:
    case SQLX_CMD_CALL:
      self->row_count = res;
      break;
    default:
      self->row_count = -1;
      break;
    }

  if (res_sql_type == SQLX_CMD_SELECT)
    {
      int ret;

      _cubrid_CursorObject_set_description (self);
      ret = cci_cursor (self->handle, 1, CCI_CURSOR_CURRENT, &error);
      if (ret < 0 && ret != CCI_ER_NO_MORE_DATA)
	{
	  return handle_error (ret, &error);
	}
    }

  return _cubrid_return_PyInt_FromLong (res);
}

/* DB type to Python type mapping
* 
* int, short 			-> Integer
* float, double, numeric 	-> Float
* numeric   			-> Decimal
* time 					-> datetime.time
* date 					-> datetime.date
* datetime 				-> datetime.datetime
* timestamp 			-> datetime.datetime
* another type			-> String
*/

static PyObject *
_cubrid_CursorObject_dbval_to_pyvalue (_cubrid_CursorObject * self, int type,
				       int index)
{
  int res, ind;
  PyObject *val, *tmpval;
  char *buffer;
  int num;
  T_CCI_DATE dt;
  T_CCI_BIT bit_data;
  char *str_buffer;
  int len;
  CUBRID_LONG_LONG int64_value;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  switch (type)
    {
    case CCI_U_TYPE_BIT:
    case CCI_U_TYPE_VARBIT:
      {
	res = cci_get_data (self->handle, index, CCI_A_TYPE_BIT, &bit_data, &ind);
	if (res < 0)
	  {
	    return handle_error (res, NULL);
	  }
	if (ind < 0)
	  {
	    Py_INCREF (Py_None);
	    val = Py_None;
	  }
	else
	  {
	    if (bit_data.buf == NULL && bit_data.size > 0)
	      {
		return PyErr_Format(PyExc_SystemError, "CCI returned invalid data for BIT type: NULL buffer with size %d", bit_data.size);
	      }
	    val = _cubrid_return_PyString_FromStringAndSize((const char*)bit_data.buf, bit_data.size);

	    if (val == NULL)
	      {
		return NULL;
	      }
	  }
      }
      break;
    case CCI_U_TYPE_INT:
    case CCI_U_TYPE_SHORT:
      res = cci_get_data (self->handle, index, CCI_A_TYPE_INT, &num, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
      if (ind < 0)
	{
	  Py_INCREF (Py_None);
	  return Py_None;
	}
      else
	{
	  val = _cubrid_return_PyInt_FromLong (num);
	}
      break;
    case CCI_U_TYPE_BIGINT:
      res = cci_get_data (self->handle, index, CCI_A_TYPE_BIGINT, &int64_value, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
      if (ind < 0)
	{
	  Py_INCREF (Py_None);
	  return Py_None;
	}
      else
	{
	  val = _cubrid_return_PyLong_FromLongLong (int64_value);
	}
      break;
    case CCI_U_TYPE_FLOAT:
    case CCI_U_TYPE_DOUBLE:
      res = cci_get_data (self->handle, index, CCI_A_TYPE_STR, &buffer, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
      if (ind < 0)
	{
	  Py_INCREF (Py_None);
	  val = Py_None;
	}
      else
	{
	  tmpval = _cubrid_return_PyString_FromString (buffer);
#if PY_MAJOR_VERSION >= 3
	  val = PyFloat_FromString (tmpval);
#else
	  val = PyFloat_FromString (tmpval, NULL);
#endif
	  Py_DECREF (tmpval);
	}
      break;
    case CCI_U_TYPE_NUMERIC:
      res = cci_get_data (self->handle, index, CCI_A_TYPE_STR, &buffer, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
      if (ind < 0)
	{
	  Py_INCREF (Py_None);
	  val = Py_None;
	}
      else
	{
	  tmpval = PyTuple_New (1);
	  PyTuple_SetItem (tmpval, 0, Py_BuildValue ("s", buffer));
	  val = PyObject_CallObject (_func_Decimal, tmpval);
	  Py_DECREF (tmpval);
	}
      break;
    case CCI_U_TYPE_DATE:
      res = cci_get_data (self->handle, index, CCI_A_TYPE_DATE, &dt, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
      if (ind < 0)
	{
	  Py_INCREF (Py_None);
	  val = Py_None;
	}
      else
	{
	  val = PyDate_FromDate (dt.yr, dt.mon, dt.day);
	}
      break;
    case CCI_U_TYPE_TIME:
      res = cci_get_data (self->handle, index, CCI_A_TYPE_DATE, &dt, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
      if (ind < 0)
	{
	  Py_INCREF (Py_None);
	  val = Py_None;
	}
      else
	{
	  val = PyTime_FromTime (dt.hh, dt.mm, dt.ss, 0);
	}
      break;
    case CCI_U_TYPE_DATETIME:
      res = cci_get_data (self->handle, index, CCI_A_TYPE_DATE, &dt, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
      if (ind < 0)
	{
	  Py_INCREF (Py_None);
	  val = Py_None;
	}
      else
	{
	  val =
	    PyDateTime_FromDateAndTime (dt.yr, dt.mon, dt.day, dt.hh, dt.mm,
					dt.ss, dt.ms * 1000);
	}
      break;
    case CCI_U_TYPE_TIMESTAMP:
      res = cci_get_data (self->handle, index, CCI_A_TYPE_DATE, &dt, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
      if (ind < 0)
	{
	  Py_INCREF (Py_None);
	  val = Py_None;
	}
      else
	{
	  val =
	    PyDateTime_FromDateAndTime (dt.yr, dt.mon, dt.day, dt.hh, dt.mm,
					dt.ss, 0);
	}
      break;
    case CCI_U_TYPE_JSON:
    case CCI_U_TYPE_CHAR:
    case CCI_U_TYPE_STRING:
      res = cci_get_data (self->handle, index, CCI_A_TYPE_STR, &buffer, &ind);
      if (res < 0)
        {
          return handle_error (res, NULL);
        }
      if (ind < 0)
        {
          Py_INCREF (Py_None);
          val = Py_None;
        }
      else
        {
          val = _cubrid_return_PyUnicode_FromString (buffer, strlen (buffer), self->charset, NULL);
          if (val == NULL)
            {
	      PyErr_SetString (PyExc_ValueError, "String decoding failed");
	      return Py_None;
            }
        }
      break;
    default:
      res = cci_get_data (self->handle, index, CCI_A_TYPE_INT, &num, &ind);
      if (res == 0)
        {
          if (ind < 0)
            {
              Py_INCREF (Py_None);
              return Py_None;
            }

          return PyLong_FromLong (num);
        }

      res = cci_get_data (self->handle, index, CCI_A_TYPE_DATE, &dt, &ind);
      if (res == 0)
        {
          if (ind < 0)
            {
              Py_INCREF (Py_None);
              val = Py_None;
            }

          if (dt.yr == 0)
            {
              return PyTime_FromTime(dt.hh, dt.mm, dt.ss, dt.ms * 1000);
            }
          if (dt.hh == 0 && dt.mm == 0 && dt.ss == 0 && dt.ms == 0)
            {
              return PyDate_FromDate (dt.yr, dt.mon, dt.day);
            }
          else
            {
              return PyDateTime_FromDateAndTime (dt.yr, dt.mon, dt.day, dt.hh,
                                                 dt.mm, dt.ss, dt.ms * 1000);
            }
        }

      // Unknown type, try str
      res = cci_get_data (self->handle, index, CCI_A_TYPE_STR, &buffer, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
      if (ind < 0)
	{
	  Py_INCREF (Py_None);
	  val = Py_None;
	}
      else
	{
	  if (self->charset != NULL && *(self->charset) != '\0')
	    {
	      val =
		_cubrid_return_PyUnicode_FromString (buffer, strlen (buffer),
						     self->charset, NULL);
	      if (val == NULL)
	        {
		  PyErr_SetString (PyExc_ValueError, "String decoding failed");
		  return Py_None;
		}
	    }
	  else
	    {
	      val = _cubrid_return_PyString_FromString (buffer);
	    }
	}
      break;
    }

  return val;
}

/*
 * Collection(set)                        -> Set,
 * Collection(multiset, sequence)         -> List,
 * Collection' item  -> String
*/

static PyObject *
_cubrid_CursorObject_dbset_to_pyvalue (_cubrid_CursorObject * self, int type, int index)
{
  int i, res, ind;
  PyObject *val;
  T_CCI_SET set = NULL;
  int set_size;
  PyObject *e;
  char *buffer;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  res = cci_get_data (self->handle, index, CCI_A_TYPE_SET, &set, &ind);
  if (res < 0)
    {
      return handle_error (res, NULL);
    }

  if (ind < 0)
    {
      Py_INCREF (Py_None);
      return Py_None;
    }

  set_size = cci_set_size (set);

  if (CCI_IS_SET_TYPE (type))
    {
      val = PySet_New (NULL);
    }
  else
    {
      val = PyList_New (set_size);
    }

  for (i = 0; i < set_size; i++)
    {
      res = cci_set_get (set, i + 1, CCI_A_TYPE_STR, &buffer, &ind);
      if (res < 0)
        {
          cci_set_free (set);
          return handle_error (res, NULL);
        }

      if (buffer == NULL)
        {
          e = _cubrid_return_PyString_FromString ("");
        }
      else
        {
          e = _cubrid_return_PyUnicode_FromString (buffer, strlen (buffer), self->charset, NULL);
          if (e == NULL)
            {
              PyErr_SetString (PyExc_ValueError, "String decoding failed");
              cci_set_free (set);
              return handle_error (res, NULL);
            }
        }

      if (CCI_IS_SET_TYPE (type))
        {
          PySet_Add (val, e);
          Py_DECREF (e);
        }
      else
        {
          PyList_SetItem (val, i, e);
        }
    }

  cci_set_free (set);
  return val;
}

static PyObject *
_cubrid_row_to_tuple (_cubrid_CursorObject * self)
{
  int i, type;
  PyObject *row, *val;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  row = PyTuple_New (self->col_count);

  for (i = 0; i < self->col_count; i++)
    {
      type = CCI_GET_RESULT_INFO_TYPE (self->col_info, i + 1);

      if (CCI_IS_COLLECTION_TYPE (type))
	{
	  val = _cubrid_CursorObject_dbset_to_pyvalue (self, type, i + 1);
	}
      else
	{
	  val = _cubrid_CursorObject_dbval_to_pyvalue (self, type, i + 1);
	}
      PyTuple_SetItem (row, i, val);
    }

  return row;
}

static PyObject *
_cubrid_row_to_dict (_cubrid_CursorObject * self)
{
  PyObject *row, *val;
  int i, type;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!(row = PyDict_New ()))
    {
      return NULL;
    }

  for (i = 0; i < self->col_count; i++)
    {
      char *col_name = CCI_GET_RESULT_INFO_NAME (self->col_info, i + 1);

      type = CCI_GET_RESULT_INFO_TYPE (self->col_info, i + 1);

      if (CCI_IS_COLLECTION_TYPE (type))
	{
	  val = _cubrid_CursorObject_dbset_to_pyvalue (self, type, i + 1);
	}
      else
	{
	  val = _cubrid_CursorObject_dbval_to_pyvalue (self, type, i + 1);
	}
      PyMapping_SetItemString (row, col_name, val);
    }

  return row;
}

static char _cubrid_CursorObject_fetch__doc__[] = "fetch_row()\n\
get a single row from the query result. The cursor automatically moves\n\
to the next row after getting the result.\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
  cur = con.cursor()\n\
  cur.prepare('select * from test_cubrid')\n\
  cur.execute()\n\
  row = cur.fetch_row()\n\
  while row:\n\
    print row\n\
    row = cur.fetch_row()\n\
  cur.close()\n\
  con.close()";

static PyObject *
_cubrid_CursorObject_fetch (_cubrid_CursorObject * self, PyObject * args)
{
  int res, how = 0;
  T_CCI_ERROR error;
  PyObject *row;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, "|i", &how))
    {
      return NULL;
    }

  if (how < 0 || how > 1)
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
    }

  res = cci_cursor (self->handle, 0, CCI_CURSOR_CURRENT, &error);
  if (res == CCI_ER_NO_MORE_DATA)
    {
      Py_INCREF (Py_None);
      return Py_None;
    }
  else if (res < 0)
    {
      return handle_error (res, &error);
    }

  res = cci_fetch (self->handle, &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  if (how == 0)
    {
      row = _cubrid_row_to_tuple (self);
    }
  else
    {
      row = _cubrid_row_to_dict (self);
    }

  res = cci_cursor (self->handle, 1, CCI_CURSOR_CURRENT, &error);
  if (res < 0 && res != CCI_ER_NO_MORE_DATA)
    {
      return handle_error (res, &error);
    }

  self->cursor_pos += 1;

  return row;
}

static char _cubrid_CursorObject_fetch_lob__doc__[] = "fetch_lob(col, lob)\n\
get BLOB/CLOB data out from the database server. You need to specify\n\
which column is lob type.\n\
\n\
Parameters::\n\
  col: int, the column of LOB\n\
  lob: LOB object, to process LOB data.\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
  cur = con.cursor()\n\
  cur.prepare('select * from test_lob')\n\
  cur.execute()\n\
  lob = con.lob()\n\
  cur.fetch_lob(1, lob)\n\
  lob.close()\n\
  cur.close()\n\
  con.close()";

static PyObject *
_cubrid_CursorObject_fetch_lob (_cubrid_CursorObject * self, PyObject * args)
{
  _cubrid_LobObject *lob;
  int col = 1, res, ind;
  T_CCI_ERROR error;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, "iO!", &col, &_cubrid_LobObject_type, &lob))
    {
      return NULL;
    }

  res = cci_cursor (self->handle, 0, CCI_CURSOR_CURRENT, &error);
  if (res == CCI_ER_NO_MORE_DATA)
    {
      Py_INCREF (Py_None);
      return Py_None;
    }
  else if (res < 0)
    {
      return handle_error (res, &error);
    }

  res = cci_fetch (self->handle, &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  if (CCI_GET_RESULT_INFO_TYPE (self->col_info, 1) == CCI_U_TYPE_BLOB)
    {
      lob->type = CUBRID_BLOB;
      res =
	cci_get_data (self->handle, col, CCI_A_TYPE_BLOB,
		      (void *) &lob->blob, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
    }
  else
    {
      lob->type = CUBRID_CLOB;
      res =
	cci_get_data (self->handle, col, CCI_A_TYPE_CLOB,
		      (void *) &lob->clob, &ind);
      if (res < 0)
	{
	  return handle_error (res, NULL);
	}
    }

  res = cci_cursor (self->handle, 1, CCI_CURSOR_CURRENT, &error);
  if (res < 0 && res != CCI_ER_NO_MORE_DATA)
    {
      return handle_error (res, &error);
    }

  self->cursor_pos += 1;

  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_CursorObject_affected_rows__doc__[] = "affected_rows()\n\
get the number of rows affected by the SQL sentence (INSERT,\n\
DELETE, UPDATE).\n\
\n\
Return values::\n\
  Success: Number of rows affected by the SQL sentence\n\
  Failure: -1";

static PyObject *
_cubrid_CursorObject_affected_rows (_cubrid_CursorObject * self,
				    PyObject * args)
{
  int affected_rows;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, ""))
    {
      return NULL;
    }

  switch (self->sql_type)
    {
    case SQLX_CMD_INSERT:
    case SQLX_CMD_UPDATE:
    case SQLX_CMD_DELETE:
      affected_rows = self->row_count;
      break;
    default:
      affected_rows = -1;
      break;
    }

  return _cubrid_return_PyInt_FromLong (affected_rows);
}

static char _cubrid_CursorObject_data_seek__doc__[] = "data_seek(n)\n\
move the cursor based on the original position.\n\
\n\
offset: int, number of units you want to move the cursor.";

static PyObject *
_cubrid_CursorObject_data_seek (_cubrid_CursorObject * self, PyObject * args)
{
  int res;
  T_CCI_ERROR error;
  int row;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, "i", &row))
    {
      return NULL;
    }

  if (row < 1 || row > self->row_count)
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, &error);
    }

  res = cci_cursor (self->handle, row, CCI_CURSOR_FIRST, &error);
  if (res < 0 || res == CCI_ER_NO_MORE_DATA)
    {
      return handle_error (res, &error);
    }

  self->cursor_pos = row;

  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_CursorObject_num_fields__doc__[] = "num_fields()\n\
get the number of columns from the query result. It can\n\
only be used when the query executed is a select sentence.\n";

static PyObject *
_cubrid_CursorObject_num_fields (_cubrid_CursorObject * self, PyObject * args)
{
  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, ""))
    {
      return NULL;
    }

  if (self->sql_type == SQLX_CMD_SELECT)
    {
      return _cubrid_return_PyInt_FromLong (self->col_count);
    }

  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_CursorObject_num_rows__doc__[] = "num_rows()\n\
get the number of rows from the query result. It can\n\
only be used when the query executed is a select sentence.\n";

static PyObject *
_cubrid_CursorObject_num_rows (_cubrid_CursorObject * self, PyObject * args)
{
  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, ""))
    {
      return NULL;
    }

  if (self->sql_type == SQLX_CMD_SELECT)
    {
      return _cubrid_return_PyInt_FromLong (self->row_count);
    }

  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_CursorObject_row_tell__doc__[] =
  "get the current position of the cursor.";

static PyObject *
_cubrid_CursorObject_row_tell (_cubrid_CursorObject * self, PyObject * args)
{
  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, ""))
    {
      return NULL;
    }

  if (self->cursor_pos > self->row_count)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR_POS, NULL);
    }

  return _cubrid_return_PyInt_FromLong (self->cursor_pos);
}

static char _cubrid_CursorObject_row_seek__doc__[] = "row_seek(offset)\n\
move the current cursor based on current cursor\n\
position. If give a positive number, it will move forward.\n\
If you give a negative number, it will move back.\n\
\n\
offset: int, relative location that you want to move.\n";

static PyObject *
_cubrid_CursorObject_row_seek (_cubrid_CursorObject * self, PyObject * args)
{
  int offset, res;
  T_CCI_ERROR error;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, "i", &offset))
    {
      return NULL;
    }

  res = cci_cursor (self->handle, offset, CCI_CURSOR_CURRENT, &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  self->cursor_pos += offset;

  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_CursorObject_next_result__doc__[] = "next_result()\n\
get results of next query if CUBRID_EXEC_QUERY_ALL\n\
flag is set upon execute(). If next result is executed successfully,\n\
the database is updated with the information of the current query.";

static PyObject *
_cubrid_CursorObject_next_result (_cubrid_CursorObject * self,
				  PyObject * args)
{
  int res, col_count;
  T_CCI_ERROR error;
  T_CCI_COL_INFO *res_col_info;
  T_CCI_SQLX_CMD res_sql_type;

  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, ""))
    {
      return NULL;
    }

  //_cubrid_CursorObject_reset (self);
  if (self->description)
    {
      Py_DECREF (self->description);
      self->description = NULL;
    }

  self->bind_num = -1;
  self->col_count = -1;
  self->sql_type = 0;
  self->row_count = -1;
  self->cursor_pos = 0;

  res = cci_next_result (self->handle, &error);
  if (res == CAS_ER_NO_MORE_RESULT_SET)
    {
      goto RETURN_NEXT_RESULT;
    }
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  res_col_info =
    cci_get_result_info (self->handle, &res_sql_type, &col_count);
  if (res_sql_type == SQLX_CMD_SELECT && !res_col_info)
    {
      return handle_error (CUBRID_ER_CANNOT_GET_COLUMN_INFO, NULL);
    }

  self->col_info = res_col_info;
  self->sql_type = res_sql_type;
  self->col_count = col_count;

  switch (res_sql_type)
    {
    case SQLX_CMD_SELECT:
    case SQLX_CMD_INSERT:
    case SQLX_CMD_UPDATE:
    case SQLX_CMD_DELETE:
    case SQLX_CMD_CALL:
      self->row_count = res;
      break;
    default:
      self->row_count = -1;
      break;
    }

  if (res_sql_type == SQLX_CMD_SELECT)
    {
      _cubrid_CursorObject_set_description (self);
      res = cci_cursor (self->handle, 1, CCI_CURSOR_CURRENT, &error);
      if (res < 0 && res != CCI_ER_NO_MORE_DATA)
	{
	  return handle_error (res, &error);
	}
    }

RETURN_NEXT_RESULT:
  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_CursorObject_close__doc__[] =
  "close() -- Close the current cursor object.";

static PyObject *
_cubrid_CursorObject_close (_cubrid_CursorObject * self, PyObject * args)
{
  if (self->state == CURSOR_STATE_CLOSED)
    {
      return handle_error (CUBRID_ER_INVALID_CURSOR, NULL);
    }
  if (!PyArg_ParseTuple (args, ""))
    {
      return NULL;
    }

  _cubrid_CursorObject_reset (self);
  self->state = CURSOR_STATE_CLOSED;
  Py_INCREF (Py_None);
  return Py_None;
}

static void
_cubrid_CursorObject_dealloc (_cubrid_CursorObject * self)
{
  _cubrid_CursorObject_reset (self);
  Py_TYPE (self)->tp_free ((PyObject *) self);
}

static PyObject *
_cubrid_LobObject_new (PyTypeObject * type, PyObject * args,
		       PyObject * kwargs)
{
  _cubrid_LobObject *self;

  self = (_cubrid_LobObject *) type->tp_alloc (type, 0);
  if (!self)
    {
      return NULL;
    }

  return (PyObject *) self;
}

static int
_cubrid_LobObject_init (_cubrid_LobObject * self, PyObject * args,
			PyObject * kwargs)
{
  _cubrid_ConnectionObject *conn;

  if (!PyArg_ParseTuple (args, "O!", &_cubrid_ConnectionObject_type, &conn))
    {
      return -1;
    }

  self->connection = conn->handle;
  self->blob = NULL;
  self->clob = NULL;
  self->pos = 0;
  self->type = CUBRID_BLOB;

  return 0;
}

static char _cubrid_LobObject_close__doc__[] = "close() -- Close the lob";

static PyObject *
_cubrid_LobObject_close (_cubrid_LobObject * self, PyObject * args)
{
  if (self->blob)
    {
      cci_blob_free (self->blob);
      self->blob = NULL;
    }
  if (self->clob)
    {
      cci_blob_free (self->clob);
      self->clob = NULL;
    }
  Py_INCREF (Py_None);
  return Py_None;
}

static PyObject *
_cubrid_LobObject_create (_cubrid_LobObject * self, char type)
{
  int res;
  T_CCI_ERROR error;

  if (type == 'B' || type == 'b')
    {
      res = cci_blob_new (self->connection, &self->blob, &error);
      if (res < 0)
	{
	  return handle_error (res, &error);
	}
      self->type = CUBRID_BLOB;
    }
  else if (type == 'C' || type == 'c')
    {
      res = cci_clob_new (self->connection, &self->clob, &error);
      if (res < 0)
	{
	  return handle_error (res, &error);
	}
      self->type = CUBRID_CLOB;
    }
  else
    {
      return handle_error (CUBRID_ER_UNKNOWN_TYPE, NULL);
    }

  Py_INCREF (Py_None);
  return Py_None;
}

static int
_cubrid_LobObject_cci_write (_cubrid_LobObject * self, CUBRID_LONG_LONG pos,
			     int size, char *buf, T_CCI_ERROR * error)
{
  return (self->type == CUBRID_BLOB) ?
    cci_blob_write (self->connection, self->blob, pos, size, buf, error) :
    cci_clob_write (self->connection, self->clob, pos, size, buf, error);
}

static CUBRID_LONG_LONG
_cubrid_LobObject_cci_lob_size (_cubrid_LobObject * self)
{
  return (self->type == CUBRID_BLOB) ?
    cci_blob_size (self->blob) : cci_clob_size (self->clob);
}

static char _cubrid_LobObject_import__doc__[] = "imports(file[, type])\n\
imports file in CUBRID server.\n\
If not give the type, it will be processed as BLOB.\n";

static PyObject *
_cubrid_LobObject_import (_cubrid_LobObject * self, PyObject * args)
{
  char *filename = NULL, buf[CUBRID_LOB_BUF_SIZE] = { '\0' }, *type = NULL;
  int fd;
  CUBRID_LONG_LONG pos = 0;
  int res, type_size, size;
  T_CCI_ERROR error;

  if (!PyArg_ParseTuple (args, "s|s", &filename, &type))
    {
      return NULL;
    }

  if (type == NULL)
    {
      _cubrid_LobObject_create (self, CUBRID_BLOB);
    }
  else
    {
      type_size = (int) strlen (type);
      if (type_size > 1)
	{
	  return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
	}

      _cubrid_LobObject_create (self, *type);
    }

  fd = open (filename, O_RDONLY | O_BINARY, 0400);
  if (fd < 0)
    {
      return handle_error (CUBRID_ER_OPEN_FILE, NULL);
    }

  while (1)
    {
      size = read (fd, buf, CUBRID_LOB_BUF_SIZE);
      if (size < 0)
	{
	  close (fd);
	  _cubrid_LobObject_close (self, NULL);
	  return handle_error (CUBRID_ER_READ_FILE, NULL);
	}

      if (size == 0)
	{
	  break;
	}

      res = _cubrid_LobObject_cci_write (self, pos, size, buf, &error);
      if (res < 0)
	{
	  close (fd);
	  _cubrid_LobObject_close (self, NULL);
	  return handle_error (res, &error);
	}

      pos += size;
    }

  close (fd);

  Py_INCREF (Py_None);
  return Py_None;
}


static char _cubrid_LobObject_write__doc__[] = "write(string)\n\
writes a string to the large object.If LOB object does not exist.\n\
It will be create a BLOB object as default.\n\
\n\
Example 1::\n\
  import _cubrid\n\
  con = _cubrid.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
  cur = con.cursor()\n\
  cur.prepare('insert into test_clob(content) values (?)')\n\
  lob = con.lob()\n\
  content = 'CUBRID is a very powerful RDBMS'\n\
  lob.write(content, 'C')\n\
  cur.bind_lob(1, lob)\n\
  cur.execute()\n\
  lob.close()\n\
  cur.close()\n\
  con.close()\n\
\n\
Example 2::\n\
  import _cubrid\n\
  con = _cubrid.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
  cur = con.cursor()\n\
  cur.prepare('select * from test_blob')\n\
  cur.execute()\n\
  lob = con.lob()\n\
  cur.fetch_lob(1, lob)\n\
  lob.seek(50, SEEK_CUR)\n\
  lob.write('CUBRID a powerfer database')\n\
  lob.close()\n\
  cur.close()\n\
  con.close()";

static PyObject *
_cubrid_LobObject_write (_cubrid_LobObject * self, PyObject * args)
{
  char *buf = NULL, *type = NULL;
  Py_ssize_t len = -1;
  Py_ssize_t type_len = 0;
  int res = -1;
  T_CCI_ERROR error;

  if (!PyArg_ParseTuple (args, "s#|s", &buf, &len, &type))
    {
      return NULL;
    }

  if (self->blob == NULL && self->clob == NULL)
    {
      if (type == NULL)
	{
	  _cubrid_LobObject_create (self, CUBRID_BLOB);
	}
      else
	{
	  type_len = (int) strlen (type);
	  if (type_len > 1)
	    {
	      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
	    }

	  _cubrid_LobObject_create (self, *type);
	}
    }

  res = _cubrid_LobObject_cci_write (self, self->pos, len, buf, &error);
  if (res < 0)
    {
      return handle_error (res, &error);
    }

  self->pos += len;

  Py_INCREF (Py_None);
  return Py_None;
}

static int
_cubrid_LobObject_cci_read (_cubrid_LobObject * self, CUBRID_LONG_LONG pos,
			    int size, char *buf, T_CCI_ERROR * error)
{
  return (self->type == CUBRID_BLOB) ?
    cci_blob_read (self->connection, self->blob, pos, size, buf, error) :
    cci_clob_read (self->connection, self->clob, pos, size, buf, error);
}

static char _cubrid_LobObject_export__doc__[] = "export(file)\n\
export BLOB/CLOB data to the specified file. To use this function, you must\n\
use fetch_lob() in cursor class first to get BLOB/CLOB info from CUBRID.\n\
\n\
file: string, support filepath/file\n\
\n\
Example::\n\
  import _cubrid\n\
  con = _cubrid.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
  cur = con.cursor()\n\
  cur.prepare('select * from test_lob')\n\
  cur.execute()\n\
  lob = con.lob()\n\
  cur.fetch_lob(1, lob)\n\
  lob.export('out')\n\
  lob.close()\n\
  cur.close()\n\
  con.close()";

static PyObject *
_cubrid_LobObject_export (_cubrid_LobObject * self, PyObject * args)
{
  char *filename = NULL, buf[CUBRID_LOB_BUF_SIZE] = { '\0' };
  int fp, res, size;
  CUBRID_LONG_LONG pos = 0, lob_size;
  T_CCI_ERROR error;
  if (!PyArg_ParseTuple (args, "s", &filename))
    {
      return NULL;
    }

  if (self->blob == NULL && self->clob == NULL)
    {
      return handle_error (CUBRID_ER_LOB_NOT_EXIST, NULL);
    }

  fp = open (filename, O_CREAT | O_WRONLY | O_TRUNC | O_BINARY, 0666);
  if (fp < 0)
    {
      return handle_error (CUBRID_ER_OPEN_FILE, NULL);
    }

  lob_size = _cubrid_LobObject_cci_lob_size (self);

  while (1)
    {
      size =
	_cubrid_LobObject_cci_read (self, pos, CUBRID_LOB_BUF_SIZE, buf,
				    &error);
      if (size < 0)
	{
	  close (fp);
	  unlink (filename);
	  return handle_error (size, &error);
	}

      res = write (fp, buf, size);
      if (res < 0)
	{
	  close (fp);
	  unlink (filename);
	  return handle_error (CUBRID_ER_WRITE_FILE, NULL);
	}

      pos += size;
      if (pos == lob_size)
	{
	  break;
	}
    }

  close (fp);

  Py_INCREF (Py_None);
  return Py_None;
}

static char _cubrid_LobObject_read__doc__[] = "read(len)\n\
read a chunk of data from the current file position.\n\
If not given the length, it will read all the remaining data.\n\
\n\
Return a string that contains the data read.\n\
\n\
Example 1::\n\
  import _cubrid\n\
  con = _cubrid.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
  lob = con.lob()\n\
  lob.imports('README', 'C')\n\
  str = lob.read(32)\n\
  print str\n\
  lob.close()\n\
  con.clsoe()\n\
\n\
Example 2::\n\
  import _cubrid\n\
  con = _cubrid.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
  cur = con.cursor()\n\
  cur.prepare('select * from test_lob')\n\
  cur.execute()\n\
  lob = con.lob()\n\
  cur.fetch_lob(1, lob)\n\
  print lob.read(32)\n\
  lob.close()\n\
  cur.close()\n\
  con.close()";

static PyObject *
_cubrid_LobObject_read (_cubrid_LobObject * self, PyObject * args)
{
  int res;
  char *buf;
  T_CCI_ERROR error;
  PyObject *ret;
  CUBRID_LONG_LONG size, len = 0;

  if (!PyArg_ParseTuple (args, "|L", &len))
    {
      return NULL;
    }

  if (len < 0)
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
    }

  if (self->blob == NULL && self->clob == NULL)
    {
      return handle_error (CUBRID_ER_LOB_NOT_EXIST, NULL);
    }

  if (!len)
    {
      size = _cubrid_LobObject_cci_lob_size (self);
      len = size - self->pos;
    }

  buf = PyMem_Malloc ((int) len);
  if (!buf)
    {
      return handle_error (CUBRID_ER_NO_MORE_MEMORY, NULL);
    }

  res = _cubrid_LobObject_cci_read (self, self->pos, (int) len, buf, &error);
  if (res < 0)
    {
      PyMem_Free (buf);
      return handle_error (res, &error);
    }

  self->pos += len;

#if PY_MAJOR_VERSION >= 3
  ret = PyUnicode_FromStringAndSize (buf, (int) len);
#else
  ret = PyString_FromStringAndSize (buf, (int) len);
#endif

  PyMem_Free (buf);
  return ret;
}

static char _cubrid_LobObject_seek__doc__[] = "seek(offset[, whence])\n\
move the LOB object current position to the direction LOB object\n\
according to the mode whence giving.\n\
The argument whence can be the following values:\n\
 - SEKK_SET: means move the cursor based on the original position,\n\
   offset must be positive number, the cursor will be moved forward\n\
   offset units relative to the original position.\n\
 - SEEK_CUR: means move the cursor based on the current position.\n\
   If offset is positive number, means move the cursor forward offset\n\
   units. If offset is negative number, means move back offset units.\n\
   This is the default value.\n\
 - SEEK_END: means move the cursor based on the end position, offset\n\
   must be positive number, the cursor will be moved back offset units\n\
   relative to the end position.\n\
\n\
Return the current position of the cursor.";

static PyObject *
_cubrid_LobObject_seek (_cubrid_LobObject * self, PyObject * args)
{
  int whence = SEEK_CUR;
  CUBRID_LONG_LONG size, offset;

  if (!PyArg_ParseTuple (args, "L|i", &offset, &whence))
    {
      return NULL;
    }

  if (whence == SEEK_CUR)
    {
      self->pos += offset;
    }
  else if (whence == SEEK_SET)
    {
      self->pos = offset;
    }
  else if (whence == SEEK_END)
    {
      size = _cubrid_LobObject_cci_lob_size (self);
      self->pos = size - offset;
    }
  else
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
    }

  return _cubrid_return_PyLong_FromLongLong (self->pos);
}

static void
_cubrid_LobObject_dealloc (_cubrid_LobObject * self)
{
  _cubrid_LobObject_close (self, NULL);
  Py_TYPE (self)->tp_free ((PyObject *) self);
}

static int
_cubrid_SetObject_init (_cubrid_SetObject * self, PyObject * args,
			PyObject * kwargs)
{
  _cubrid_ConnectionObject *conn;

  if (!PyArg_ParseTuple (args, "O!", &_cubrid_ConnectionObject_type, &conn))
    {
      return -1;
    }

  self->connection = conn->handle;
  self->data = NULL;
  self->type = CCI_U_TYPE_STRING;

  return 0;
}

static PyObject *
_cubrid_SetObject_new (PyTypeObject * type, PyObject * args,
		       PyObject * kwargs)
{
  _cubrid_SetObject *self;

  self = (_cubrid_SetObject *) type->tp_alloc (type, 0);
  if (!self)
    {
      return NULL;
    }

  return (PyObject *) self;
}

static void
_cubrid_SetObject_dealloc (_cubrid_SetObject * self)
{
  cci_set_free (self->data);
  Py_TYPE (self)->tp_free ((PyObject *) self);
}

static char *
_cubrid_str2bit (char *str)
{
  int i = 0, len = 0, t = 0;
  char *buf = NULL;
  int shift = 8;

  if (str == NULL)
    return NULL;
  len = strlen (str);

  if (0 == len % shift)
    t = 1;

  buf = (char *) malloc (len / shift + 1 + 1);
  memset (buf, 0, len / shift + 1 + 1);

  for (i = 0; i < len; i++)
    {
      if (str[len - i - 1] == '1')
	{
	  buf[len / shift - i / shift - t] |= (1 << (i % shift));
	}
      else if (str[len - i - 1] == '0')
	{
	  //nothing
	}
      else
	{
	  return NULL;
	}
    }
  return buf;
}

static PyObject *
_cubrid_SetObject_import (_cubrid_SetObject * self, PyObject * args)
{
  char **data = NULL, **pointer = NULL;
  int *indicator = NULL;
  int i = 0, type, num = 1;
  T_CCI_SET set;
  int err_code = 0;
  char *temp_data_char;
  T_CCI_BIT *pBit = NULL;

  PyObject *pTube;
  PyObject *pValue;

  if (!PyArg_ParseTuple (args, "Oi", &pTube, &type))
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
    }

  if (!PyTuple_Check (pTube))
    {
      return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
    }
  num = PyTuple_GET_SIZE (pTube);
  data = (char **) _cubrid_get_data_buf (type, num + 1);
  pointer = (char **) _cubrid_get_data_buf (type, num + 1);
  indicator = (int *) _cubrid_dup_buf (NULL, sizeof (int) * (num + 1));


  for (i = 0; i < num; ++i)
    {
      pValue = PyTuple_GET_ITEM (pTube, i);
      pointer[i] = _cubrid_return_PyString_AsString (pValue);

      if (pointer[i] == NULL || (strlen (pointer[i]) == 0))
	{
	  return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
	}

      if (strcmp (pointer[i], "NULL") == 0)
	{
	  indicator[i] = 1;
	}
    }


  if (NULL == indicator || NULL == data)
    {
      return handle_error (CUBRID_ER_NO_MORE_MEMORY, NULL);
    }

  switch (type)
    {
    case CCI_U_TYPE_BIT:
    case CCI_U_TYPE_VARBIT:
      for (i = 0; i < num; i++)
	{
	  if (indicator[i] == 1)
	    continue;
	  temp_data_char = _cubrid_str2bit ((char *) pointer[i]);
	  if (temp_data_char == NULL)
	    {
	      goto handle_error;
	    }
	  pBit = (T_CCI_BIT *) data;
	  pBit[i].buf = temp_data_char;
	  pBit[i].size = strlen ((char *) pointer[i]) / 8 + 1;
	}
      break;
    default:
      err_code =
	cci_set_make (&set, CCI_U_TYPE_STRING, num, pointer,
		      (int *) indicator);
      if (err_code < 0)
	{
	  goto handle_error;
	}
      self->data = set;
      Py_INCREF (Py_None);
      free (data);
      free (indicator);
      free (pointer);
      return Py_None;
    }

  err_code = cci_set_make (&set, type, num, data, (int *) indicator);
  if (err_code < 0)
    {
      goto handle_error;
    }
  self->data = set;

  pBit = (T_CCI_BIT *) data;
  switch (type)
    {
    case CCI_U_TYPE_BIT:
    case CCI_U_TYPE_VARBIT:
      for (i = 0; i < num; i++)
	{
	  if (indicator[i] == 1)
	    continue;
	  if (pBit != NULL && pBit[i].buf != NULL)
	    {
	      free (pBit[i].buf);
	    }
	}
    }

  Py_INCREF (Py_None);
  free (data);
  free (indicator);
  free (pointer);
  return Py_None;

handle_error:
  free (data);
  free (indicator);
  free (pointer);
  return handle_error (CUBRID_ER_INVALID_PARAM, NULL);
}

static char _cubrid_SetObject_import__doc__[] = "imports(data,type)\n\
imports LIST/SET/MULTISET data. To use this function.\n\
data:tuple object\n\
type:Element type of set,default type:string.\n\
\n\
    Example::\n\
from CUBRIDdb import FIELD_TYPE\n\
def one_para():\n\
    con = CUBRIDdb.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
    c = con.cursor()\n\
    set_val=(('1','23','48'),)\n\
    etype = FIELD_TYPE.INT\n\
    c.execute(\"insert into set_tbl_int VALUES(?)\", set_val,etype)\n\
    con.commit();\n\
    c.close()\n\
    con.close() \n\
def two_para():\n\
    con = CUBRIDdb.connect('CUBRID:localhost:33000:demodb:::', 'public')\n\
    c = con.cursor()\n\
    set_val=(('abc','def'),('1','23','48'))\n\
    etype = (FIELD_TYPE.CHAR,FIELD_TYPE.INT)\n\
    c.execute('CREATE TABLE set_tbl_char_int ( col_1 set(CHAR(5)),col_2  set(int));')\n\
    c.execute('insert into set_tbl_int VALUES(?,?)', set_val,etype)\n\
    c.close()\n\
    con.close()";

static PyMethodDef _cubrid_SetObject_methods[] = {
  {
   "imports",
   (PyCFunction) _cubrid_SetObject_import,
   METH_VARARGS,
   _cubrid_SetObject_import__doc__},
  {NULL, NULL}
};

static char _cubrid_SetObject__doc__[] = "Set class.\n\
Process Set,MULTISET and LIST/SEQUENCE type\n\
The class is support by version 9.1.0.0003 and later";

PyTypeObject _cubrid_SetObject_type = {
#if PY_MAJOR_VERSION >= 3
  PyVarObject_HEAD_INIT (NULL, 0)
#else
  PyObject_HEAD_INIT (NULL) 0,	/* ob_size */
#endif
  "_cubrid.set",		/* tp_name */
  sizeof (_cubrid_SetObject),	/* tp_basicsize */
  0,				/* tp_itemsize */
  (destructor) _cubrid_SetObject_dealloc,	/* tp_dealloc */
  0,				/* tp_print */
  0,				/* tp_getattr */
  0,				/* tp_setattr */
  0,				/* tp_compare */
  0,				/* tp_repr */
  0,				/* tp_as_number */
  0,				/* tp_as_sequence */
  0,				/* tp_as_mapping */
  0,				/* tp_hash */
  0,				/* tp_call */
  0,				/* tp_str */
  0,				/* tp_getattro */
  0,				/* tp_setattro */
  0,				/* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
  _cubrid_SetObject__doc__,	/* tp_doc */
  0,				/* tp_traverse */
  0,				/* tp_clear */
  0,				/* tp_richcompare */
  0,				/* tp_weaklistoffset */
  0,				/* tp_iter */
  0,				/* tp_iternext */
  _cubrid_SetObject_methods,	/* tp_methods */
  0,				/* tp_members */
  0,				/* tp_getset */
  0,				/* tp_base */
  0,				/* tp_dict */
  0,				/* tp_descr_get */
  0,				/* tp_descr_set */
  0,				/* tp_dictoffset */
  (initproc) _cubrid_SetObject_init,	/* tp_init */
  0,				/* tp_alloc */
  (newfunc) _cubrid_SetObject_new,	/* tp_new */
  0,				/* tp_free */
};

static PyMethodDef _cubrid_LobObject_methods[] = {
  {
   "export",
   (PyCFunction) _cubrid_LobObject_export,
   METH_VARARGS,
   _cubrid_LobObject_export__doc__},
  {
   "imports",
   (PyCFunction) _cubrid_LobObject_import,
   METH_VARARGS,
   _cubrid_LobObject_import__doc__},
  {
   "write",
   (PyCFunction) _cubrid_LobObject_write,
   METH_VARARGS,
   _cubrid_LobObject_write__doc__},
  {
   "read",
   (PyCFunction) _cubrid_LobObject_read,
   METH_VARARGS,
   _cubrid_LobObject_read__doc__},
  {
   "seek",
   (PyCFunction) _cubrid_LobObject_seek,
   METH_VARARGS,
   _cubrid_LobObject_seek__doc__},

  {
   "close",
   (PyCFunction) _cubrid_LobObject_close,
   METH_VARARGS,
   _cubrid_LobObject_close__doc__},
  {NULL, NULL}
};

static char _cubrid_LobObject__doc__[] = "Lob class.\n\
Process BLOB/CLOB type";

PyTypeObject _cubrid_LobObject_type = {
#if PY_MAJOR_VERSION >= 3
  PyVarObject_HEAD_INIT (NULL, 0)
#else
  PyObject_HEAD_INIT (NULL) 0,	/* ob_size */
#endif
  "_cubrid.lob",		/* tp_name */
  sizeof (_cubrid_LobObject),	/* tp_basicsize */
  0,				/* tp_itemsize */
  (destructor) _cubrid_LobObject_dealloc,	/* tp_dealloc */
  0,				/* tp_print */
  0,				/* tp_getattr */
  0,				/* tp_setattr */
  0,				/* tp_compare */
  0,				/* tp_repr */
  0,				/* tp_as_number */
  0,				/* tp_as_sequence */
  0,				/* tp_as_mapping */
  0,				/* tp_hash */
  0,				/* tp_call */
  0,				/* tp_str */
  0,				/* tp_getattro */
  0,				/* tp_setattro */
  0,				/* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
  _cubrid_LobObject__doc__,	/* tp_doc */
  0,				/* tp_traverse */
  0,				/* tp_clear */
  0,				/* tp_richcompare */
  0,				/* tp_weaklistoffset */
  0,				/* tp_iter */
  0,				/* tp_iternext */
  _cubrid_LobObject_methods,	/* tp_methods */
  0,				/* tp_members */
  0,				/* tp_getset */
  0,				/* tp_base */
  0,				/* tp_dict */
  0,				/* tp_descr_get */
  0,				/* tp_descr_set */
  0,				/* tp_dictoffset */
  (initproc) _cubrid_LobObject_init,	/* tp_init */
  0,				/* tp_alloc */
  (newfunc) _cubrid_LobObject_new,	/* tp_new */
  0,				/* tp_free */
};

static PyMethodDef _cubrid_CursorObject_methods[] = {
  {
   "close",
   (PyCFunction) _cubrid_CursorObject_close,
   METH_VARARGS,
   _cubrid_CursorObject_close__doc__},
  {
   "prepare",
   (PyCFunction) _cubrid_CursorObject_prepare,
   METH_VARARGS,
   _cubrid_CursorObject_prepare__doc__},
  {
   "_set_charset_name",
   (PyCFunction) _cubrid_CursorObject__set_charset_name,
   METH_VARARGS,
   _cubrid_CursorObject__set_charset_name__doc__},
  {
   "bind_param",
   (PyCFunction) _cubrid_CursorObject_bind_param,
   METH_VARARGS,
   _cubrid_CursorObject_bind_param__doc__},
  {
   "bind_lob",
   (PyCFunction) _cubrid_CursorObject_bind_lob,
   METH_VARARGS,
   _cubrid_CursorObject_bind_lob__doc__},
  {
   "bind_set",
   (PyCFunction) _cubrid_CursorObject_bind_Set,
   METH_VARARGS,
   _cubrid_CursorObject_bind_set__doc__},
  {
   "execute",
   (PyCFunction) _cubrid_CursorObject_execute,
   METH_VARARGS,
   _cubrid_CursorObject_execute__doc__},
  {
   "affected_rows",
   (PyCFunction) _cubrid_CursorObject_affected_rows,
   METH_VARARGS,
   _cubrid_CursorObject_affected_rows__doc__},
  {
   "fetch_row",
   (PyCFunction) _cubrid_CursorObject_fetch,
   METH_VARARGS,
   _cubrid_CursorObject_fetch__doc__},
  {
   "fetch_lob",
   (PyCFunction) _cubrid_CursorObject_fetch_lob,
   METH_VARARGS,
   _cubrid_CursorObject_fetch_lob__doc__},
  {
   "data_seek",
   (PyCFunction) _cubrid_CursorObject_data_seek,
   METH_VARARGS,
   _cubrid_CursorObject_data_seek__doc__},
  {
   "num_fields",
   (PyCFunction) _cubrid_CursorObject_num_fields,
   METH_VARARGS,
   _cubrid_CursorObject_num_fields__doc__},
  {
   "num_rows",
   (PyCFunction) _cubrid_CursorObject_num_rows,
   METH_VARARGS,
   _cubrid_CursorObject_num_rows__doc__},
  {
   "row_tell",
   (PyCFunction) _cubrid_CursorObject_row_tell,
   METH_VARARGS,
   _cubrid_CursorObject_row_tell__doc__},
  {
   "row_seek",
   (PyCFunction) _cubrid_CursorObject_row_seek,
   METH_VARARGS,
   _cubrid_CursorObject_row_seek__doc__},
  {
   "result_info",
   (PyCFunction) _cubrid_CursorObject_result_info,
   METH_VARARGS,
   _cubrid_CursorObject_result_info__doc__},
  {
   "next_result",
   (PyCFunction) _cubrid_CursorObject_next_result,
   METH_VARARGS,
   _cubrid_CursorObject_next_result__doc__},
  {NULL, NULL}
};

static PyMethodDef _cubrid_ConnectionObject_methods[] = {
  {
   "close",
   (PyCFunction) _cubrid_ConnectionObject_close,
   METH_VARARGS,
   _cubrid_ConnectionObject_close__doc__},
  {
   "cursor",
   (PyCFunction) _cubrid_ConnectionObject_cursor,
   METH_VARARGS,
   _cubrid_ConnectionObject_cursor__doc__},
  {
   "lob",
   (PyCFunction) _cubrid_ConnectionObject_lob,
   METH_VARARGS,
   _cubrid_ConnectionObject_lob__doc__},
  {
   "set",
   (PyCFunction) _cubrid_ConnectionObject_set,
   METH_VARARGS,
   _cubrid_ConnectionObject_set__doc__},
  {
   "commit",
   (PyCFunction) _cubrid_ConnectionObject_commit,
   METH_VARARGS,
   _cubrid_ConnectionObject_commit__doc__},
  {
   "rollback",
   (PyCFunction) _cubrid_ConnectionObject_rollback,
   METH_VARARGS,
   _cubrid_ConnectionObject_rollback__doc__},
  {
   "ping",
   (PyCFunction) _cubrid_ConnectionObject_ping,
   METH_VARARGS,
   _cubrid_ConnectionObject_ping__doc__},
  {
   "server_version",
   (PyCFunction) _cubrid_ConnectionObject_server_version,
   METH_VARARGS,
   _cubrid_ConnectionObject_server_version__doc__},
  {
   "client_version",
   (PyCFunction) _cubrid_ConnectionObject_client_version,
   METH_VARARGS,
   _cubrid_ConnectionObject_client_version__doc__},
  {
   "set_autocommit",
   (PyCFunction) _cubrid_ConnectionObject_set_autocommit,
   METH_VARARGS,
   _cubrid_ConnectionObject_set_autocommit__doc__},
  {
   "set_isolation_level",
   (PyCFunction) _cubrid_ConnectionObject_set_isolation_level,
   METH_VARARGS,
   _cubrid_ConnectionObject_set_isolation_level__doc__},
  {
   "insert_id",
   (PyCFunction) _cubrid_ConnectionObject_last_insert_id,
   METH_VARARGS,
   _cubrid_ConnectionObject_last_insert_id__doc__},
  {
   "schema_info",
   (PyCFunction) _cubrid_ConnectionObject_schema_info,
   METH_VARARGS,
   _cubrid_ConnectionObject_schema_info__doc__},
  {
   "escape_string",
   (PyCFunction) _cubrid_ConnectionObject_escape_string,
   METH_VARARGS,
   _cubrid_ConnectionObject_escape_string__doc__},
  {
   "batch_execute",
   (PyCFunction) _cubrid_ConnectionObject_batch_execute,
   METH_VARARGS,
   _cubrid_ConnectionObject_batch_execute__doc__},
  {NULL, NULL}
};

static char _cubrid_ConnectionObject__doc__[] =
  "Returns a CUBRID connection object.";

static char _cubrid_CursorObject__doc__[] = "Cursor class.";

static struct PyMemberDef _cubrid_ConnectionObject_members[] = {
  {
   "autocommit",
   T_OBJECT,
   offsetof (_cubrid_ConnectionObject, autocommit),
   0,
   "autocommit status"},
  {
   "isolation_level",
   T_OBJECT,
   offsetof (_cubrid_ConnectionObject, isolation_level),
   0,
   "isolation level"},
  {
   "max_string_len",
   T_OBJECT,
   offsetof (_cubrid_ConnectionObject, max_string_len),
   0,
   "max string length"},
  {
   "lock_timeout",
   T_OBJECT,
   offsetof (_cubrid_ConnectionObject, lock_timeout),
   0,
   "lock time out"},
  {NULL}
};

static PyObject *
_cubrid_ConnectionObject_repr (_cubrid_ConnectionObject * self)
{
  char buf[1024];
  if (self->handle)
    {
      sprintf (buf, "<open CUBRID connection at %s:%s>", self->url,
	       self->user);
    }
  else
    {
      sprintf (buf, "<closed connection at %lx>", (long) self);
    }

  return _cubrid_return_PyString_FromString (buf);
}

static PyObject *
_cubrid_CursorObject_repr (_cubrid_CursorObject * self)
{
  char buf[1024];
  sprintf (buf, "<_cubrid.cursor object at %lx>", (long) self);

  return _cubrid_return_PyString_FromString (buf);
}

static struct PyMemberDef _cubrid_CursorObject_members[] = {
  {
   "description",
   T_OBJECT,
   offsetof (_cubrid_CursorObject, description),
   0,
   "description"},
  {
   "rowcount",
   T_INT,
   offsetof (_cubrid_CursorObject, row_count),
   0,
   "row count"},
  {NULL}
};

static struct PyMethodDef _cubrid_methods[] = {
  {
   "connect",
   (PyCFunction) _cubrid_connect,
   METH_VARARGS | METH_KEYWORDS,
   _cubrid_connect__doc__},
  {
   "escape_string",
   (PyCFunction) _cubrid_escape_string,
   METH_VARARGS | METH_KEYWORDS,
   _cubrid_escape_string__doc__},
  {NULL, NULL}
};

PyTypeObject _cubrid_ConnectionObject_type = {
#if PY_MAJOR_VERSION >= 3
  PyVarObject_HEAD_INIT (NULL, 0)
#else
  PyObject_HEAD_INIT (NULL) 0,	/* ob_size */
#endif
  "_cubrid.connection",		/* tp_name */
  sizeof (_cubrid_ConnectionObject),	/* tp_basicsize */
  0,				/* tp_itemsize */
  (destructor) _cubrid_ConnectionObject_dealloc,	/* tp_dealloc */
  0,				/* tp_print */
  0,				/* tp_getattr */
  0,				/* tp_setattr */
  0,				/* tp_compare */
  (reprfunc) _cubrid_ConnectionObject_repr,	/* tp_repr */
  0,				/* tp_as_number */
  0,				/* tp_as_sequence */
  0,				/* tp_as_mapping */
  0,				/* tp_hash */
  0,				/* tp_call */
  0,				/* tp_str */
  0,				/* tp_getattro */
  0,				/* tp_setattro */
  0,				/* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
  _cubrid_ConnectionObject__doc__,	/* tp_doc */
  0,				/* tp_traverse */
  0,				/* tp_clear */
  0,				/* tp_richcompare */
  0,				/* tp_weaklistoffset */
  0,				/* tp_iter */
  0,				/* tp_iternext */
  _cubrid_ConnectionObject_methods,	/* tp_methods */
  _cubrid_ConnectionObject_members,	/* tp_members */
  0,				/* tp_getset */
  0,				/* tp_base */
  0,				/* tp_dict */
  0,				/* tp_descr_get */
  0,				/* tp_descr_set */
  0,				/* tp_dictoffset */
  (initproc) _cubrid_ConnectionObject_init,	/* tp_init */
  0,				/* tp_alloc */
  (newfunc) _cubrid_ConnectionObject_new,	/* tp_new */
  0,				/* tp_free */
};

PyTypeObject _cubrid_CursorObject_type = {
#if PY_MAJOR_VERSION >= 3
  PyVarObject_HEAD_INIT (NULL, 0)
#else
  PyObject_HEAD_INIT (NULL) 0,	/* ob_size */
#endif
  "_cubrid.cursor",		/* tp_name */
  sizeof (_cubrid_CursorObject),	/* tp_basicsize */
  0,				/* tp_itemsize */
  (destructor) _cubrid_CursorObject_dealloc,	/* tp_dealloc */
  0,				/* tp_print */
  0,				/* tp_getattr */
  0,				/* tp_setattr */
  0,				/* tp_compare */
  (reprfunc) _cubrid_CursorObject_repr,	/* tp_repr */
  0,				/* tp_as_number */
  0,				/* tp_as_sequence */
  0,				/* tp_as_mapping */
  0,				/* tp_hash */
  0,				/* tp_call */
  0,				/* tp_str */
  0,				/* tp_getattro */
  0,				/* tp_setattro */
  0,				/* tp_as_buffer */
  Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,	/* tp_flags */
  _cubrid_CursorObject__doc__,	/* tp_doc */
  0,				/* tp_traverse */
  0,				/* tp_clear */
  0,				/* tp_richcompare */
  0,				/* tp_weaklistoffset */
  0,				/* tp_iter */
  0,				/* tp_iternext */
  _cubrid_CursorObject_methods,	/* tp_methods */
  _cubrid_CursorObject_members,	/* tp_members */
  0,				/* tp_getset */
  0,				/* tp_base */
  0,				/* tp_dict */
  0,				/* tp_descr_get */
  0,				/* tp_descr_set */
  0,				/* tp_dictoffset */
  (initproc) _cubrid_CursorObject_init,	/* tp_init */
  0,				/* tp_alloc */
  (newfunc) _cubrid_CursorObject_new,	/* tp_new */
  0,				/* tp_free */
};

static char _cubrid_doc[] = "CUBRID API Module for Python";

#if PY_MAJOR_VERSION >= 3
static struct PyModuleDef cubriddef = {
  PyModuleDef_HEAD_INIT,
  "_cubrid",
  NULL,
  0,
  _cubrid_methods,
  NULL,
  NULL,
  NULL,
  NULL
};
#endif

/*
 *  pep-0249 Error inheritance layout
 *
 *  StandardError
 *  |__Warning
 *  |__Error
 *     |__InterfaceError
 *     |__DatabaseError
 *        |__DataError
 *        |__OperationalError
 *        |__IntegrityError
 *        |__InternalError
 *        |__ProgrammingError
 *        |__NotSupportedError
 *
 */
void
init_exceptions (PyObject * dict)
{
  _cubrid_error = PyErr_NewException ("_cubrid.Error", PyExc_Exception, NULL);
  PyDict_SetItemString (dict, "Error", _cubrid_error);

  _cubrid_interface_error =
    PyErr_NewException ("_cubrid.InterfaceError", _cubrid_error, NULL);
  PyDict_SetItemString (dict, "InterfaceError", _cubrid_interface_error);

  _cubrid_database_error =
    PyErr_NewException ("_cubrid.DatabaseError", _cubrid_error, NULL);
  PyDict_SetItemString (dict, "DatabaseError", _cubrid_database_error);

  _cubrid_data_error =
    PyErr_NewException ("_cubrid.DataError", _cubrid_database_error, NULL);
  PyDict_SetItemString (dict, "DataError", _cubrid_data_error);

  _cubrid_operational_error =
    PyErr_NewException ("_cubrid.OperationalError", _cubrid_database_error,
			NULL);
  PyDict_SetItemString (dict, "OperationalError", _cubrid_operational_error);

  _cubrid_integrity_error =
    PyErr_NewException ("_cubrid.IntegrityError", _cubrid_database_error,
			NULL);
  PyDict_SetItemString (dict, "IntegrityError", _cubrid_integrity_error);

  _cubrid_internal_error =
    PyErr_NewException ("_cubrid.InternalError", _cubrid_database_error,
			NULL);
  PyDict_SetItemString (dict, "InternalError", _cubrid_internal_error);

  _cubrid_programming_error =
    PyErr_NewException ("_cubrid.ProgrammingError", _cubrid_database_error,
			NULL);
  PyDict_SetItemString (dict, "ProgrammingError", _cubrid_programming_error);

  _cubrid_not_supported_error =
    PyErr_NewException ("_cubrid.NotSupportedError", _cubrid_database_error,
			NULL);
  PyDict_SetItemString (dict, "NotSupportedError",
			_cubrid_not_supported_error);
}

static int
ins (PyObject * d, char *symbol, long value)
{
  PyObject *v = _cubrid_return_PyInt_FromLong (value);
  if (!v || PyDict_SetItemString (d, symbol, v) < 0)
    {
      return -1;
    }

  Py_DECREF (v);
  return 0;
}

static int
all_ins (PyObject * d)
{
  if (ins (d, "CUBRID_EXEC_ASYNC", (long) CUBRID_EXEC_ASYNC))
    return -1;

  if (ins (d, "CUBRID_EXEC_QUERY_ALL", (long) CUBRID_EXEC_QUERY_ALL))
    return -1;

  if (ins (d, "CUBRID_EXEC_QUERY_INFO", (long) CUBRID_EXEC_QUERY_INFO))
    return -1;

  if (ins
      (d, "CUBRID_EXEC_ONLY_QUERY_PLAN", (long) CUBRID_EXEC_ONLY_QUERY_PLAN))
    return -1;

  if (ins (d, "CUBRID_EXEC_THREAD", (long) CUBRID_EXEC_THREAD))
    return -1;

  if (ins
      (d, "CUBRID_REP_CLASS_COMMIT_INSTANCE",
       (long) TRAN_REP_CLASS_COMMIT_INSTANCE))
    return -1;

  if (ins
      (d, "CUBRID_REP_CLASS_REP_INSTANCE",
       (long) TRAN_REP_CLASS_REP_INSTANCE))
    return -1;

  if (ins (d, "CUBRID_SERIALIZABLE", (long) TRAN_SERIALIZABLE))
    return -1;

  if (ins (d, "CUBRID_SCH_TABLE", (long) CCI_SCH_CLASS))
    return -1;

  if (ins (d, "CUBRID_SCH_VIEW", (long) CCI_SCH_VCLASS))
    return -1;

  if (ins (d, "CUBRID_SCH_QUERY_SPEC", (long) CCI_SCH_QUERY_SPEC))
    return -1;

  if (ins (d, "CUBRID_SCH_ATTRIBUTE", (long) CCI_SCH_ATTRIBUTE))
    return -1;

  if (ins (d, "CUBRID_SCH_TABLE_ATTRIBUTE", (long) CCI_SCH_CLASS_ATTRIBUTE))
    return -1;

  if (ins (d, "CUBRID_SCH_METHOD", (long) CCI_SCH_METHOD))
    return -1;

  if (ins (d, "CUBRID_SCH_TABLE_METHOD", (long) CCI_SCH_CLASS_METHOD))
    return -1;

  if (ins (d, "CUBRID_SCH_METHOD_FILE", (long) CCI_SCH_METHOD_FILE))
    return -1;

  if (ins (d, "CUBRID_SCH_SUPERTABLE", (long) CCI_SCH_SUPERCLASS))
    return -1;

  if (ins (d, "CUBRID_SCH_SUBTABLE", (long) CCI_SCH_SUBCLASS))
    return -1;

  if (ins (d, "CUBRID_SCH_CONSTRAINT", (long) CCI_SCH_CONSTRAINT))
    return -1;

  if (ins (d, "CUBRID_SCH_TRIGGER", (long) CCI_SCH_TRIGGER))
    return -1;

  if (ins (d, "CUBRID_SCH_TABLE_PRIVILEGE", (long) CCI_SCH_CLASS_PRIVILEGE))
    return -1;

  if (ins (d, "CUBRID_SCH_COLUMN_PRIVILEGE", (long) CCI_SCH_ATTR_PRIVILEGE))
    return -1;

  if (ins
      (d, "CUBRID_SCH_DIRECT_SUPER_TABLE", (long) CCI_SCH_DIRECT_SUPER_CLASS))
    return -1;

  if (ins (d, "CUBRID_SCH_PRIMARY_KEY", (long) CCI_SCH_PRIMARY_KEY))
    return -1;

  if (ins (d, "CUBRID_SCH_IMPORTED_KEYS", (long) CCI_SCH_IMPORTED_KEYS))
    return -1;

  if (ins (d, "CUBRID_SCH_EXPORTED_KEYS", (long) CCI_SCH_EXPORTED_KEYS))
    return -1;

  if (ins (d, "CUBRID_SCH_CROSS_REFERENCE", (long) CCI_SCH_CROSS_REFERENCE))
    return -1;

  if (ins (d, "SEEK_CUR", (long) SEEK_CUR))
    return -1;

  if (ins (d, "SEEK_SET", (long) SEEK_SET))
    return -1;

  if (ins (d, "SEEK_END", (long) SEEK_END))
    return -1;

  return 0;
}

#if PY_MAJOR_VERSION >= 3
PyObject *
PyInit__cubrid (void)
#else
void
init_cubrid (void)
#endif
{
  PyObject *dict, *module, *mDecimal;

#if PY_MAJOR_VERSION >= 3
  module = PyModule_Create (&cubriddef);
#else
  module =
    Py_InitModule4 ("_cubrid", _cubrid_methods, _cubrid_doc,
		    (PyObject *) NULL, PYTHON_API_VERSION);
#endif

  if (!(dict = PyModule_GetDict (module)))
    {
      goto Error;
    }

  init_exceptions (dict);
  all_ins (dict);
  PyDict_SetItemString (dict, "__version__",
			PyString_FromString (_CUBRID_VERSION_));

  if (PyType_Ready (&_cubrid_ConnectionObject_type) < 0)
    {
      goto Error;
    }

  Py_INCREF (&_cubrid_ConnectionObject_type);
  if (PyModule_AddObject
      (module, "connection",
       (PyObject *) & _cubrid_ConnectionObject_type) < 0)
    {
      goto Error;
    }

  if (PyType_Ready (&_cubrid_CursorObject_type) < 0)
    {
      goto Error;
    }

  Py_INCREF (&_cubrid_CursorObject_type);
  if (PyModule_AddObject
      (module, "cursor", (PyObject *) & _cubrid_CursorObject_type) < 0)
    {
      goto Error;
    }

  if (PyType_Ready (&_cubrid_LobObject_type) < 0)
    {
      goto Error;
    }

  Py_INCREF (&_cubrid_LobObject_type);
  if (PyModule_AddObject
      (module, "lob", (PyObject *) & _cubrid_LobObject_type) < 0)
    {
      goto Error;
    }

  if (PyType_Ready (&_cubrid_SetObject_type) < 0)
    {
      goto Error;
    }

  Py_INCREF (&_cubrid_SetObject_type);
  if (PyModule_AddObject
      (module, "set", (PyObject *) & _cubrid_SetObject_type) < 0)
    {
      goto Error;
    }

  /* import function Decimal from module decimal */
  mDecimal = PyImport_ImportModule ("decimal");
  if (!mDecimal)
    {
      goto Error;
    }

  _func_Decimal = PyObject_GetAttrString (mDecimal, "Decimal");
  if (!_func_Decimal)
    {
      goto Error;
    }

  Py_INCREF (_func_Decimal);
  Py_DECREF (mDecimal);

  /* invoke PyDateTime_IMPORT macro to use functions from datetime.h */
  PyDateTime_IMPORT;

#if PY_MAJOR_VERSION >= 3
  return module;
#else
  return;
#endif

Error:
  if (PyErr_Occurred ())
    {
      PyErr_SetString (PyExc_ImportError, "_cubrid: init failure");
    }

#if PY_MAJOR_VERSION >= 3
  return NULL;
#else
  return;
#endif
}
