import json
from pathlib import Path

from primitive_db.constants import DATA_DIR


def load_metadata(filepath):
    """Загружает метаданные из JSON-файла."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    """Сохраняет метаданные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_table_data(table_name):
    """Загружает данные указанной таблицы."""
    filepath = Path(DATA_DIR) / f"{table_name}.json"

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    """Сохраняет данные указанной таблицы."""
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

    filepath = Path(DATA_DIR) / f"{table_name}.json"

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def delete_table_data(table_name):
    """Удаляет файл данных таблицы."""
    filepath = Path(DATA_DIR) / f"{table_name}.json"
    filepath.unlink(missing_ok=True)
