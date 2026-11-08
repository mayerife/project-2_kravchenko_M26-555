import ast
import re


def parse_value(value):
    """Преобразует строковое значение в Python-тип."""
    value = value.strip()

    if value == "true":
        return True

    if value == "false":
        return False

    return ast.literal_eval(value)


def split_conditions(text):
    """Разделяет условия по запятым вне кавычек."""
    parts = []
    current = []
    quote = None
    escaped = False

    for char in text:
        if escaped:
            current.append(char)
            escaped = False
            continue

        if char == "\\" and quote is not None:
            current.append(char)
            escaped = True
            continue

        if char in ('"', "'"):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None

        if char == "," and quote is None:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)

    if quote is not None:
        raise ValueError("Не закрыты кавычки.")

    parts.append("".join(current).strip())

    if any(not part for part in parts):
        raise ValueError("Обнаружено пустое условие.")

    return parts


def parse_conditions(text):
    """Разбирает условия вида column = value в словарь."""
    conditions = {}

    for part in split_conditions(text):
        match = re.fullmatch(
            r"([A-Za-z_]\w*)\s*=\s*(.+)",
            part,
        )

        if not match:
            raise ValueError(f"Некорректное условие: {part}")

        column, value = match.groups()

        if column in conditions:
            raise ValueError(f"Столбец {column} указан несколько раз.")

        conditions[column] = parse_value(value)

    return conditions


def parse_insert_values(text):
    """Разбирает значения команды insert."""
    return [parse_value(value) for value in split_conditions(text)]
