from typing import Any, Dict, List
from serializepy import serialize, deserialize


class TestClass1():
    def __init__(self, a: int, b: bool) -> None:
        self.a: int = a
        self.b: bool = b
        d: int = 2                  # Make sure this isn't used


class TestClass2():
    def __init__(self, c: List[int], e: List[List[int]]) -> None:
        self.c: List[int] = c
        self.e: List[List[int]] = e
        # self.k = e[1:2]


class TestClass3():
    def __init__(self, f: Dict[str, Any], g: Dict[str, Dict[str, Any]]) -> None:
        self.f: Dict[str, Any] = f
        self.g: Dict[str, Dict[str, Any]] = g


class TestDeserialize():
    def test_deserialize_simple(self) -> None:
        d = {
            'a': 5,
            'b': True,
            'c': [1, 2, 3]
        }

        obj: TestClass1 = deserialize(TestClass1, d)

        assert obj.a == 5
        assert obj.b
        assert not hasattr(obj, 'd')

    def test_deserialize_list(self) -> None:
        d = {
            'c': [1, 2, 3],
            'e': [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        }

        obj: TestClass2 = deserialize(TestClass2, d)

        # assert obj.c == [1, 2, 3]
        # assert obj.e == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    def test_deserialize_dict(self) -> None:
        d = {
            'c': {'a': 1, 'b': 2, 'c': 3},
            'e': {{'a': 1, 'b': 2, 'c': 3}, {'a': 4, 'b': 5, 'c': 6}, {'a': 7, 'b': 8, 'c': 9}}
        }

        obj: TestClass2 = deserialize(TestClass2, d)

        assert obj.c == {'a': 1, 'b': 2, 'c': 3}
        assert obj.e == {{'a': 1, 'b': 2, 'c': 3}, {'a': 4, 'b': 5, 'c': 6}, {'a': 7, 'b': 8, 'c': 9}}