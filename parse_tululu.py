import argparse
import json
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


def get_content(page_reference: str, book_id: int = None) -> bytes:
    """ Функция делает запрос для получения всей страницы в HTML.

    Args:
        book_id: Идентификационный номер книги.
        page_reference: ссылка на страницу.

    Returns:
        Страница в HTML формате.
    """

    payload = {'id': book_id}
    response = requests.get(page_reference, params=payload)
    response.raise_for_status()
    check_for_redirect(response)
    return response.content


def parse_url(url: str) -> dict:
    """ Функция парсит урл.

    Args:
        url: Ссылка на книгу или обложку.

    Returns:
        dict: Словарь с ключами: book_id, extension, image_name.
    """

    unq_url = unquote(url)
    split_url = urlsplit(unq_url)
    if split_url.path:
        return {'book_id': f'{split_url.path.strip("/")[1:]}',
                'extension': f'.{split_url.path.split(".")[-1]}',
                'image_name': split_url.path.split('.')[0].split('/')[-1]}


def parse_book_page(page: bytes, book_id: int, dest_folder: str = 'media') -> dict:
    """ Функция парсит страницу книги.

    Args:
        dest_folder: папка куда сохраняются файлы.
        page: Страница книги в текстовом формате.
        book_id: Идентификационный номер книги.

    Returns:
        Словарь с ключами: title, author, img_src, book_path, genres, cover_url, comments.
    """

    soup = BeautifulSoup(page, 'lxml')
    book_title, book_author = parse_book_title(soup)
    cover_url = parse_cover_url(soup, book_id)
    cover = parse_url(cover_url)
    return {'title': book_title,
            'author': book_author,
            'img_src': str(Path(dest_folder, 'covers', f'{cover.get("image_name")}{cover.get("extension")}')),
            'book_path': str(Path(dest_folder, 'books', f'{book_title}.txt')),
            'genres': parse_book_genre(soup),
            'cover_url': cover_url,
            'comments': parse_book_comments(soup)}


def parse_cover_url(bs4_soup: BeautifulSoup, book_id) -> str:
    """ Функция получения ссылки на обложку книги.

    Args:
        book_id: Идентификатор книги.
        bs4_soup: HTML контент.

    Returns:
        str: Ссылка на обложку книги.
    """

    cover_url_selector = '.bookimage img[src]'
    cover_link = bs4_soup.select_one(cover_url_selector)['src']
    cover_url = urljoin(f'{TULULU_URL}/b{book_id}/', cover_link)
    return cover_url


def parse_book_title(bs4_soup: BeautifulSoup) -> list:
    """ Функция получения названия и автора книги.

    Args:
        bs4_soup (int): HTML контент.

    Returns:
        list: [book_title, book_author].
    """

    title_tag = bs4_soup.select('h1')
    return [elem.strip().replace(': ', '. ') for elem in title_tag[0].text.split(' :: ')]


def parse_book_comments(bs4_soup: BeautifulSoup) -> list:
    """ Функция для получения комментариев к книге.

    Args:
        bs4_soup: HTML контент.

    Returns:
        list: Список с комментариями.
    """

    book_comments_selector = '.texts .black'
    book_comments = bs4_soup.select(book_comments_selector)
    return [elem.string for elem in book_comments]


def parse_book_genre(bs4_soup: BeautifulSoup) -> list:
    """ Функция для получения жанра книги.

    Args:
        bs4_soup: HTML контент.

    Returns:
        list: Список с жанрами книги.
    """
    book_genre_selector = 'span.d_book a'
    book_genre_sel = bs4_soup.select(book_genre_selector)
    return [elem.string for elem in book_genre_sel]


def download_image(image_name: str, cover_url: str, file_extension: str, folder: str) -> None:
    """ Функция для скачивания обложки книги.

    Args:
        image_name: Название обложки.
        cover_url: Ссылка на обложку.
        file_extension: Расширение файла обложки.
        folder: Папка, куда сохранять.
    """

    cover = get_content(cover_url)
    folder = Path(folder, 'covers')
    cover_path = create_path(image_name, folder) + file_extension
    save_to_file(cover, cover_path)


def download_txt(book_id: int, book_name: str, folder: str) -> str:
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
    folder = Path(folder, 'books')
    book_path = create_path(book_name, folder)
    save_to_file(book, book_path)
    return book_path


def save_to_file(content: bytes, filepath: str) -> None:
    """ Функция для сохранения книг, обложек книг.

    Args:
        content: Контент в байтах.
        filepath: Путь к файлу.
    """

    with open(Path(filepath), 'wb') as file:
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


def save_json_file(books: list, file_name: str, folder: str = 'media'):
    """
    Сохраняет список из книг в JSON файл.

    Args:
        file_name: назавние файла.
        books: список с книгами.
        folder: папка, куда сохранить JSON файл.
    """

    with open(Path(folder, file_name), 'a', encoding='utf-8') as file:
        json.dump(books, file, ensure_ascii=False)


def get_book(book_id: int,
             dest_folder: str = 'media',
             skip_images: bool = False,
             skip_txt: bool = False):
    """
    Запускает парсер и сохраняет информацию о книге в json файл.

    Args:
        book_id: идентификационный номер книги, которую надо скачать
        dest_folder: папка назначения, куда необходимо сохранить файлы
        skip_images: скачивать обложку или нет
        skip_txt: скачивать или нет txt файл
    """

    book_page_url = f'{TULULU_URL}/b{book_id}/'
    page_book = get_content(book_page_url)
    book = parse_book_page(page_book, book_id, dest_folder)
    book_name = book.get('title')
    if not skip_txt:
        download_txt(book_id, f'{book_name}.txt', dest_folder)
    if not skip_images:
        cover_url = book.get('cover_url')
        image = parse_url(cover_url)
        image_name = image.get('image_name')
        file_extension = image.get('extension')
        download_image(image_name, cover_url, file_extension, dest_folder)
    return book


def get_command_line_arguments():
    """
    Получение аргументов командной строки.

    Returns:
        Аргументы командной строки.
    """

    parser = argparse.ArgumentParser(
        prog='parse_tululu.py',
        description='Downloading books.'
    )
    parser.add_argument(
        '-s', '--start_page', type=int, default=1,
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
    if arguments.start_page > arguments.end_page:
        print(f'Первый аргумент должен быть меньше второго.\n'
              f'python parse_tululu.py {arguments.end_page} {arguments.start_page}')
        sys.exit()
    book_id = arguments.start_page
    dest_folder = sanitize_filename(arguments.dest_folder)
    json_path = arguments.json_path.rpartition('/')[0] if arguments.json_path else dest_folder
    json_name = arguments.json_path.rpartition('/')[-1]if arguments.json_path else 'books.json'
    if not arguments.json_path == 'media':
        with open('.env', 'w+') as env_file:
            env_file.write(f'FOLDER_PATH={json_path}\nFILE_NAME={json_name}')
    Path(Path.cwd() / json_path).mkdir(parents=True, exist_ok=True)
    progress_bar = (elem for elem in tqdm(range(arguments.end_page),
                                          initial=1,
                                          bar_format='{l_bar}{n_fmt}/{total_fmt}',
                                          ncols=100))
    books = []
    while arguments.end_page >= book_id:
        successful_iteration = True
        try:
            book = get_book(book_id, dest_folder)
            books.append(book)
        except requests.HTTPError:
            print(f'\nПо заданному адресу книга номер {book_id} отсутствует', file=sys.stderr)
        except requests.ConnectionError:
            print('\nНеполадки с интернетом. Восстановление соединения...', file=sys.stderr)
            successful_iteration = False
            time.sleep(30)
        if successful_iteration:
            book_id += 1
            progress_bar.__next__()
    save_json_file(books, json_name, json_path)


if __name__ == '__main__':
    main()
