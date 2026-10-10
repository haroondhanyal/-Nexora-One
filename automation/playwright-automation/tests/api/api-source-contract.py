import ast
import json
from pathlib import Path


API_DIR = Path(__file__).resolve().parents[4] / "services" / "api" / "app"
ROUTE_FILES = ("main.py", "hr.py", "extended.py")
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def call_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def route_auth_dependencies(function):
    dependencies = []
    for argument in (*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs):
        if argument in function.args.kwonlyargs:
            default = function.args.kw_defaults[function.args.kwonlyargs.index(argument)]
        else:
            positional = (*function.args.posonlyargs, *function.args.args)
            index = positional.index(argument)
            offset = len(positional) - len(function.args.defaults)
            default = function.args.defaults[index - offset] if index >= offset else None
        if isinstance(default, ast.Call) and call_name(default.func) == "Depends" and default.args:
            dependency = call_name(default.args[0])
            if dependency:
                dependencies.append(dependency)
    return sorted(set(dependencies))


def returned_dict(function):
    for node in ast.walk(function):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            try:
                return ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
    return None


def main():
    routes = []
    app_config = {}
    for filename in ROUTE_FILES:
        tree = ast.parse((API_DIR / filename).read_text(encoding="utf-8"), filename=filename)
        router_prefixes = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and call_name(node.value.func) == "APIRouter":
                prefix = next((keyword.value.value for keyword in node.value.keywords if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant)), "")
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        router_prefixes[target.id] = prefix
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call) and call_name(node.value.func) == "FastAPI":
                app_config = {keyword.arg: keyword.value.value for keyword in node.value.keywords if keyword.arg in {"title", "version", "openapi_url"} and isinstance(keyword.value, ast.Constant)}
        for function in ast.walk(tree):
            if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for decorator in function.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                method = decorator.func.attr.lower()
                target = call_name(decorator.func.value)
                if method not in HTTP_METHODS or not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                    continue
                path = decorator.args[0].value
                if not isinstance(path, str):
                    continue
                if target in router_prefixes:
                    path = router_prefixes[target].rstrip("/") + "/" + path.lstrip("/")
                elif target != "app":
                    continue
                routes.append({
                    "method": method.upper(),
                    "path": path,
                    "function": function.name,
                    "authDependencies": route_auth_dependencies(function),
                    "responseExample": returned_dict(function),
                })
    print(json.dumps({"app": app_config, "routes": routes}, sort_keys=True))


if __name__ == "__main__":
    main()
