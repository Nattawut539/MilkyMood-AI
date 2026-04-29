"""Utility functions for counting Python variables in code text."""

import ast


def _get_variable_names_from_ast(tree: ast.AST) -> set[str]:
    names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            if node.asname:
                names.add(node.asname)
            else:
                names.add(node.name.split(".")[0])
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)

    return names


def count_variables(code: str) -> int:
    """Count unique variable names in the given Python source code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0

    return len(_get_variable_names_from_ast(tree))


def list_variables(code: str) -> list[str]:
    """Return a sorted list of unique variable names from the given Python source code."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    return sorted(_get_variable_names_from_ast(tree))


if __name__ == "__main__":
    sample = """
import os

x = 10
for i in range(x):
    y = i * 2

class MyClass:
    def method(self, value):
        result = value + x
        return result
"""
    print("Variables:", list_variables(sample))
    print("Count:", count_variables(sample))
