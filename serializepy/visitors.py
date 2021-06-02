import ast
from typing import List


class SelfVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.nodes: List[ast.AnnAssign] = []

    def visit(self, n: ast.AST) -> None:
        if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Attribute):
            if isinstance(n.target.value, ast.Name) and n.target.value.id == 'self':
                self.nodes.append(n)
        super().visit(n)


class SuperVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.has_super_call: bool = False

    def visit(self, n: ast.AST) -> None:
        if isinstance(n, ast.FunctionDef) and n.name == '__init__':
            for stmt in n.body:
                if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                    if isinstance(stmt.value.func, ast.Attribute) and isinstance(stmt.value.func.value, ast.Call):
                        if isinstance(stmt.value.func.value.func, ast.Name) and stmt.value.func.value.func.id == 'super':
                            self.has_super_call = True
                            # TODO: This is extremely ugly LOL
        super().visit(n)
