#include "Python.h"
#include "structmember.h"
#include "datetime.h"
#include "cas_cci.h"

#if PY_MAJOR_VERSION >= 3
#define PyString_FromString PyBytes_FromString
#define PyString_AsString PyBytes_AsString
#define PyString_Check PyBytes_Check
#endif

#define CUBRID_ER_NO_MORE_MEMORY	    -30001
#define CUBRID_ER_INVALID_SQL_TYPE	    -30002
#define CUBRID_ER_CANNOT_GET_COLUMN_INFO    -30003
#define CUBRID_ER_INIT_ARRAY_FAIL           -30004
#define CUBRID_ER_UNKNOWN_TYPE              -30005
#define CUBRID_ER_INVALID_PARAM             -30006
#define CUBRID_ER_INVALID_ARRAY_TYPE        -30007
#define CUBRID_ER_NOT_SUPPORTED_TYPE        -30008
#define CUBRID_ER_OPEN_FILE                 -30009
#define CUBRID_ER_CREATE_TEMP_FILE          -30010
#define CUBRID_ER_INVALID_CURSOR_POS	    -30012
#define CUBRID_ER_SQL_UNPREPARE		    -30013
#define CUBRID_ER_PARAM_UNBIND		    -30014
#define CUBRID_ER_SCHEMA_TYPE               -30015
#define CUBRID_ER_READ_FILE                 -30016
#define CUBRID_ER_WRITE_FILE                -30017
#define CUBRID_ER_LOB_NOT_EXIST             -30018
#define CUBRID_ER_INVALID_CURSOR            -30019
#define CUBRID_ER_END                       -31000

#define CUBRID_EXEC_ASYNC           CCI_EXEC_ASYNC
#define CUBRID_EXEC_QUERY_ALL       CCI_EXEC_QUERY_ALL
#define CUBRID_EXEC_QUERY_INFO      CCI_EXEC_QUERY_INFO
#define CUBRID_EXEC_ONLY_QUERY_PLAN CCI_EXEC_ONLY_QUERY_PLAN
#define CUBRID_EXEC_THREAD          CCI_EXEC_THREAD

#define SHRT_MIN_STR     "-32768"       /* minimum (signed) short value */
#define SHRT_MAX_STR       "32767"         /* maximum (signed) short value */
#define INT_MIN_STR     "-2147483648"/* minimum (signed) int value */
#define INT_MAX_STR       "2147483647"    /* maximum (signed) int value */
#define LLONG_MAX_STR     "9223372036854775807"       /* maximum signed long long int value */
#define LLONG_MIN_STR   "-9223372036854775807" /* minimum signed long long int value */
#define DBL_MAX_STR       "1.7976931348623158e+308" /* max value */
#define DBL_MIN_STR         "2.2250738585072014e-308" /* min positive value */
#define FLT_MAX_STR         "3.402823466e+38F"        /* max value */
#define FLT_MIN_STR         "1.175494351e-38F"        /* min positive value */


#ifdef MS_WINDOWS
#define CUBRID_LONG_LONG _int64
#else
#define CUBRID_LONG_LONG long long
#endif

typedef enum
{
  CURSOR_STATE_CLOSED,
  CURSOR_STATE_OPENED
} CURSOR_STATE;

typedef struct
{
  PyObject_HEAD
  int handle;
  char *url;
  char *user;
  char *passwd;
  PyObject *autocommit;
  PyObject *isolation_level;
  PyObject *max_string_len;
  PyObject *lock_timeout;
} _cubrid_ConnectionObject;

typedef struct
{
  PyObject_HEAD
  CURSOR_STATE state;
  int handle;
  int connection;  
  int col_count;
  int row_count;
  int bind_num;
  int cursor_pos;
  char charset[128];
  T_CCI_CUBRID_STMT sql_type;
  T_CCI_COL_INFO *col_info;
  PyObject *description;  
} _cubrid_CursorObject;

typedef struct
{
  PyObject_HEAD
  int connection;
  T_CCI_BLOB blob;
  T_CCI_CLOB clob;
  char type;
  CUBRID_LONG_LONG pos;
} _cubrid_LobObject;

typedef struct
{
  PyObject_HEAD
  int connection;
  T_CCI_SET data;
  char type;
  CUBRID_LONG_LONG pos;
} _cubrid_SetObject;


extern PyTypeObject _cubrid_ConnectionObject_type;
extern PyTypeObject _cubrid_CursorObject_type;
extern PyTypeObject _cubrid_LobObject_type;
extern PyTypeObject _cubrid_SetObject_type;

extern int ut_str_to_bigint (char *str, CUBRID_LONG_LONG * value);
extern int ut_str_to_int (char *str, int *value);
extern int ut_str_to_float (char *str, float *value);
extern int ut_str_to_double (char *str, double *value);
extern int ut_str_to_date (char *str, T_CCI_DATE * value);
extern int ut_str_to_time (char *str, T_CCI_DATE * value);
extern int ut_str_to_mtime (char *str, T_CCI_DATE * value);
extern int ut_str_to_timestamp (char *str, T_CCI_DATE * value);
extern int ut_str_to_datetime (char *str, T_CCI_DATE * value);