import ast
from pathlib import Path


def asserted_example_function_calls(test_path: Path) -> set[str]:
    tree = ast.parse(test_path.read_text())
    calls: set[str] = set()

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if not isinstance(node.func.value, ast.Name):
            continue
        if node.func.value.id == "examples":
            calls.add(node.func.attr)

    return calls


def public_example_functions(example_path: Path) -> set[str]:
    tree = ast.parse(example_path.read_text())
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        and not node.name.startswith("_")
    }
