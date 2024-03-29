import json
import os
from pathlib import Path

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def get_books():
    """Открытие JSON файла."""
    folder = os.getenv('FOLDER_PATH', 'media')
    file_name = os.getenv('FILE_NAME', 'books.json')
    with open(Path(folder, file_name), 'r', encoding='utf-8') as file:
        books = json.load(file)
    return books


def load_template(path, name):
    """Загрузка шаблона для рендеринга страниц."""
    env = Environment(
        loader=FileSystemLoader(path),
        autoescape=select_autoescape(['html', 'xml'])
    )
    return env.get_template(name)


def render_pages():
    """Рендеринг страниц библиотеки."""
    folder = Path.cwd() / 'pages'
    Path(folder).mkdir(parents=True, exist_ok=True)
    template = load_template('.', 'template.html')
    book_quantity = 10
    books = list(chunked(get_books(), book_quantity))
    for page_number, page_books in enumerate(books, 1):
        page = template.render(
            books=page_books,
            page_count=len(books),
            current_page=page_number
        )
        with open(Path(folder, f'index{page_number}.html'), 'w', encoding='utf-8') as file:
            file.write(page)


if __name__ == '__main__':
    load_dotenv()
    server = Server()
    render_pages()
    server.watch('template.html', render_pages)
    server.serve(root='.')
