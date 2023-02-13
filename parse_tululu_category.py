from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from tululu import TULULU_URL


def get_links_from_one_page(page_reference: str):
    response = requests.get(page_reference)
    response.raise_for_status()
    bs4_soup = BeautifulSoup(response.content, 'lxml')
    books = bs4_soup.find_all('table', class_='d_book')
    book_references = [urljoin(TULULU_URL, url.find('a')['href']) for url in books]
    return book_references


def get_many_of_references(page_number: int):
    science_fiction_books = f'{TULULU_URL}/l55/'
    references_to_book_pages = [f'{science_fiction_books}/{page_number}' for page_number in range(1, page_number)]
    books_links = []
    for reference in references_to_book_pages:
        books_links.extend(get_links_from_one_page(reference))
    return books_links


if __name__ == '__main__':
    number_of_pages = 10
    print(get_many_of_references(number_of_pages))
