import builtins
from functools import reduce
import inspect
import ast
import textwrap
from pydoc import locate

from types import FunctionType, ModuleType
from typing import Optional, List, Any, Dict, TypeVar, Type, cast, get_type_hints

from serializepy.utilities import get_type_from_module


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
    def __init__(self, module: ModuleType) -> None:
        self.module = module

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
        def rec(t: ast.expr) -> str:
            result = ""
            if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name):
                result = t.value.id

                if isinstance(t.slice, ast.Index) and isinstance(t.slice.value, ast.Subscript):
                    r = rec(t.slice.value)
                    result += f"[{r}]"
                elif isinstance(t.slice, ast.Index) and isinstance(t.slice.value, ast.Name):
                    result += f"[{t.slice.value.id}]"
            return result

        if isinstance(tree.annotation, ast.Subscript) and isinstance(tree.value, ast.Name):
            name = tree.value.id
            type_string = rec(tree.annotation)
            typ = get_type_from_module(type_string, self.module)
            return Annotation(name, typ)

        return None

    def parse_dict(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        raise NotImplementedError()

    def test(self) -> None:
        reduce(lambda x, b: x, ['List', 'List', 'int'], "")


def get_annotations(type: Type[T]) -> List[Annotation]:

    type_source = inspect.getsource(type)
    module = inspect.getmodule(type)
    if module is None:
        # TODO: It might still work for all builtin types etc.
        raise Exception(f"Couldn't detect module of type: {type}")

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
        parser = ASTParseResult(module)
        annotation = parser.parse(n)
        if annotation is None:
            name = n.target.attr if isinstance(n.target, ast.Attribute) else 'unknown'
            # raise Exception(f"Was unable to find name/type for {name}")
        else:
            annotations.append(annotation)
    return annotations


def deserialize(t: Type[T], o: Dict[str, Any]) -> T:
    a = t.__dict__
    b = inspect.getmembers(t)
    c = get_type_hints(t)

    annotations = get_annotations(t)
    obj: T = t.__new__(t)

    def get_parsed(annotation: Annotation) -> Any:
        if anno.type in PRIMITIVES:
            return o[anno.name]

        # WORK IN PROGRESS, make this recursive.

    for anno in annotations:
        val = get_parsed(anno)
        setattr(obj, anno.name, val)

        if anno.type in PRIMITIVES:
            setattr(obj, anno.name, o[anno.name])
        elif issubclass(anno.type, List):
            if hasattr(anno.type, '__args__') and anno.type.__args__:
                generic = anno.type.__args__[0]
                if generic in PRIMITIVES:
                    lst = []
                    setattr(obj, anno.name, o[anno.name])
                elif issubclass(generic, List):

            else:
                setattr(obj, anno.name, o[anno.name])
            t = 123
        elif issubclass(anno.type, Dict):
            pass
        elif inspect.isclass(anno.type):
            setattr(obj, anno.name, deserialize(anno.type, o[anno.name]))
        else:
            raise Exception(f"Not sure how to parse this type: {anno.type}")
    return obj


def serialize(o: Any) -> Dict[str, Any]:
    raise NotImplementedError()
