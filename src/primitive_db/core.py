from primitive_db.constants import VALID_TYPES


def create_table(metadata, table_name, columns):
    """Создаёт таблицу с указанными столбцами."""
    if not table_name:
        print("Некорректное значение: имя таблицы.")
        return metadata

    if table_name in metadata:
        print(f'Таблица "{table_name}" уже существует.')
        return metadata

    if not columns:
        print("Некорректное значение: укажите столбцы.")
        return metadata

    table_columns = {"ID": "int"}

    for column in columns:
        if ":" not in column:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata

        column_name, column_type = column.split(":", maxsplit=1)

        if not column_name or not column_type:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata

        if column_name == "ID" or column_name in table_columns:
            print(f"Некорректное значение: {column_name}.")
            return metadata

        if column_type not in VALID_TYPES:
            print(f"Некорректное значение: {column_type}. Попробуйте снова.")
            return metadata

        table_columns[column_name] = column_type

    metadata[table_name] = table_columns

    columns_info = ", ".join(f"{name}:{type_}" for name, type_ in table_columns.items())
    print(f'Таблица "{table_name}" успешно создана со столбцами: {columns_info}')

    return metadata


def drop_table(metadata, table_name):
    """Удаляет таблицу из метаданных."""
    if table_name not in metadata:
        print(f'Таблица "{table_name}" не существует.')
        return metadata

    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')

    return metadata


def list_tables(metadata):
    """Выводит список существующих таблиц."""
    if not metadata:
        print("Таблиц пока нет.")
        return

    for table_name in metadata:
        print(f"- {table_name}")
