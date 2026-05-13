import ast
from pathlib import Path


def asserted_example_function_calls(test_path: Path) -> set[str]:
    tree = ast.parse(test_path.read_text())
    calls: set[str] = set()
    example_instances: dict[str, str] = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if not isinstance(node.value.func, ast.Attribute):
            continue
        if not isinstance(node.value.func.value, ast.Name):
            continue
        if node.value.func.value.id != "examples":
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                example_instances[target.id] = node.value.func.attr

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if isinstance(node.func.value, ast.Name):
            if node.func.value.id == "examples":
                calls.add(node.func.attr)
            if node.func.value.id in example_instances:
                calls.add(f"{example_instances[node.func.value.id]}.{node.func.attr}")
        if isinstance(node.func.value, ast.Call):
            nested = node.func.value.func
            if (
                isinstance(nested, ast.Attribute)
                and isinstance(nested.value, ast.Name)
                and nested.value.id == "examples"
            ):
                calls.add(f"{nested.attr}.{node.func.attr}")

    return calls


def _is_public_method(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if node.name.startswith("_"):
        return False
    return not any(
        isinstance(decorator, ast.Name) and decorator.id == "property"
        for decorator in node.decorator_list
    )


def public_example_functions(example_path: Path) -> set[str]:
    tree = ast.parse(example_path.read_text())
    public_callables: set[str] = set()

    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and not node.name.startswith("_")
        ):
            public_callables.add(node.name)
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            public_callables.update(
                f"{node.name}.{child.name}"
                for child in node.body
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
                and _is_public_method(child)
            )

    return public_callables
