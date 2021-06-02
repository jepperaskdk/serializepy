from typing import Any, Dict, List
from serializepy import serialize, deserialize


class TestClass_int_bool():
    def __init__(self, a: int, b: bool) -> None:
        self.a: int = a
        self.b: bool = b
        d: int = 2                  # Make sure this isn't used


def test_testclass_int_bool() -> None:
    d = {
        'a': 5,
        'b': True
    }

    obj: TestClass_int_bool = deserialize(TestClass_int_bool, d)

    assert obj.a == 5
    assert obj.b
    assert not hasattr(obj, 'd')


class TestClass_List_int():
    def __init__(self, c: List[int]) -> None:
        self.c: List[int] = c


def test_list_int() -> None:
    d = {
        'c': [1, 2, 3],
    }

    obj: TestClass_List_int = deserialize(TestClass_List_int, d)

    assert obj.c == [1, 2, 3]


class TestClass_List_List_int():
    def __init__(self, e: List[List[int]]) -> None:
        self.e: List[List[int]] = e


def test_list_list_int() -> None:
    d = {
        'e': [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    }

    obj: TestClass_List_List_int = deserialize(TestClass_List_List_int, d)

    assert obj.e == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


class TestClass_Dict_str_Any():
    def __init__(self, f: Dict[str, Any]) -> None:
        self.f: Dict[str, int] = f


def test_dict_str_any() -> None:
    d = {
        'f': {'a': 1, 'b': 2, 'c': 3},
    }

    obj: TestClass_Dict_str_Any = deserialize(TestClass_Dict_str_Any, d)
    assert obj.f == {'a': 1, 'b': 2, 'c': 3}


class TestClass_Dict_str_Dict_str_Any():
    def __init__(self, g: Dict[str, Dict[str, Any]]) -> None:
        self.g: Dict[str, Dict[str, int]] = g


def test_dict_str_dict_str_any() -> None:
    d = {
        'g': { 'q': {'a': 1, 'b': 2, 'c': 3}, 'w': {'a': 4, 'b': 5, 'c': 6}, 'z': {'a': 7, 'b': 8, 'c': 9}}
    }

    obj: TestClass_Dict_str_Dict_str_Any = deserialize(TestClass_Dict_str_Dict_str_Any, d)

    assert obj.g == {'q': {'a': 1, 'b': 2, 'c': 3}, 'w': {'a': 4, 'b': 5, 'c': 6}, 'z': {'a': 7, 'b': 8, 'c': 9}}


class B():
    def __init__(self, b: int) -> None:
        self.b: int = b


class A():
    def __init__(self, a: int, b: B) -> None:
        self.a: int = a
        self.b: B = b


def test_deserialize_nested_class() -> None:
    d = {
        'a': 1,
        'b': {
            'b': 2
        }
    }

    obj: A = deserialize(A, d)
    assert isinstance(obj, A)
    assert obj.a == 1
    assert isinstance(obj.b, B)
    assert obj.b.b == 2
