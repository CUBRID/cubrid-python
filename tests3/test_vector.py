from types import MethodType, SimpleNamespace

import CUBRIDdb
from CUBRIDdb import FIELD_TYPE
from CUBRIDdb.cursors import BaseCursor


class _FakeLowLevelCursor:
    def __init__(self):
        self.bind_param_calls = []

    def bind_param(self, index, value, bind_type=None):
        self.bind_param_calls.append((index, value, bind_type))


def _make_cursor():
    cursor = BaseCursor.__new__(BaseCursor)
    cursor._cs = _FakeLowLevelCursor()
    cursor.con = SimpleNamespace(connection=None)
    return cursor


def test_field_type_vector_constant():
    assert FIELD_TYPE.VECTOR == 41
    assert CUBRIDdb.VECTOR == FIELD_TYPE.VECTOR


def test_bind_params_uses_vector_binding_when_requested():
    cursor = _make_cursor()
    bind_set_calls = []

    def _bind_set(self, index, value, element_type=None):
        bind_set_calls.append((index, value, element_type))

    cursor._bind_set = MethodType(_bind_set, cursor)
    cursor._bind_params(([1.5, 2.25, 3.0],), set_type=FIELD_TYPE.VECTOR)

    assert cursor._cs.bind_param_calls == [(1, [1.5, 2.25, 3.0], FIELD_TYPE.VECTOR)]
    assert bind_set_calls == []


def test_bind_params_keeps_collection_binding_by_default():
    cursor = _make_cursor()
    bind_set_calls = []

    def _bind_set(self, index, value, element_type=None):
        bind_set_calls.append((index, value, element_type))

    cursor._bind_set = MethodType(_bind_set, cursor)
    cursor._bind_params(((1.0, 2.0),))

    assert cursor._cs.bind_param_calls == []
    assert bind_set_calls == [(1, (1.0, 2.0), None)]
