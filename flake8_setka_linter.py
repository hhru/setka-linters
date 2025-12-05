#!/usr/bin/env python
import ast
from importlib.metadata import version
from typing import Callable, Generator, TypedDict


class FieldInfo(TypedDict):
    name: str
    column_type_node: ast.AST
    base_type: str
    full_type: str


class Rule(TypedDict):
    error_code: str
    condition: Callable[[FieldInfo], bool]
    assertion: Callable[[FieldInfo], bool]
    message: str


class Plugin:
    name = __name__
    version = version(__name__) if __name__ != "__main__" else "0.0.0"

    def __init__(self, tree: ast.AST, filename: str) -> None:
        self.tree = tree
        self.filename = filename

        self.rules: list[Rule] = [
            {
                "error_code": "STK001",
                "condition": lambda f: f.get("base_type") == "DateTime",
                "assertion": lambda f: f.get("name").endswith("_at")
                or f.get("name").endswith("_dt"),
                "message": "Поле '{}' имеет тип DateTime, должно оканчиваться на '_at' или '_dt'",
            },
            {
                "error_code": "STK002",
                "condition": lambda f: f.get("base_type") == "Date",
                "assertion": lambda f: f.get("name").endswith("_date"),
                "message": "Поле '{}' имеет тип Date, должно оканчиваться на '_date'",
            },
            {
                "error_code": "STK003",
                "condition": lambda f: f.get("name") == "type",
                "assertion": lambda f: f.get("full_type") == "sqlalchemy.Enum",
                "message": "Поле '{}' должно быть определено как Enum",
            },
            {
                "error_code": "STK004",
                "condition": lambda f: f.get("name") == "id"
                or f.get("name").endswith("_id")
                or f.get("name").startswith("id_"),
                "assertion": lambda f: f.get("full_type") == "sqlalchemy.UUID",
                "message": "Поле '{}' должно использовать UUID вместо Integer",
            },
            {
                "error_code": "STK005",
                "condition": lambda f: f.get("base_type") == "bool",
                "assertion": lambda f: not (f.get("name").startwith('is_') or f.get("name").startwith('is_')),
                "message": "Поле '{}' должно использовать UUID вместо Integer",
            },


        ]

    def run(self) -> Generator[tuple[int, int, str, type], None, None]:
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Assign):
                continue
            if not isinstance(node.value, ast.Call):
                continue
            if not node.value.args:
                continue
            #if not self.get_base_type_name(node.value.func) == "Column":
            #    continue

            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue

                field_name = target.id
                column_type_node = node.value.args[0]
                base_type = self.get_base_type_name(column_type_node)
                full_type = self.get_full_name(column_type_node)

                field_info: FieldInfo = {
                    "name": field_name,
                    "column_type_node": column_type_node,
                    "base_type": base_type,
                    "full_type": full_type,
                }

                for rule in self.rules:
                    if rule["condition"](field_info) and not rule["assertion"](
                        field_info
                    ):
                        yield (
                            node.lineno,
                            node.col_offset,
                            "{}: ".format(rule["error_code"])
                            + rule["message"].format(field_info["name"]),
                            type(self),
                        )

    def get_full_name(self, node: ast.AST) -> str:
        """
        Рекурсивно собирает полное имя (например, "sa.Column" или "sqlalchemy.DateTime").
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self.get_full_name(node.value)
            return "{}.{}".format(value, node.attr) if value else node.attr
        elif isinstance(node, ast.Call):
            # Если узел – вызов (например, DateTime()), возвращаем имя вызываемой функции.
            return self.get_full_name(node.func)
        raise ValueError(f"Unexpected node type: {type(node)}")

    def get_base_type_name(self, node: ast.AST) -> str:
        """
        Возвращает базовое имя типа без пространств имён.
        Например, для "sqlalchemy.DateTime" вернется "DateTime".
        """
        full_name = self.get_full_name(node)
        return full_name.split(".")[-1]


if __name__ == "__main__":
    import sys

    with open(sys.argv[1]) as f:
        source = f.read()
    tree = ast.parse(source)
    checker = Plugin(tree, sys.argv[1])
    for error in checker.run():
        print("{}:{}: {}".format(error[0], error[1], error[2]))
