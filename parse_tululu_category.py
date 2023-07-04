import argparse
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from tqdm import tqdm

from parse_tululu import TULULU_URL, parse_url, get_book, get_content, save_json_file, get_command_line_arguments


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
        end_page: последняя страница

    Returns:
        Список ссылок на книги
    """

    science_fiction_reference = f'{TULULU_URL}/l55/'
    books_links = []
    while start_page < end_page:
        successful_iteration = True
        reference = urljoin(science_fiction_reference, str(start_page))
        try:
            page = get_content(reference)
            books_links.extend(parse_links_from_page(page, reference))
        except requests.HTTPError:
            print('По заданному адресу страница отсутствует.', file=sys.stderr)
        except requests.ConnectionError:
            print('При получении ссылок на книги пропала связь с Интернетом.', file=sys.stderr)
            successful_iteration = False
            time.sleep(20)
        if successful_iteration:
            start_page += 1
    return books_links


def main():
    """ Запуска скрипта. """

    arguments = get_command_line_arguments()
    if arguments.start_page > arguments.end_page:
        print(f'Первый аргумент должен быть меньше второго.\n'
              f'python parse_tululu_category.py {arguments.end_page} {arguments.start_page}')
        sys.exit()
    dest_folder = sanitize_filename(arguments.dest_folder)
    skip_images = arguments.skip_imgs
    skip_txt = arguments.skip_txt
    json_path = arguments.json_path if arguments.json_path else dest_folder
    Path(Path.cwd() / json_path).mkdir(parents=True, exist_ok=True)
    if not arguments.json_path == 'media':
        with open('.env', 'w+') as env_file:
            env_file.write(f'FILE_FOLDER={json_path}')
    all_books_url = get_links(arguments.start_page, arguments.end_page)
    references_count = len(all_books_url)
    progress_bar = (elem for elem in tqdm(range(references_count),
                                          initial=1,
                                          bar_format='{l_bar}{n_fmt}/{total_fmt}',
                                          ncols=100))
    reference_index = 0
    books = []
    while reference_index < references_count:
        successful_iteration = True
        book_id = int(parse_url(all_books_url[reference_index]).get('book_id'))
        try:
            book = get_book(book_id, dest_folder, skip_images, skip_txt)
            books.append(book)
        except requests.HTTPError:
            print(f'\nПо заданному адресу книга номер {book_id} отсутствует', file=sys.stderr)
        except requests.ConnectionError:
            print('\nНеполадки с интернетом. Восстановление соединения...', file=sys.stderr)
            successful_iteration = False
            time.sleep(30)
        if successful_iteration:
            reference_index += 1
            progress_bar.__next__()
    save_json_file(books, json_path)


if __name__ == '__main__':
    main()
