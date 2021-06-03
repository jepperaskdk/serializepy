import sys
import inspect
import ast
import textwrap

from types import ModuleType
from typing import Optional, List, Any, Dict, TypeVar, Type, Union, cast

from serializepy.utilities import get_type_from_module
from serializepy.visitors import SelfVisitor, SuperVisitor


PRIMITIVES = [int, float, bool, str]
T = TypeVar('T')


class Annotation():
    def __init__(self, name: str, type: Type) -> None:
        self.name = name
        self.type = type


class ASTParseResult():
    def __init__(self, module: ModuleType, signature_parameters: Dict[str, Type]) -> None:
        self.module = module
        self.signature_parameters = signature_parameters

    def parse(self, tree: Union[ast.AnnAssign, ast.Assign]) -> Optional[Annotation]:
        raise NotImplementedError()


class ASTParseResult_3_9(ASTParseResult):
    def parse(self, tree: Union[ast.AnnAssign, ast.Assign]) -> Optional[Annotation]:
        anno = self.__parse_name(tree)
        if anno:
            return anno

        anno = self.__parse_subscript(tree)
        if anno:
            return anno

        return None

    def __parse_name(self, tree: Union[ast.AnnAssign, ast.Assign]) -> Optional[Annotation]:
        if isinstance(tree, ast.AnnAssign) and isinstance(tree.annotation, ast.Name) and isinstance(tree.target, ast.Attribute):
            name = tree.target.attr
            type_string = tree.annotation.id
            located_type: Type = get_type_from_module(type_string, self.module)
            return Annotation(name, located_type)
        elif isinstance(tree, ast.Assign) and isinstance(tree.value, ast.Name):
            name = tree.value.id
            typ = self.signature_parameters.get(name, None)
            if typ is None:
                raise Exception(f"Unable to get type for variable {name}")
            return Annotation(name, typ)
        return None

    def __parse_subscript(self, tree: Union[ast.AnnAssign, ast.Assign]) -> Optional[Annotation]:
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

        if isinstance(tree, ast.AnnAssign) and isinstance(tree.annotation, ast.Subscript) and isinstance(tree.value, ast.Name):
            name = tree.value.id
            type_string = rec(tree.annotation)
            typ = get_type_from_module(type_string, self.module)
            return Annotation(name, typ)

        return None


class ASTParseResult_3_6(ASTParseResult):
    # https://docs.python.org/3/library/ast.html#ast.AnnAssign
    def parse(self, tree: Union[ast.AnnAssign, ast.Assign]) -> Optional[Annotation]:
        anno = self.__parse_name(tree)
        if anno:
            return anno

        anno = self.__parse_subscript(tree)
        if anno:
            return anno

        return None

    def __parse_name(self, tree: Union[ast.AnnAssign, ast.Assign]) -> Optional[Annotation]:
        if isinstance(tree, ast.AnnAssign) and isinstance(tree.annotation, ast.Name) and isinstance(tree.target, ast.Attribute):
            name = tree.target.attr
            type = tree.annotation.id
            located_type: Type = get_type_from_module(type, self.module)
            return Annotation(name, located_type)
        elif isinstance(tree, ast.Assign) and isinstance(tree.value, ast.Name):
            name = tree.value.id
            typ = self.signature_parameters.get(name, None)
            if typ is None:
                raise Exception(f"Unable to get type for variable {name}")
            return Annotation(name, typ)
        return None

    def __parse_subscript(self, tree: Union[ast.AnnAssign, ast.Assign]) -> Optional[Annotation]:
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

        if isinstance(tree, ast.AnnAssign) and isinstance(tree.annotation, ast.Subscript) and isinstance(tree.value, ast.Name):
            name = tree.value.id
            type_string = rec(tree.annotation)
            typ = get_type_from_module(type_string, self.module)
            return Annotation(name, typ)

        return None


def get_ast_parser_type(module: ModuleType, signature_parameters: Dict[str, Type] = {}) -> ASTParseResult:
    if sys.version_info >= (3, 9):
        return ASTParseResult_3_9(module, signature_parameters)
    else:
        return ASTParseResult_3_6(module, signature_parameters)


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

    # Get signature types and fallback if no annotation in body of __init__
    parameters: Dict[str, Type] = {k: v.annotation for k, v in inspect.signature(type.__init__).parameters.items()}
    # TODO: Check if this returns ALL self.x = y in the class. We only want the __init__ ones.
    self_visitor = SelfVisitor()
    self_visitor.generic_visit(tree)
    annotations: List[Annotation] = []

    # Iterate self.X = Y assignments
    for n in self_visitor.nodes:
        parser = get_ast_parser_type(module, parameters)
        annotation = parser.parse(n)
        if annotation is None:
            if isinstance(n, ast.AnnAssign):
                name = n.target.attr if isinstance(n.target, ast.Attribute) else 'unknown'
            elif isinstance(n, ast.Assign) and isinstance(n.value, ast.Name):
                name = n.value.id
            raise Exception(f"Was unable to find name/type for {name}")
        else:
            annotations.append(annotation)

    # Iterate super, if used
    super_visitor = SuperVisitor()
    super_visitor.generic_visit(tree)

    # getmro returns the type itself as first value
    base_classes = inspect.getmro(type)[1:]

    # If super-call in constructor or we dont have constructor, call base-classes
    if (super_visitor.has_super_call or 'def __init__' not in type_source) and len(base_classes) > 0:
        # Recursively get annotations for the next base-class
        annotations.extend(get_annotations(base_classes[0]))

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
