import argparse
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from tqdm import tqdm

from tululu import TULULU_URL, parse_url, run_parser, check_for_redirect


def get_page(page_reference: str) -> bytes:
    """
    Запрос на получение страницы.

    Args:
        page_reference: ссылка на источник.

    Returns:
        Страница в байтах.
    """

    response = requests.get(page_reference)
    response.raise_for_status()
    check_for_redirect(response)
    return response.content


def parse_links_from_page(page: bytes, page_reference: str) -> list:
    """
    Получение ссылок на книги с страницы со списком книг по жанрам.

    Args:
        page: страница в байтах.
        page_reference: ссылка на страницу.

    Returns:
        Список ссылок на книги.
    """

    bs4_soup = BeautifulSoup(page, 'lxml')
    books_selector = '.d_book .bookimage a[href]'
    books_links = bs4_soup.select(books_selector)
    book_references = [urljoin(page_reference, url['href']) for url in books_links]
    return book_references


def get_links(start_page: int, end_page: int) -> list:
    """
    Получение списка ссылок на книги с нескольких страниц жанра.

    Args:
        start_page: начальная страница
        end_page: послденяя страница

    Returns:
        Список ссылок на книги
    """

    science_fiction_reference = f'{TULULU_URL}/l55/'
    books_links = []
    for page_number in range(start_page, end_page):
        reference = urljoin(science_fiction_reference, str(page_number))
        page = get_page(reference)
        books_links.extend(parse_links_from_page(page, reference))
    return books_links


def get_command_line_arguments():
    """
    Получение аргументов командной строки.

    Returns:
        Аргументы командной строки
    """

    parser = argparse.ArgumentParser(
        prog='parse_tululu_category.py',
        description='Downloading books by genre.'
    )
    parser.add_argument(
        '-s', '--start_page', type=int,
        help='Which page to start downloading.'
    )
    parser.add_argument(
        '-e', '--end_page', type=int, default=702,
        help='Last page to download.'
    )
    parser.add_argument(
        '-df', '--dest_folder', type=str, default='media',
        help='Path to directory with parsing results: pictures, books, JSON.'
    )
    parser.add_argument(
        '-si', '--skip_imgs', action='store_true',
        help="Don't download pictures."
    )
    parser.add_argument(
        '-st', '--skip_txt', action='store_true',
        help="Don't download books."
    )
    parser.add_argument(
        '-j', '--json_path', type=str,
        help='Specify your path to the *.json file with the results.'
    )
    args = parser.parse_args()

    return args


def main():
    """ Запуска скрипта. """

    arguments = get_command_line_arguments()
    if not arguments.start_page:
        print('Необходимо указать страницу, с которой желаете начать скачивание.')
        sys.exit()
    if arguments.start_page > arguments.end_page:
        print(f'Первый аргумент должен быть меньше второго.\n'
              f'python parse_tululu_category.py {arguments.end_page} {arguments.start_page}')
        sys.exit()
    dest_folder = sanitize_filename(arguments.dest_folder)
    skip_images = arguments.skip_imgs
    skip_txt = arguments.skip_txt
    json_path = arguments.json_path if arguments.json_path else dest_folder
    Path(Path.cwd() / json_path).mkdir(parents=True, exist_ok=True)
    all_books_url = get_links(arguments.start_page, arguments.end_page)
    progress_bar = (elem for elem in tqdm(range(len(all_books_url)),
                                          initial=1,
                                          bar_format='{l_bar}{n_fmt}/{total_fmt}',
                                          ncols=100))

    for book_url in all_books_url:
        book_id = int(parse_url(book_url).get('book_id'))
        try:
            run_parser(book_id, dest_folder, skip_images, skip_txt, json_path)
        except requests.HTTPError:
            print(f'\nПо заданному адресу книга номер {book_id} отсутствует', file=sys.stderr)
        except requests.ConnectionError:
            print('\nНеполадки с интернетом. Восстановление соединения...', file=sys.stderr)
            time.sleep(30)
        progress_bar.__next__()


if __name__ == '__main__':
    main()
