serializepy: typed deserialization
=======================================
![example workflow](https://github.com/jepperaskdk/serializepy/actions/workflows/python-package.yml/badge.svg)
[![PyPI version serializepy](https://badge.fury.io/py/serializepy.svg)](https://pypi.python.org/pypi/serializepy/)


File issues here: [Issues tracker](https://github.com/jepperaskdk/serializepy/issues)

Motivation
------------

serializepy inspects the type-hints of self-assignments in class-constructors, and constructs the type from a given dictionary. The goal is to support this work recursively for large and complex (typed) hierarchies.


Installation
-----------

Install serializepy with pip:

    $ python3 -m pip install serializepy

Usage
-----------
```
# Example class hierarchy
class B():
    def __init__(self, b: int) -> None:
        self.b: int = b


class A():
    def __init__(self, a: int, b: B) -> None:
        self.a: int = a
        self.b: B = b

# Data that we want to fit the above hierarchy, possibly from json.load(..)
d = {
    'a': 1,
    'b': {
        'b': 2
    }
}

# Deserialization and assertion
obj: A = deserialize(A, d)
assert isinstance(obj, A)
assert obj.a == 1
assert isinstance(obj.b, B)
assert obj.b.b == 2

```

Inheritance:
```
class A():
    def __init__(self, a: int) -> None:
        self.a: int = a

class B(A):
    def __init__(self, a: int, b: int) -> None:
        super().__init__(a)
        self.b: int = b
d = {
    'a': 5,
    'b': 7
}

obj: B = deserialize(B, d)

assert isinstance(obj, B)
assert obj.a == 5
assert obj.b == 7
```


License
-----------

serializepy is licensed under the terms of the MIT License (see the LICENSE file).
