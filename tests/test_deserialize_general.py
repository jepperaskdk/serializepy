from typing import Any, Dict, List
from serializepy import serialize, deserialize


def test_list_int() -> None:
    d = [1, 2, 3]

    obj: List[int] = deserialize(List[int], d)

    assert obj == [1, 2, 3]


def test_list_list_int() -> None:
    d = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

    obj: List[List[int]] = deserialize(List[List[int]], d)

    assert obj == [[1, 2, 3], [4, 5, 6], [7, 8, 9]]


def test_dict_str_any() -> None:
    d = {'a': 1, 'b': 2, 'c': 3}

    obj: Dict[str, Any] = deserialize(Dict[str, Any], d)
    assert obj == {'a': 1, 'b': 2, 'c': 3}


def test_dict_str_dict_str_any() -> None:
    d = { 'q': {'a': 1, 'b': 2, 'c': 3}, 'w': {'a': 4, 'b': 5, 'c': 6}, 'z': {'a': 7, 'b': 8, 'c': 9}}

    obj: Dict[str, Dict[str, Any]] = deserialize(Dict[str, Dict[str, Any]], d)

    assert obj == {'q': {'a': 1, 'b': 2, 'c': 3}, 'w': {'a': 4, 'b': 5, 'c': 6}, 'z': {'a': 7, 'b': 8, 'c': 9}}
