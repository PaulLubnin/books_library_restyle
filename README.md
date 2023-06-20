# Парсер книг с сайта tululu.org

Программа для скачивания книг.

### Как установить

Для запуска нужен установленный Python 3.8 и старше. Затем из папки с файлом запустите командную строку и
наберите: 
```
pip install -r requirements.txt
```

### Как пользоваться
Из папки с проектом наберите:
- для скачивания книг по порядковому номеру
```
python tululu.py [--start_id] [--end_id]
```
- для скачивания книг по жанрам
```
python parse_tululu_category.py --start_page [номер страницы] --end_page [номер страницы]
```
#### Пример использования:

- программа начнет скачивать книги с 1 по 20
```
python tululu.py 1 20
```
- программа начнет скачивать книги из раздела с жанрами с 600 по 601 станицы
```
python parse_tululu_category.py --start_page 600 --end_page 602
```
- программа начнет скачивать книги из раздела с жанрами с 600 до последней
```
python parse_tululu_category.py --start_page 600
```
- запустить сайт
```
python render_website.py
```

### Аргументы

`--start_id` - первая книга, с которой начнется скачивание

`--end_id` - последняя книга, на которой заканчивается скачивание

`--start_page` - номер страницы, с которой начнется скачивание книг

`--end_page` - номер страницы, на которой закончится скачивание

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).