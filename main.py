from pathlib import Path
from urllib.parse import unquote, urlsplit

import requests
from bs4 import BeautifulSoup

TULULU_URl = 'https://tululu.org'


def check_url(url: str):
    """Проверка урла."""

    unq_url = unquote(url)
    if urlsplit(unq_url).netloc == urlsplit(TULULU_URl).netloc:
        return
    raise requests.HTTPError


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


def fetch_book_data(book_id: int):
    """Функция получения данных о книге (название, автор)"""

    url = f'{TULULU_URl}/b{book_id}'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1')
    serialized_book = [elem.strip() for elem in title_tag.text.split(' :: ')]
    header, author = serialized_book
    return header, author


def main(url: str):
    try:
        check_url(url)

        for book_id in range(1, 11):
            book = get_books_file(book_id)
            if book:
                save_book(book, book_id)
    except requests.HTTPError:
        print('Wrong url')


if __name__ == '__main__':
    url_file = 'http://tululu.org/txt.php?id=1'
    main(url_file)

    # print(type(serialized_url(url)), serialized_url(url))
    # print(type(serialized_url(url)), serialized_url(url)[1])
