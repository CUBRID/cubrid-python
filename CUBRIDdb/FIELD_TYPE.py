"""CUBRID FIELD_TYPE Constants

These constants represent the various column (field) types that are
supported by CUBRID.

This numbers should be consistent with T_CCI_U_TYPE in cas_cci.h

"""

CHAR    = 1
VARCHAR = 2
NCHAR   = 3
VARNCHAR = 4

BIT     = 5
VARBIT  = 6

NUMERIC = 7
INT     = 8
SMALLINT = 9
MONETARY = 10

FLOAT   = 11
DOUBLE  = 12

DATE    = 13
TIME    = 14
TIMESTAMP   = 15

SET     = 16
MULTISET    = 17
SEQUENCE    = 18

OBJECT = 19

BIGINT = 21
DATETIME = 22

BLOB        = 23
CLOB        = 24

STRING = VARCHAR
