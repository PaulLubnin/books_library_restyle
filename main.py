from pathlib import Path

import requests


def create_path(folder_name: str, book_name: str) -> Path:
    """Функция создает папку и возвращает её путь."""

    save_folder = Path.cwd() / folder_name
    Path(save_folder).mkdir(parents=True, exist_ok=True)
    return save_folder / book_name


def save_book(json, book_id: int):
    """Функция сохранения книг."""

    filename = f'id{book_id}.txt'
    book_path = create_path('books', filename)
    with open(book_path, 'wb') as file:
        file.write(json)


def get_books_file(book_id: int):
    """Функция делает запрос."""

    url = f'https://tululu.org/txt.php?id={book_id}'
    response = requests.get(url)
    response.raise_for_status()

    return response.content


def main():
    for book_id in range(1, 10):
        book = get_books_file(book_id)
        save_book(book, book_id)


if __name__ == '__main__':
    main()
