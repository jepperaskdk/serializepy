from serializepy import deserialize


class A():
    def __init__(self, a: int) -> None:
        self.a: int = a


class B(A):
    def __init__(self, a: int, b: int) -> None:
        super().__init__(a)

        self.b: int = b


def test_inheritance() -> None:
    d = {
        'a': 5,
        'b': 7
    }

    obj: B = deserialize(B, d)

    assert isinstance(obj, B)
    assert obj.a == 5
    assert obj.b == 7


class GrandGrand():
    def __init__(self, grand_grand: int) -> None:
        self.grand_grand: int = grand_grand


class Grand(GrandGrand):
    def __init__(self, grand: int, grand_grand: int) -> None:
        super().__init__(grand_grand)
        self.grand: int = grand


class Child(Grand):
    def __init__(self, child: int, grand: int, grand_grand: int) -> None:
        super().__init__(grand, grand_grand)
        self.child: int = child


def test_multiple_ancestors() -> None:
    d = {
        'child': 5,
        'grand': 7,
        'grand_grand': 9,
    }

    obj: Child = deserialize(Child, d)

    assert isinstance(obj, Child)
    assert obj.child == 5
    assert obj.grand == 7
    assert obj.grand_grand == 9


class Base():
    def __init__(self, a: int) -> None:
        self.a: int = a


class Example(Base):
    pass


def test_without_constructor() -> None:
    d = {
        'a': 123
    }
    obj: Example = deserialize(Example, d)
    assert isinstance(obj, Example)
    assert obj.a == 123
