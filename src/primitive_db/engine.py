import re
import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import META_FILE
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    update,
    validate_conditions,
    validate_value,
)
from primitive_db.parser import parse_conditions, parse_insert_values
from primitive_db.utils import (
    delete_table_data,
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)


def print_help():
    """Выводит справку по командам."""

    print("""
Доступные команды:

Управление таблицами:
  create_table <имя> <столбец:тип> ...
  list_tables
  drop_table <имя>
  info <имя>

Работа с записями:
  insert into <таблица> values (<значения>)
  select from <таблица>
  select from <таблица> where <условие>
  update <таблица> set <условия> where <условие>
  delete from <таблица> where <условие>

Дополнительные команды:
  help
  exit
""")


def print_records(records):
    """Выводит записи с помощью PrettyTable."""

    if not records:
        print("Записей не найдено.")
        return

    table = PrettyTable()
    table.field_names = list(records[0].keys())

    for record in records:
        table.add_row(list(record.values()))

    print(table)


def validate_set_clause(metadata, table_name, set_clause):
    """Проверяет поля и типы значений для UPDATE."""

    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")

    columns = metadata[table_name]

    for column, value in set_clause.items():
        if column == "ID":
            raise ValueError("Изменять ID запрещено.")

        if column not in columns:
            raise ValueError(f"Столбец '{column}' не существует.")

        validate_value(value, columns[column])


def run():
    """Главный цикл программы."""

    print_help()

    while True:
        try:
            user_input = prompt.string("\n>>> Введите команду: ").strip()

            if not user_input:
                continue

            if user_input == "exit":
                print("Выход из программы.")
                break

            if user_input == "help":
                print_help()
                continue

            metadata = load_metadata(META_FILE)

            # CREATE TABLE
            if user_input.startswith("create_table "):
                args = shlex.split(user_input)

                if len(args) < 3:
                    raise ValueError("Укажите имя таблицы и хотя бы один столбец.")

                new_metadata = create_table(
                    metadata,
                    args[1],
                    args[2:],
                )

                if new_metadata is None:
                    continue

                save_metadata(META_FILE, new_metadata)
                continue

            # LIST TABLES
            if user_input == "list_tables":
                list_tables(metadata)
                continue

            # DROP TABLE
            if user_input.startswith("drop_table "):
                args = shlex.split(user_input)

                if len(args) != 2:
                    raise ValueError("Формат команды: drop_table <имя>.")

                table_name = args[1]

                new_metadata = drop_table(
                    metadata,
                    table_name,
                )

                if new_metadata is None:
                    continue

                save_metadata(META_FILE, new_metadata)
                delete_table_data(table_name)
                continue

            # INSERT
            match = re.fullmatch(
                r"insert\s+into\s+(\w+)\s+values\s*\((.*)\)",
                user_input,
            )

            if match:
                table_name, values_text = match.groups()
                values = parse_insert_values(values_text)

                table_data = insert(
                    metadata,
                    table_name,
                    values,
                )

                if table_data is None:
                    continue

                new_id = table_data[-1]["ID"]
                print(f"Запись успешно добавлена. ID: {new_id}")
                continue

            # SELECT
            match = re.fullmatch(
                r"select\s+from\s+(\w+)(?:\s+where\s+(.+))?",
                user_input,
            )

            if match:
                table_name, where_text = match.groups()

                if table_name not in metadata:
                    raise ValueError(f"Таблица '{table_name}' не существует.")

                table_data = load_table_data(table_name)

                where_clause = parse_conditions(where_text) if where_text else None

                if where_clause is not None:
                    validate_conditions(
                        metadata,
                        table_name,
                        where_clause,
                    )

                records = select(table_data, where_clause)

                if records is None:
                    continue

                print_records(records)
                continue

            # UPDATE
            match = re.fullmatch(
                r"update\s+(\w+)\s+set\s+(.+?)\s+where\s+(.+)",
                user_input,
            )

            if match:
                table_name, set_text, where_text = match.groups()

                if table_name not in metadata:
                    raise ValueError(f"Таблица '{table_name}' не существует.")

                set_clause = parse_conditions(set_text)
                where_clause = parse_conditions(where_text)

                validate_conditions(
                    metadata,
                    table_name,
                    where_clause,
                )

                validate_set_clause(
                    metadata,
                    table_name,
                    set_clause,
                )

                table_data = load_table_data(table_name)

                updated_ids = [
                    row["ID"]
                    for row in table_data
                    if all(
                        row.get(column) == value
                        for column, value in where_clause.items()
                    )
                ]

                new_table_data = update(
                    table_data,
                    set_clause,
                    where_clause,
                )

                if new_table_data is None:
                    continue

                if updated_ids:
                    save_table_data(
                        table_name,
                        new_table_data,
                    )

                    for record_id in updated_ids:
                        print(f"Запись с ID {record_id} обновлена.")
                else:
                    print("Подходящих записей не найдено.")

                continue

            # DELETE
            match = re.fullmatch(
                r"delete\s+from\s+(\w+)\s+where\s+(.+)",
                user_input,
            )

            if match:
                table_name, where_text = match.groups()

                if table_name not in metadata:
                    raise ValueError(f"Таблица '{table_name}' не существует.")

                where_clause = parse_conditions(where_text)

                validate_conditions(
                    metadata,
                    table_name,
                    where_clause,
                )

                table_data = load_table_data(table_name)

                deleted_ids = [
                    row["ID"]
                    for row in table_data
                    if all(
                        row.get(column) == value
                        for column, value in where_clause.items()
                    )
                ]

                new_table_data = delete(
                    table_data,
                    where_clause,
                )

                if new_table_data is None:
                    continue

                if deleted_ids:
                    save_table_data(
                        table_name,
                        new_table_data,
                    )

                    for record_id in deleted_ids:
                        print(f"Запись с ID {record_id} удалена.")
                else:
                    print("Подходящих записей не найдено.")

                continue

            # INFO
            match = re.fullmatch(
                r"info\s+(\w+)",
                user_input,
            )

            if match:
                table_name = match.group(1)

                if table_name not in metadata:
                    raise ValueError(f"Таблица '{table_name}' не существует.")

                columns = metadata[table_name]
                table_data = load_table_data(table_name)

                columns_info = ", ".join(
                    f"{name}:{column_type}" for name, column_type in columns.items()
                )

                print(f"Таблица: {table_name}")
                print(f"Столбцы: {columns_info}")
                print(f"Количество записей: {len(table_data)}")

                continue

            print("Неизвестная команда. Введите help.")

        except (ValueError, SyntaxError, TypeError, KeyError, OSError) as error:
            print(f"Ошибка: {error}")
