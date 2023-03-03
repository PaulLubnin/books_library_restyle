import argparse
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from tqdm import tqdm

from tululu import TULULU_URL, parse_url, run_parser


def parse_links_from_page(page_reference: str) -> list:
    """
    Получение ссылок на книги с страницы со списком книг по жанрам.

    Args:
        page_reference: ссылка на страницу.

    Returns:
        Список ссылок на книги.
    """

    response = requests.get(page_reference)
    response.raise_for_status()
    bs4_soup = BeautifulSoup(response.content, 'lxml')
    books_selector = '.d_book .bookimage a[href]'
    books_links = bs4_soup.select(books_selector)
    book_references = [urljoin(TULULU_URL, url['href']) for url in books_links]
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

    science_fiction_books = f'{TULULU_URL}/l55/'
    references_to_book_pages = [urljoin(science_fiction_books, str(page_number))
                                for page_number in range(start_page, end_page)]
    books_links = []
    for reference in references_to_book_pages:
        books_links.extend(parse_links_from_page(reference))
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

    if not args.start_page:
        print('Необходимо указать страницу, с которой желаете начать скачивание.')
        sys.exit()
    if args.start_page > args.end_page:
        print(f'Первый аргумент должен быть меньше второго.\npython parse_tululu_category.py {args.end_page} {args.start_page}')
        sys.exit()

    return args


def main():
    """ Запуска скрипта. """

    arguments = get_command_line_arguments()
    dest_folder = sanitize_filename(arguments.dest_folder)
    skip_images = arguments.skip_imgs
    all_books_url = get_links(arguments.start_page, arguments.end_page)
    progress_bar = (elem for elem in tqdm(range(len(all_books_url)),
                    initial=1, bar_format='{l_bar}{n_fmt}/{total_fmt}', ncols=100))

    for book_url in all_books_url:
        book_id = int(parse_url(book_url).get('book_id'))
        try:
            run_parser(book_id, dest_folder, skip_images)
        except requests.HTTPError:
            print(f'\nПо заданному адресу книга номер {book_id} отсутствует', file=sys.stderr)
        except requests.ConnectionError:
            print('\nНеполадки с интернетом. Восстановление соединения...', file=sys.stderr)
            time.sleep(30)
        progress_bar.__next__()


if __name__ == '__main__':
    main()
