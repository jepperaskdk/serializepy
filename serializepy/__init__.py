import builtins
import inspect
import ast
import textwrap
from pydoc import locate

from types import FunctionType, ModuleType
from typing import Optional, List, Any, Dict, TypeVar, Type, cast, get_type_hints


PRIMITIVES = [int, float, bool, str]
T = TypeVar('T')


class SelfVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.nodes: List[ast.AnnAssign] = []

    def visit(self, n: ast.AST) -> None:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Attribute):
            if isinstance(n.target.value, ast.Name) and n.target.value.id == 'self':
                self.nodes.append(n)
        super().visit(n)


class Annotation():
    def __init__(self, name: str, type: Type) -> None:
        self.name = name
        self.type = type


class ASTParseResult():
    # https://docs.python.org/3/library/ast.html#ast.AnnAssign
    # TODO: If we don't have an annotation, check the signature of __init__?

    def parse(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        anno = self.parse_primitive(tree)
        if anno:
            return anno

        anno = self.parse_list(tree)
        if anno:
            return anno

        return None

    def parse_primitive(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        if isinstance(tree.annotation, ast.Name) and isinstance(tree.value, ast.Name):
            type = tree.annotation.id
            name = tree.value.id
            located_type: Type = cast(Type, locate(type))
            return Annotation(name, located_type)
        return None

    def parse_list(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        if isinstance(tree.annotation, ast.Subscript):
            t = 123
        raise NotImplementedError()

    def parse_dict(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        raise NotImplementedError()


def get_annotations(type: Type[T]) -> List[Annotation]:
    type_source = inspect.getsource(type)
    max_indents = 10

    # Try to parse, and if IndentationError, dedent up to 10 times.
    while max_indents > 0:
        try:
            tree = ast.parse(type_source)
            break
        except IndentationError as e:
            type_source = textwrap.dedent(type_source)
            max_indents -= 1

    visitor = SelfVisitor()
    visitor.generic_visit(tree)
    annotations: List[Annotation] = []
    for n in visitor.nodes:
        parser = ASTParseResult()
        annotation = parser.parse(n)
        if annotation is None:
            name = n.target.attr if isinstance(n.target, ast.Attribute) else 'unknown'
            raise Exception(f"Was unable to find name/type for {name}")
        annotations.append(annotation)
    return annotations


def deserialize(t: Type[T], o: Dict[str, Any]) -> T:
    a = t.__dict__
    b = inspect.getmembers(t)
    c = get_type_hints(t)

    annotations = get_annotations(t)
    obj: T = t.__new__(t)
    for anno in annotations:
        if anno.type in PRIMITIVES:
            setattr(obj, anno.name, o[anno.name])
        else:
            pass
    return obj


def serialize(o: Any) -> Dict[str, Any]:
    raise NotImplementedError()