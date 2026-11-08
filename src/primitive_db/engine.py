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
    """Выводит справочную информацию."""
    print(
        """
***Операции с данными***

Функции:
insert into <таблица> values (<значения>) - создать запись.
select from <таблица> - прочитать все записи.
select from <таблица> where <столбец> = <значение> - поиск записей.
update <таблица> set <столбец> = <значение> where <столбец> = <значение> 
- обновить записи.
delete from <таблица> where <столбец> = <значение> - удалить записи.
info <таблица> - информация о таблице.
create_table <таблица> <столбец:тип> ... - создать таблицу.
list_tables - показать список таблиц.
drop_table <таблица> - удалить таблицу.
help - справочная информация.
exit - выход из программы.
"""
    )


def print_records(records):
    """Выводит записи в виде таблицы PrettyTable."""
    if not records:
        print("Записей не найдено.")
        return

    table = PrettyTable()
    table.field_names = list(records[0].keys())

    for record in records:
        table.add_row(list(record.values()))

    print(table)


def validate_set_clause(metadata, table_name, set_clause):
    """Проверяет столбцы и типы обновляемых значений."""
    if table_name not in metadata:
        raise ValueError(f'Таблица "{table_name}" не существует.')

    columns = metadata[table_name]

    for column, value in set_clause.items():
        if column == "ID":
            raise ValueError("Изменять ID запрещено.")

        if column not in columns:
            raise ValueError(f'Столбца "{column}" не существует.')

        validate_value(value, columns[column])


def run():
    """Запускает интерфейс базы данных."""
    print_help()

    while True:
        try:
            user_input = prompt.string(
                "\n>>> Введите команду: "
            ).strip()

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
                    raise ValueError(
                        "Укажите имя таблицы и хотя бы один столбец."
                    )

                metadata = create_table(
                    metadata,
                    args[1],
                    args[2:],
                )

                save_metadata(META_FILE, metadata)
                continue

            # LIST TABLES
            if user_input == "list_tables":
                list_tables(metadata)
                continue

            # DROP TABLE
            if user_input.startswith("drop_table "):
                args = shlex.split(user_input)

                if len(args) != 2:
                    raise ValueError(
                        "Использование: drop_table <имя_таблицы>"
                    )

                metadata = drop_table(metadata, args[1])

                save_metadata(META_FILE, metadata)
                delete_table_data(args[1])

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

                new_id = table_data[-1]["ID"]

                print(
                    f'Запись с ID={new_id} успешно добавлена '
                    f'в таблицу "{table_name}".'
                )

                continue

            # SELECT
            match = re.fullmatch(
                r"select\s+from\s+(\w+)(?:\s+where\s+(.+))?",
                user_input,
            )

            if match:
                table_name, where_text = match.groups()

                if table_name not in metadata:
                    raise ValueError(
                        f'Таблица "{table_name}" не существует.'
                    )

                table_data = load_table_data(table_name)

                where_clause = (
                    parse_conditions(where_text)
                    if where_text
                    else None
                )

                if where_clause is not None:
                    validate_conditions(
                        metadata,
                        table_name,
                        where_clause,
                    )

                records = select(table_data, where_clause)

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
                    raise ValueError(
                        f'Таблица "{table_name}" не существует.'
                    )

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

                table_data = update(
                    table_data,
                    set_clause,
                    where_clause,
                )

                if updated_ids:
                    save_table_data(table_name, table_data)

                    for record_id in updated_ids:
                        print(
                            f"Запись с ID={record_id} "
                            f'в таблице "{table_name}" успешно обновлена.'
                        )
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
                    raise ValueError(
                        f'Таблица "{table_name}" не существует.'
                    )

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

                table_data = delete(
                    table_data,
                    where_clause,
                )

                if deleted_ids:
                    save_table_data(table_name, table_data)

                    for record_id in deleted_ids:
                        print(
                            f"Запись с ID={record_id} успешно удалена."
                        )
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
                    raise ValueError(
                        f'Таблица "{table_name}" не существует.'
                    )

                columns = metadata[table_name]
                table_data = load_table_data(table_name)

                columns_info = ", ".join(
                    f"{name}:{column_type}"
                    for name, column_type in columns.items()
                )

                print(f"Таблица: {table_name}")
                print(f"Столбцы: {columns_info}")
                print(f"Количество записей: {len(table_data)}")

                continue

            print("Неизвестная команда. Введите help.")

        except (ValueError, SyntaxError, TypeError, KeyError) as error:
            print(f"Ошибка: {error}")