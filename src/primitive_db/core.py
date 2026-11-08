from primitive_db.constants import VALID_TYPES
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)
from primitive_db.utils import load_table_data, save_table_data


def validate_value(value, column_type):
    """Проверяет соответствие значения типу столбца."""

    types = {
        "int": int,
        "str": str,
        "bool": bool,
    }

    if column_type not in types:
        raise ValueError(f"Неизвестный тип данных: {column_type}")

    if type(value) is not types[column_type]:
        raise ValueError(
            f"Ожидается тип {column_type}, "
            f"получено значение {value!r} "
            f"типа {type(value).__name__}."
        )


def validate_conditions(metadata, table_name, conditions):
    """Проверяет таблицу, столбцы и типы значений условий."""

    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")

    columns = metadata[table_name]

    for column_name, value in conditions.items():
        if column_name not in columns:
            raise ValueError(f"Столбец '{column_name}' не существует.")

        validate_value(value, columns[column_name])


@handle_db_errors
def create_table(metadata, table_name, columns):
    """Создаёт таблицу и добавляет её в метаданные."""

    if not table_name:
        raise ValueError("Имя таблицы не может быть пустым.")

    if table_name in metadata:
        raise ValueError(f"Таблица '{table_name}' уже существует.")

    if not columns:
        raise ValueError("Таблица должна содержать хотя бы один столбец.")

    table_columns = {"ID": "int"}

    for column in columns:
        if ":" not in column:
            raise ValueError(
                f"Неверный формат столбца: {column}. Используйте формат имя:тип."
            )

        column_name, column_type = column.split(":", maxsplit=1)

        if not column_name or not column_type:
            raise ValueError(f"Неверный формат столбца: {column}.")

        if column_name in table_columns:
            raise ValueError(f"Столбец '{column_name}' уже существует.")

        if column_type not in VALID_TYPES:
            raise ValueError(f"Неизвестный тип данных: {column_type}.")

        table_columns[column_name] = column_type

    metadata[table_name] = table_columns

    columns_info = ", ".join(
        f"{name}:{column_type}" for name, column_type in table_columns.items()
    )

    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_info}')

    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных."""

    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")

    del metadata[table_name]

    print(f'Таблица "{table_name}" успешно удалена.')

    return metadata


def list_tables(metadata):
    """Выводит список таблиц."""

    if not metadata:
        print("Таблиц пока нет.")
        return

    for table_name in metadata:
        print(f"- {table_name}")


@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """Добавляет запись в таблицу."""

    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")

    columns = metadata[table_name]

    user_columns = {
        name: column_type for name, column_type in columns.items() if name != "ID"
    }

    if len(values) != len(user_columns):
        raise ValueError(
            f"Ожидается {len(user_columns)} значений, получено {len(values)}."
        )

    record = {}

    for (column_name, column_type), value in zip(user_columns.items(), values):
        validate_value(value, column_type)
        record[column_name] = value

    table_data = load_table_data(table_name)

    new_id = (
        max(
            (row["ID"] for row in table_data),
            default=0,
        )
        + 1
    )

    record = {"ID": new_id, **record}

    table_data.append(record)

    save_table_data(table_name, table_data)

    return table_data


# Один экземпляр кэшера используется всеми вызовами select.
select_cache = create_cacher()


@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """Выбирает записи и кэширует результаты запросов."""

    data_key = tuple(tuple(sorted(row.items())) for row in table_data)

    where_key = (
        tuple(sorted(where_clause.items())) if where_clause is not None else None
    )

    cache_key = (data_key, where_key)

    def get_records():
        if where_clause is None:
            return [dict(row) for row in table_data]

        return [
            dict(row)
            for row in table_data
            if all(row.get(column) == value for column, value in where_clause.items())
        ]

    return select_cache(cache_key, get_records)


@handle_db_errors
def update(table_data, set_clause, where_clause):
    """Обновляет записи по условию."""

    if not where_clause:
        raise ValueError("Для обновления необходимо указать условие WHERE.")

    if "ID" in set_clause:
        raise ValueError("Изменять ID запрещено.")

    for row in table_data:
        if all(row.get(column) == value for column, value in where_clause.items()):
            row.update(set_clause)

    return table_data


@handle_db_errors
@confirm_action("удаление записей")
def delete(table_data, where_clause):
    """Удаляет записи по условию."""

    if not where_clause:
        raise ValueError("Для удаления необходимо указать условие WHERE.")

    return [
        row
        for row in table_data
        if not all(row.get(column) == value for column, value in where_clause.items())
    ]
