import ast
import json
import pathlib

app_dir = pathlib.Path(__file__).resolve().parents[4] / "services" / "api" / "app"
routes = set()

for filename in ("main.py", "hr.py", "extended.py"):
    tree = ast.parse((app_dir / filename).read_text())
    prefix = ""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "APIRouter":
            continue
        for keyword in node.keywords:
            if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant):
                prefix = keyword.value.value

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            target = decorator.func.value
            if not isinstance(target, ast.Name) or target.id not in ("app", "router"):
                continue
            method = decorator.func.attr.upper()
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                continue
            path = decorator.args[0].value
            routes.add((method, path if target.id == "app" else prefix + path))

print(json.dumps([{"method": method, "path": path} for method, path in sorted(routes)]))
