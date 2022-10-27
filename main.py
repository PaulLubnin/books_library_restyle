from pathlib import Path

import requests

TULULU_URl = 'https://tululu.org'


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


def check_for_redirect(response):
    """Функция проверки редиректа."""

    if not response.history and response.url != TULULU_URl:
        return
    else:
        raise requests.HTTPError


def get_books_file(book_id: int):
    """Функция делает запрос."""

    url = f'{TULULU_URl}/txt.php'
    payload = {'id': book_id}
    response = requests.get(url, params=payload)
    response.raise_for_status()
    try:
        check_for_redirect(response)
        return response.content
    except requests.HTTPError:
        print(f'Book {book_id} is not found')


def main():
    for book_id in range(1, 11):
        book = get_books_file(book_id)
        if book:
            save_book(book, book_id)


if __name__ == '__main__':
    main()
