import sys
import inspect
import ast
import textwrap

from types import ModuleType
from typing import Optional, List, Any, Dict, TypeVar, Type, cast

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
    def __init__(self, module: ModuleType) -> None:
        self.module = module

    def parse(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        raise NotImplementedError()


class ASTParseResult_3_9(ASTParseResult):
    def parse(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        anno = self.__parse_name(tree)
        if anno:
            return anno

        anno = self.__parse_subscript(tree)
        if anno:
            return anno

        return None

    def __parse_name(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        if isinstance(tree.annotation, ast.Name) and isinstance(tree.value, ast.Name):
            type = tree.annotation.id
            name = tree.value.id
            located_type: Type = get_type_from_module(type, self.module)
            return Annotation(name, located_type)
        return None

    def __parse_subscript(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        def rec(t: ast.expr) -> str:
            result = ""
            if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name):
                result = t.value.id

                if isinstance(t.slice, ast.Subscript):
                    # one generic type
                    r = rec(t.slice)
                    result += f"[{r}]"
                elif isinstance(t.slice, ast.Tuple):
                    # multiple generic types
                    key_t, val_t = cast(List[ast.Name], t.slice.elts)
                    r = rec(val_t)
                    result += f"[{key_t.id}, {r}]"
                elif isinstance(t.slice, ast.Name):
                    result += f"[{t.slice.id}]"
            if isinstance(t, ast.Name):
                return t.id
            return result

        if isinstance(tree.annotation, ast.Subscript) and isinstance(tree.value, ast.Name):
            name = tree.value.id
            type_string = rec(tree.annotation)
            typ = get_type_from_module(type_string, self.module)
            return Annotation(name, typ)

        return None


class ASTParseResult_3_6(ASTParseResult):
    # https://docs.python.org/3/library/ast.html#ast.AnnAssign
    # TODO: If we don't have an annotation, check the signature of __init__?
    def parse(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        anno = self.__parse_name(tree)
        if anno:
            return anno

        anno = self.__parse_subscript(tree)
        if anno:
            return anno

        return None

    def __parse_name(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        if isinstance(tree.annotation, ast.Name) and isinstance(tree.value, ast.Name):
            type = tree.annotation.id
            name = tree.value.id
            located_type: Type = get_type_from_module(type, self.module)
            return Annotation(name, located_type)
        return None

    def __parse_subscript(self, tree: ast.AnnAssign) -> Optional[Annotation]:
        def rec(t: ast.expr) -> str:
            result = ""
            if isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name):
                result = t.value.id

                if isinstance(t.slice, ast.Index) and isinstance(t.slice.value, ast.Subscript):
                    # one generic type
                    r = rec(t.slice.value)
                    result += f"[{r}]"
                elif isinstance(t.slice, ast.Index) and isinstance(t.slice.value, ast.Tuple):
                    # multiple generic types
                    key_t, val_t = cast(List[ast.Name], t.slice.value.elts)
                    r = rec(val_t)
                    result += f"[{key_t.id}, {r}]"
                elif isinstance(t.slice, ast.Index) and isinstance(t.slice.value, ast.Name):
                    result += f"[{t.slice.value.id}]"
            if isinstance(t, ast.Name):
                return t.id
            return result

        if isinstance(tree.annotation, ast.Subscript) and isinstance(tree.value, ast.Name):
            name = tree.value.id
            type_string = rec(tree.annotation)
            typ = get_type_from_module(type_string, self.module)
            return Annotation(name, typ)

        return None


def get_ast_parser_type(module: ModuleType) -> ASTParseResult:
    if sys.version_info >= (3, 9):
        return ASTParseResult_3_9(module)
    else:
        return ASTParseResult_3_6(module)


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
        parser = get_ast_parser_type(module)
        annotation = parser.parse(n)
        if annotation is None:
            name = n.target.attr if isinstance(n.target, ast.Attribute) else 'unknown'
            raise Exception(f"Was unable to find name/type for {name}")
        else:
            annotations.append(annotation)
    return annotations


# Inspired by https://stackoverflow.com/a/54241536/3717691
def get_type_class(typ: Type) -> Type:
    if sys.version_info >= (3, 7):
        if hasattr(typ, '__origin__'):
            return typ.__origin__
    else:
        if hasattr(typ, '__extra__'):
            return typ.__extra__
    return typ


def deserialize(t: Type[T], obj: Any) -> T:
    if t in PRIMITIVES or t == Any:
        # TODO: Parse primitives? E.g. '1' => 1, if t == int
        return obj
    elif issubclass(get_type_class(t), List) and hasattr(t, '__args__'):
        generic: Type = cast(Type, t).__args__[0]
        return cast(T, [deserialize(generic, o) for o in obj])
    elif issubclass(get_type_class(t), Dict) and hasattr(t, '__args__'):
        key_t, val_t = cast(Type, t).__args__
        return cast(T, {k: deserialize(val_t, v) for k, v in obj.items()})
    elif inspect.isclass(t):
        annotations = get_annotations(t)
        o: T = t.__new__(t)

        for anno in annotations:
            val = deserialize(anno.type, obj[anno.name])
            setattr(o, anno.name, val)
        return o
    raise Exception(f"Not sure how to parse this type: {t}")


def serialize(o: Any) -> Dict[str, Any]:
    raise NotImplementedError()
