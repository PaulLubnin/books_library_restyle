import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from livereload import Server


def get_books():
    with open(Path('media', 'books.json'), 'r', encoding='utf-8') as file:
        books_json = file.read()
    books = json.loads(books_json)
    return books


def on_reload():
    template = env.get_template('template.html')
    rendered_page = template.render(
        books=get_books(),
    )

    with open('index.html', 'w', encoding="utf8") as file:
        file.write(rendered_page)


if __name__ == '__main__':
    env = Environment(
        loader=FileSystemLoader('.'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    on_reload()
    server = Server()
    server.watch('template.html', on_reload)
    server.serve(root='.')
