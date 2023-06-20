import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server
from more_itertools import chunked


def get_books():
    with open(Path('pages/media', 'books.json'), 'r', encoding='utf-8') as file:
        books_json = file.read()
    books = json.loads(books_json)
    return books


def load_template(path, name):
    env = Environment(
        loader=FileSystemLoader(path),
        autoescape=select_autoescape(['html', 'xml'])
    )
    return env.get_template(name)


def render_pages(folder_name):
    template = load_template('.', 'template.html')
    book_quantity = 5
    books = list(chunked(get_books(), book_quantity))
    for page_number, page_books in enumerate(books):
        page = template.render(
            books=page_books,
            page_count=len(books),
            current_page=page_number
        )
        with open(f'{folder_name}/index{"" if not page_number else page_number}.html', 'w', encoding="utf8") as file:
            file.write(page)


if __name__ == '__main__':
    templates_folder = 'pages'
    Path(templates_folder).mkdir(parents=True, exist_ok=True)
    render_pages(templates_folder)
    server = Server()
    server.watch('template.html', render_pages(templates_folder))
    server.serve(root=templates_folder)
