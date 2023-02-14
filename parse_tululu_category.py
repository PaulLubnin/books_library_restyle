import json
import sys
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from tululu import TULULU_URL, parse_url, download_txt, get_content, parse_book_page, download_image


def get_links_from_one_page(page_reference: str) -> list:
    """
    Получение ссылок на книги со страницы со списком книг по жанрам.

    Args:
        page_reference: ссылка на страницу.

    Returns:
        Список ссылок на книги.
    """
    response = requests.get(page_reference)
    response.raise_for_status()
    bs4_soup = BeautifulSoup(response.content, 'lxml')
    books = bs4_soup.find_all('table', class_='d_book')
    book_references = [urljoin(TULULU_URL, url.find('a')['href']) for url in books]
    return book_references


def get_many_of_references(page_count: int) -> list:
    """
    Получение списка ссылок на книги с нескольких страниц.

    Args:
        page_count: количество страниц.

    Returns:
        Список ссылок на книги.
    """
    science_fiction_books = f'{TULULU_URL}/l55/'
    references_to_book_pages = [f'{science_fiction_books}/{page_number}' for page_number in range(1, page_count + 1)]
    books_links = []
    for reference in references_to_book_pages:
        books_links.extend(get_links_from_one_page(reference))
    return books_links


if __name__ == '__main__':
    number_of_pages = 1
    all_books = []
    for book_page_url in get_many_of_references(number_of_pages):
        book_id = parse_url(book_page_url).get('book_id')
        try:
            page_book = get_content(book_page_url)
            book = parse_book_page(page_book, book_id)
            all_books.append(book)
            book_name = book.get('title')
            download_txt(book_id, book_name)
            cover_url = book.get('cover_url')
            image = parse_url(cover_url)
            image_name = image.get('image_name')
            file_extension = image.get('extension')
            download_image(image_name, cover_url, file_extension)

        except requests.HTTPError:
            print(f'\nПо заданному адресу книга номер {book_id} отсутствует', file=sys.stderr)

    books_json = json.dumps(all_books, ensure_ascii=False)
    with open('books.json', 'a', encoding='utf-8') as file:
        file.write(books_json)
