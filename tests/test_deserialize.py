from typing import Any, Dict, List
from serializepy import serialize, deserialize


class TestClass1():
    def __init__(self, a: int, b: bool) -> None:
        self.a: int = a
        self.b: bool = b
        d: int = 2                  # Make sure this isn't used


def test_deserialize_simple() -> None:
    d = {
        'a': 5,
        'b': True,
        'c': [1, 2, 3]
    }

    obj: TestClass1 = deserialize(TestClass1, d)

    assert obj.a == 5
    assert obj.b
    assert not hasattr(obj, 'd')


class TestClass2():
    def __init__(self, c: List[int], e: List[List[int]]) -> None:
        self.c: List[int] = c
        self.e: List[List[int]] = e
        # self.k = e[1:2]


def test_deserialize_list() -> None:
    d = {
        'c': [1, 2, 3],
        'e': [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    }

    obj: TestClass2 = deserialize(TestClass2, d)

    assert obj.c == [1, 2, 3]
    assert obj.e == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


class TestClass3():
    def __init__(self, f: Dict[str, Any], g: Dict[str, Dict[str, Any]]) -> None:
        self.f: Dict[str, int] = f
        self.g: Dict[str, Dict[str, int]] = g


def test_deserialize_dict() -> None:
    d = {
        'f': {'a': 1, 'b': 2, 'c': 3},
        'g': { 'q': {'a': 1, 'b': 2, 'c': 3}, 'w': {'a': 4, 'b': 5, 'c': 6}, 'z': {'a': 7, 'b': 8, 'c': 9}}
    }

    obj: TestClass3 = deserialize(TestClass3, d)

    assert obj.f == {'a': 1, 'b': 2, 'c': 3}
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
    assert obj.a == 1
    assert isinstance(obj.b, B)
    assert obj.b.b == 2
