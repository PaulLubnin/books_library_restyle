from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

TULULU_URl = 'https://tululu.org'


def url_serializing(url: str) -> dict:
    """Функция парсит урл.

    Args:
        url (str): Ссылка на книгу.

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


def get_books_file(book_id: int) -> bytes:
    """Функция для получения книги.

    Args:
        book_id (int): Идентификационный номер книги.

    Returns:
        bytes: Книга в байтах.
    """

    url = f'{TULULU_URl}/txt.php'
    payload = {'id': book_id}
    response = requests.get(url, params=payload)
    response.raise_for_status()
    try:
        check_for_redirect(response)
        return response.content
    except requests.HTTPError:
        print(f'Book {book_id} is not found')


def parse_cover_url(bs4_soup: BeautifulSoup) -> str:
    """Функция получения ссылки на обложку книги.

    Args:
        bs4_soup (int): HTML контент.

    Returns:
        str: Ссылка на обложку книги.
    """

    book_image = bs4_soup.find('div', class_='bookimage')
    cover_url = book_image.find('img')['src']
    cover_url = urljoin(TULULU_URl, cover_url)
    return cover_url


def parse_book_title(bs4_soup: BeautifulSoup, book_id) -> dict:
    """Функция получения названия и автора книги.

    Args:
        bs4_soup (int): HTML контент.
        book_id (int): Идентификационный номер книги.
    Returns:
        dict: Словарь с ключами: book_title, book_author.
    """

    title_tag = bs4_soup.find('h1')
    book_title, book_author = [elem.strip() for elem in title_tag.text.split(' :: ')]
    book_data = {'book_title': f'{book_id}. {book_title}',
                 'book_author': book_author}
    return book_data


def parse_book_comments(bs4_soup: BeautifulSoup) -> list:
    """Функция для получения комментариев к книге.

    Args:
        bs4_soup (int): HTML контент.

    Returns:
        list: Список с комментариями.
    """

    book_comments = bs4_soup.find_all('div', class_='texts')
    return [elem.find('span').text for elem in book_comments]


def parse_book_genre(bs4_soup: BeautifulSoup) -> list:
    """Функция для получения жанра книги.

    Args:
        bs4_soup (int): HTML контент.

    Returns:
        list: Список с жанрами книги.
    """

    book_genre = bs4_soup.find_all('span', class_='d_book')
    for elem in book_genre:
        title, genre = elem.text.split(':')
        return [elem.strip() for elem in genre.split(',')]


def download_image(url: str, folder: str = 'covers/') -> None:
    """Функция для скачивания обложки книги

    Args:
        url (str): Cсылка на книгу, обложку которой необходимо скачать.
        folder (str): Папка, куда сохранять.
    """

    book_id = url_serializing(url).get('id')
    if parse_book_page(book_id):
        cover_url = parse_book_page(book_id).get('cover_url')
        folder = sanitize_filename(folder)
        response = requests.get(cover_url)
        response.raise_for_status()
        cover = response.content
        image_name = url_serializing(cover_url).get('image_name')
        file_extension = url_serializing(cover_url).get('extension')
        cover_path = f'{create_path(image_name, folder)}.{file_extension}'
        save_data(cover, cover_path)


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
        book_name = parse_book_page(book_id).get('title')
        book_path = f'{create_path(book_name, folder)}.txt'
        save_data(book, book_path)
        return book_path


def parse_book_page(book_id: int) -> dict:
    """Функция парсит страницу книги.

    Args:
        book_id (int): Идентификационный номер книги.

    Returns:
        book_data (dict): Словарь с ключами: title, author, genre, cover_url, comments.
    """

    url = f'{TULULU_URl}/b{book_id}'
    response = requests.get(url)
    response.raise_for_status()
    try:
        check_for_302_redirect(response)
        soup = BeautifulSoup(response.text, 'lxml')
        book_data = {
            'title': parse_book_title(soup, book_id).get('book_title'),
            'author': parse_book_title(soup, book_id).get('book_author'),
            'genre': parse_book_genre(soup),
            'cover_url': parse_cover_url(soup),
            'comments': parse_book_comments(soup),
        }
        return book_data
    except requests.HTTPError:
        print(f'Book {book_id} parsing failed')


def save_data(saved_file: bytes, filename: str) -> None:
    """Функция для сохранения книг, обложек книг.

    Args:
        saved_file (bytes): Файл в байтах.
        filename (str): Название файла.
    """

    with open(filename, 'wb') as file:
        file.write(saved_file)


def create_path(book_name: str, folder_name: str, ) -> Path:
    """Функция создает папку и возвращает её путь.

    Args:
        book_name (str): Название книги.
        folder_name (str): Название папки, куда нужно будет сложить файлы.
    """

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


def main():
    books_urls = [f'http://tululu.org/txt.php?id={number}' for number in range(1, 11)]
    books_ids = range(1, 11)

    check_url(books_urls[0])
    for book_number, url in enumerate(books_urls, 1):
        filepath = download_txt(url)
        download_image(url)
    # print(parse_book_page(8))


if __name__ == '__main__':
    main()
