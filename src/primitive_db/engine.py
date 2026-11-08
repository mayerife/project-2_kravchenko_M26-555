import prompt


def welcome():
    name = prompt.string("May I have your name? ")
    print(f"Hello, {name}!")