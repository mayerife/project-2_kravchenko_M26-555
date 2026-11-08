import shlex

import prompt

from primitive_db.constants import META_FILE
from primitive_db.core import create_table, drop_table, list_tables
from primitive_db.utils import load_metadata, save_metadata


def print_help():
    """Выводит список доступных команд."""
    print("\n***Процесс работы с таблицей***")
    print("create_table <имя_таблицы> <столбец1:тип> ... - создать таблицу")
    print("list_tables - показать список таблиц")
    print("drop_table <имя_таблицы> - удалить таблицу")
    print("help - справочная информация")
    print("exit - выход из программы\n")


def run():
    """Запускает основной цикл взаимодействия с базой данных."""
    print_help()

    while True:
        user_input = prompt.string("Введите команду: ")

        try:
            args = shlex.split(user_input)
        except ValueError:
            print("Некорректный ввод. Попробуйте снова.")
            continue

        if not args:
            continue

        command = args[0]
        metadata = load_metadata(META_FILE)
        old_metadata = metadata.copy()

        if command == "create_table":
            if len(args) < 3:
                print("Укажите имя таблицы и хотя бы один столбец.")
                continue

            metadata = create_table(metadata, args[1], args[2:])

        elif command == "drop_table":
            if len(args) != 2:
                print("Укажите имя таблицы.")
                continue

            metadata = drop_table(metadata, args[1])

        elif command == "list_tables":
            if len(args) != 1:
                print("Лишние аргументы.")
                continue

            list_tables(metadata)

        elif command == "help":
            print_help()

        elif command == "exit":
            print("Выход из программы.")
            break

        else:
            print(f"Функции {command} нет. Попробуйте снова.")

        if metadata != old_metadata:
            save_metadata(META_FILE, metadata)
