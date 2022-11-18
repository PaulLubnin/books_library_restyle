from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.parse import urljoin

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
    if split_url.path:
        serialised_data['extension'] = split_url.path.split('.')[-1]
        serialised_data['image_name'] = split_url.path.split('.')[0].split('/')[-1]
    return serialised_data


def get_books_file(book_id: int) -> bytes:
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


def get_cover_file(url: str) -> bytes:
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def fetch_cover_url(book_id: int) -> str:
    """Функция получения ссылки на обложку книги."""

    url = f'{TULULU_URl}/b{book_id}'
    response = requests.get(url)
    response.raise_for_status()
    try:
        check_for_302_redirect(response)
        soup = BeautifulSoup(response.text, 'lxml')
        book_image = soup.find('div', class_='bookimage')
        cover_url = book_image.find('img')['src']
        cover_url = urljoin(TULULU_URl, cover_url)
        return cover_url
    except requests.HTTPError:
        print(f'Cover for book {book_id} is not found')


def fetch_book_name(book_id: int) -> str:
    """Функция получения данных о книге.

    Args:
        book_id (int): Идентификационный номер книги.

    Returns:
        str: Название книги, автор книги.
    """

    url = f'{TULULU_URl}/b{book_id}'
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    title_tag = soup.find('h1')
    serialized_book = [elem.strip().replace(' ', '_').replace(':', '') for elem in title_tag.text.split(' :: ')]
    return f'{book_id}. {serialized_book[0]}'


def download_image(url: str, folder: str = 'covers/'):
    """Функция для скачивания обложки книги"""

    book_id = url_serializing(url).get('id')
    cover_url = fetch_cover_url(book_id)
    folder = sanitize_filename(folder)
    if cover_url:
        cover = get_cover_file(cover_url)
        image_name = url_serializing(cover_url).get('image_name')
        file_extension = url_serializing(cover_url).get('extension')
        cover_path = f'{create_path(image_name, folder)}.{file_extension}'
        save_book(cover, cover_path)


def download_txt(url: str, folder: str = 'books/') -> str:
    """Функция для скачивания текстовых файлов.

    Args:
        url (str): Cсылка на текст, который хочется скачать.
        folder (str): Папка, куда сохранять.

    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    book_id = url_serializing(url).get('id')
    book = get_books_file(book_id)
    folder = sanitize_filename(folder)
    if book:
        book_name = fetch_book_name(book_id)
        book_path = f'{create_path(book_name, folder)}.txt'
        save_book(book, book_path)
        return book_path


def save_book(text: bytes, filename: str) -> None:
    """Функция сохранения книг."""

    with open(filename, 'wb') as file:
        file.write(text)


def create_path(book_name: str, folder_name: str, ) -> Path:
    """Функция создает папку и возвращает её путь."""

    save_folder = Path.cwd() / folder_name
    Path(save_folder).mkdir(parents=True, exist_ok=True)
    return save_folder / book_name


def check_for_redirect(response) -> None:
    """Функция проверки редиректа."""

    if not response.history:
        return
    else:
        raise requests.HTTPError


def check_for_302_redirect(response) -> None:
    """Функция проверки 302 редиректа."""

    if len(response.history) == 2 and response.history[1].status_code == 302:
        raise requests.HTTPError
    else:
        return


def check_url(url: str):
    """Проверка урла, что сайт верный."""

    if url_serializing(url)['site_name'] == url_serializing(TULULU_URl)['site_name']:
        return
    raise requests.HTTPError


if __name__ == '__main__':
    books_urls = [f'http://tululu.org/txt.php?id={number}' for number in range(1, 11)]
    books_ids = range(1, 11)

    check_url(books_urls[0])
    for book_id, url in enumerate(books_urls, 1):
        filepath = download_txt(url)
        download_image(url)
    # download_txt('http://tululu.org/txt.php?id=7')

    # for book_id in books_ids:
    #     print(fetch_cover_url(book_id))
