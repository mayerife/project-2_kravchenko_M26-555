from functools import wraps
from time import monotonic


def handle_db_errors(func):
    """Централизованно обрабатывает ошибки базы данных."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print(
                "Ошибка: Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            )
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")

        return None

    return wrapper


def confirm_action(action_name):
    """Фабрика декораторов для подтверждения опасных операций."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            answer = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')

            if answer.strip().lower() != "y":
                print("Операция отменена.")
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func):
    """Измеряет время выполнения функции."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = monotonic()

        try:
            return func(*args, **kwargs)
        finally:
            elapsed_time = monotonic() - start_time
            print(f"Функция {func.__name__} выполнилась за {elapsed_time:.3f} секунд")

    return wrapper


def create_cacher():
    """Создаёт кэшер, хранящий результаты в замыкании."""

    cache = {}

    def cache_result(key, value_func):
        if key in cache:
            return cache[key]

        result = value_func()
        cache[key] = result

        return result

    return cache_result
