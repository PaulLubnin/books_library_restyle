import argparse
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

TULULU_URl = 'https://tululu.org'


def get_books_file(book_id: int) -> bytes:
    """ Функция для получения книги.

    Args:
        book_id: Идентификационный номер книги.

    Returns:
        bytes: Книга в байтах.
    """

    url = f'{TULULU_URl}/txt.php'
    payload = {'id': book_id}
    response = requests.get(url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    return response.content


def get_book_page(book_id: int) -> str:
    """ Функция делает запрос для получения страницы книги

    Args:
        book_id: Идентификационный номер книги.

    Returns:
        str: HTML контент.
    """

    url = f'{TULULU_URl}/b{book_id}'
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)
    return response.text


def get_cover_file(cover_url: str) -> bytes:
    """ Функция делает запрос для получения обложки книги.

    Args:
        cover_url: Ссылка на обложку.

    Returns:
        str: HTML контент.
    """

    response = requests.get(cover_url)
    response.raise_for_status()
    check_for_redirect(response)
    return response.content


def parsing_url(url: str) -> dict:
    """ Функция парсит урл.

    Args:
        url: Ссылка на книгу.

    Returns:
        dict: Словарь с ключами: site_name, extension, image_name, [query_key].
    """

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


def parse_book_page(page: str, book_id: int) -> dict:
    """ Функция парсит страницу книги.

    Args:
        page: Страница книги в текстовом формате.
        book_id: Идентификационный номер книги.

    Returns:
        Словарь с ключами: title, author, genre, cover_url, comments.
    """

    soup = BeautifulSoup(page, 'lxml')
    book_title, book_author = parse_book_title(soup)
    return {'title': f'{book_id}.{book_title}',
            'author': book_author,
            'genre': parse_book_genre(soup),
            'cover_url': parse_cover_url(soup, book_id),
            'comments': parse_book_comments(soup)}


def parse_cover_url(bs4_soup: BeautifulSoup, book_id) -> str:
    """ Функция получения ссылки на обложку книги.

    Args:
        book_id: Идентификатор книги.
        bs4_soup: HTML контент.

    Returns:
        str: Ссылка на обложку книги.
    """

    book_image = bs4_soup.find('div', class_='bookimage')
    cover_url = book_image.find('img')['src']
    cover_url = urljoin(f'{TULULU_URl}/b{book_id}/', cover_url)
    return cover_url


def parse_book_title(bs4_soup: BeautifulSoup) -> list:
    """ Функция получения названия и автора книги.

    Args:
        bs4_soup (int): HTML контент.

    Returns:
        list: [book_title, book_author].
    """

    title_tag = bs4_soup.find('h1')
    return [elem.strip().replace(': ', '. ') for elem in title_tag.text.split(' :: ')]


def parse_book_comments(bs4_soup: BeautifulSoup) -> list:
    """ Функция для получения комментариев к книге.

    Args:
        bs4_soup: HTML контент.

    Returns:
        list: Список с комментариями.
    """

    book_comments = bs4_soup.find_all('div', class_='texts')
    return [elem.find('span').text for elem in book_comments]


def parse_book_genre(bs4_soup: BeautifulSoup) -> list:
    """ Функция для получения жанра книги.

    Args:
        bs4_soup: HTML контент.

    Returns:
        list: Список с жанрами книги.
    """

    book_genre = bs4_soup.find_all('span', class_='d_book')
    for elem in book_genre:
        title, genre = elem.text.split(':')
        return [elem.strip() for elem in genre.split(',')]


def download_image(image_name: str, cover_url: str, file_extension: str, folder: str = 'covers/') -> None:
    """ Функция для скачивания обложки книги.

    Args:
        image_name: Название обложки.
        cover_url: Ссылка на обложку.
        file_extension: Расширение файла обложки.
        folder: Папка, куда сохранять.
    """

    cover = get_cover_file(cover_url)
    folder = sanitize_filename(folder)
    cover_path = f'{create_path(image_name, folder)}.{file_extension}'
    save_data(cover, cover_path)


def download_txt(book_id: int, book_name: str, folder: str = 'books/') -> str:
    """ Функция для скачивания текстовых файлов.

    Args:
        book_id: Идентификатор книги.
        book_name: Название книги.
        folder: Папка, куда сохранять.

    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    book = get_books_file(book_id)
    folder = sanitize_filename(folder)
    if book:
        book_path = f'{create_path(book_name, folder)}.txt'
        save_data(book, book_path)
        return book_path


def save_data(saved_file: bytes, filename: str) -> None:
    """ Функция для сохранения книг, обложек книг.

    Args:
        saved_file: Файл в байтах.
        filename: Название файла.
    """

    with open(filename, 'wb') as file:
        file.write(saved_file)


def create_path(book_name: str, folder_name: str, ) -> Path:
    """ Функция создает папку и возвращает её путь.

    Args:
        book_name: Название книги.
        folder_name: Название папки, куда нужно будет сложить файлы.
    """

    save_folder = Path.cwd() / folder_name
    Path(save_folder).mkdir(parents=True, exist_ok=True)
    return save_folder / book_name


def check_for_redirect(response) -> None:
    """ Функция проверки редиректа. """

    for elem in response.history:
        if elem.status_code == 302:
            raise requests.HTTPError


def starting_parser(first_id: int, last_id: int):
    """ Запуск парсера.

    Args:
        first_id: С какой книги начать скачивание.
        last_id: На какой книге закончить скачивание.
    """

    book_id = first_id
    iteration_number = 1

    while last_id >= book_id:
        successful_iteration = True
        try:
            page_book = get_book_page(book_id)
            book_info = parse_book_page(page_book, book_id)
            book_name = book_info.get('title')
            filepath = download_txt(book_id, book_name)
            if not filepath:
                continue
            cover_url = book_info.get('cover_url')
            image_name = parsing_url(cover_url).get('image_name')
            file_extension = parsing_url(cover_url).get('extension')
            download_image(image_name, cover_url, file_extension)
            print(f'{iteration_number}. {filepath}')

        except requests.HTTPError:
            print(f'По заданному адресу книга {book_id} отсутствует', file=sys.stderr)

        except requests.ConnectionError:
            print('Неполадки с интернетом. Восстановление соединения...', file=sys.stderr)
            successful_iteration = False
            time.sleep(30)

        if successful_iteration:
            book_id += 1
            iteration_number += 1


def main():
    """ Запуска скрипта из командной строки. """

    parser = argparse.ArgumentParser(
        prog='tululu.py',
        description='Downloading books.'
    )
    parser.add_argument(
        'start_id', type=int,
        help='Which book to start downloading.')
    parser.add_argument(
        'end_id', type=int,
        help='Which book to download.')
    args = parser.parse_args()

    if args.start_id > args.end_id:
        print(f'Первый аргумент должен быть меньше второго.\npython tululu.py {args.end_id} {args.start_id}')
        sys.exit()

    starting_parser(args.start_id, args.end_id)


if __name__ == '__main__':
    main()
