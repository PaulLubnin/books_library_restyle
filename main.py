from pathlib import Path
from urllib.parse import unquote, urlsplit

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

TULULU_URl = 'https://tululu.org'


def url_serializing(url: str) -> dict:
    """Функция парсит урл."""

    unq_url = unquote(url)
    split_url = urlsplit(unq_url)
    serialised_data = {'site_name': split_url.netloc}
    if split_url.query:
        query_key, book_id = split_url.query.split('=')
        serialised_data[query_key] = book_id
    return serialised_data


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


def download_txt(url: str, filename: str, folder: str = 'books/') -> str:
    """Функция для скачивания текстовых файлов.

    Args:
        url (str): Cсылка на текст, который хочется скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.

    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    check_url(url)
    book_name = sanitize_filename(filename)
    folder = sanitize_filename(folder)
    book_path = f'{create_path(book_name, folder)}.txt'
    book_id = url_serializing(url).get('id')
    book = get_books_file(book_id)
    save_book(book, book_path)
    return book_path


def save_book(text: bytes, filename: str):
    """Функция сохранения книг."""

    with open(filename, 'wb') as file:
        file.write(text)


def create_path(book_name: str, folder_name: str, ) -> Path:
    """Функция создает папку и возвращает её путь."""

    save_folder = Path.cwd() / folder_name
    Path(save_folder).mkdir(parents=True, exist_ok=True)
    return save_folder / book_name


def check_for_redirect(response):
    """Функция проверки редиректа."""

    if not response.history:
        return
    else:
        raise requests.HTTPError


def check_url(url: str):
    """Проверка урла, что сайт верный."""

    if url_serializing(url)['site_name'] == url_serializing(TULULU_URl)['site_name']:
        return
    raise requests.HTTPError


if __name__ == '__main__':
    url = 'http://tululu.org/txt.php?id=1'
    # url_file = 'http://tululu.org/b1'

    filepath = download_txt(url, 'Алиби')
    print(filepath)  # Выведется books/Алиби.txt

    filepath = download_txt(url, 'Али/би', folder='books/')
    print(filepath)  # Выведется books/Алиби.txt

    filepath = download_txt(url, 'Али\\би', folder='txt/')
    print(filepath)  # Выведется txt/Алиби.txt
