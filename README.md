# Парсер книг с сайта tululu.org

Программа для скачивания книг.

### Как установить

Для запуска нужен установленный Python 3.8 и старше. Затем из папки с файлом запустите командную строку и
наберите: 
```
pip install -r requirements.txt
```

### Как пользоваться

Из папки с проектом в командной строке наберите `python tululu.py <--start_page> <--end_page>`

#### Пример использования:

```
python tululu.ru 1 20
```

программа начнет скачивать книги с 1 по 20 страницы

### Аргументы

`--start_page` - первая страница, с которой начнется скачивание

`--end_page` - последняя страница, на которой заканчивается скачивание

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).