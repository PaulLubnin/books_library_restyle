import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


def get_books():
    with open(Path('media', 'books.json'), 'r', encoding='utf-8') as file:
        books_json = file.read()
    books = json.loads(books_json)
    return books


if __name__ == '__main__':
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template = env.get_template('template.html')

    rendered_page = template.render(
        books=get_books(),
    )

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)

    server = HTTPServer(('0.0.0.0', 8000), SimpleHTTPRequestHandler)
    server.serve_forever()
