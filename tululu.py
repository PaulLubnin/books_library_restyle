import argparse
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from tqdm import tqdm

TULULU_URL = 'https://tululu.org'


def get_content(file_url: str, book_id: int = None) -> bytes:
    """ Функция делает запрос для получения файла.

    Args:
        book_id: Идентификационный номер книги.
        file_url: Ссылка на файл.

    Returns:
        bytes: HTML контент.
    """

    payload = {'id': book_id}
    response = requests.get(file_url, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    return response.content


def parse_url(url: str) -> dict:
    """ Функция парсит урл.

    Args:
        url: Ссылка на книгу.

    Returns:
        dict: Словарь с ключами: extension, image_name.
    """

    unq_url = unquote(url)
    split_url = urlsplit(unq_url)
    if split_url.path:
        return {'extension': f'.{split_url.path.split(".")[-1]}',
                'image_name': split_url.path.split('.')[0].split('/')[-1]}


def parse_book_page(page: bytes, book_id: int) -> dict:
    """ Функция парсит страницу книги.

    Args:
        page: Страница книги в текстовом формате.
        book_id: Идентификационный номер книги.

    Returns:
        Словарь с ключами: title, author, genre, cover_url, comments.
    """

    soup = BeautifulSoup(page, 'lxml')
    book_title, book_author = parse_book_title(soup)
    return {'title': f'{book_id}.{book_title}.txt',
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
    cover_url = urljoin(f'{TULULU_URL}/b{book_id}/', cover_url)
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

    book_genre = bs4_soup.find('span', class_='d_book')
    genre = book_genre.text.split(':')[1].strip().split(',')
    return [elem.strip() for elem in genre]


def download_image(image_name: str, cover_url: str, file_extension: str, folder: str = 'covers/') -> None:
    """ Функция для скачивания обложки книги.

    Args:
        image_name: Название обложки.
        cover_url: Ссылка на обложку.
        file_extension: Расширение файла обложки.
        folder: Папка, куда сохранять.
    """

    cover = get_content(cover_url)
    folder = sanitize_filename(folder)
    cover_path = create_path(image_name, folder) + file_extension
    save_to_file(cover, cover_path)


def download_txt(book_id: int, book_name: str, folder: str = 'books/') -> str:
    """ Функция для скачивания текстовых файлов.

    Args:
        book_id: Идентификатор книги.
        book_name: Название книги.
        folder: Папка, куда сохранять.

    Returns:
        str: Путь до файла, куда сохранён текст.
    """

    book_url = f'{TULULU_URL}/txt.php'
    book = get_content(book_url, book_id)
    folder = sanitize_filename(folder)
    book_path = create_path(book_name, folder)
    save_to_file(book, book_path)
    return book_path


def save_to_file(content: bytes, filepath: str) -> None:
    """ Функция для сохранения книг, обложек книг.

    Args:
        content: Контент в байтах.
        filepath: Путь к файлу.
    """

    with open(filepath, 'wb') as file:
        file.write(content)


def create_path(book_name: str, folder_name: str, ) -> str:
    """ Функция создает папку и возвращает её путь.

    Args:
        book_name: Название книги.
        folder_name: Название папки, куда нужно будет сложить файлы.
    """

    folder = Path.cwd() / folder_name
    Path(folder).mkdir(parents=True, exist_ok=True)
    return str(folder / book_name)


def check_for_redirect(response) -> None:
    """ Функция проверки редиректа. """

    if response.history:
        raise requests.HTTPError


def run_parser(first_id: int, last_id: int):
    """ Запуск парсера.

    Args:
        first_id: С какой книги начать скачивание.
        last_id: На какой книге закончить скачивание.
    """

    book_id = first_id
    iteration_number = 1
    progress_bar = (elem for elem in tqdm(range(last_id),
                    initial=1, bar_format='{l_bar}{n_fmt}/{total_fmt}', ncols=100))

    while last_id >= book_id:
        successful_iteration = True
        book_page_url = f'{TULULU_URL}/b{book_id}/'
        try:
            page_book = get_content(book_page_url)
            book = parse_book_page(page_book, book_id)
            book_name = book.get('title')
            download_txt(book_id, book_name)
            cover_url = book.get('cover_url')
            image = parse_url(cover_url)
            image_name = image.get('image_name')
            file_extension = image.get('extension')
            download_image(image_name, cover_url, file_extension)

        except requests.HTTPError:
            print(f'\nПо заданному адресу книга номер {book_id} отсутствует', file=sys.stderr)

        except requests.ConnectionError:
            print('\nНеполадки с интернетом. Восстановление соединения...', file=sys.stderr)
            successful_iteration = False
            time.sleep(30)

        if successful_iteration:
            book_id += 1
            iteration_number += 1
            progress_bar.__next__()


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

    run_parser(args.start_id, args.end_id)


if __name__ == '__main__':
    main()
