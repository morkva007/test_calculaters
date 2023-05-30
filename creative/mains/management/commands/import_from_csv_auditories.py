import csv
from django.core.management.base import BaseCommand
from mains.models import Auditories

FILE_PATH = 'static/data/auditories.csv'
FILE_NAME = FILE_PATH.split('/')[2]
ALREDY_LOADED_ERROR_MESSAGE = """Если вам нужно перезагрузить дочерние данные из CSV-файла,
сначала удалите файл db.sqlite3, чтобы уничтожить базу данных.
Затем запустите `python manage.py миграция` для новой пустой
базы данных с таблицами"""

class Command(BaseCommand):
    help = f'Импорт данных {FILE_PATH}'

    def handle(self, *args, **kwargs):
        print(f'Импорт из {FILE_PATH}:')

        with open(f'{FILE_PATH}', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)

            for row in reader:
                obj, created = Auditories.objects.update_or_create(
                    speciality=row['speciality'],
                    count_doc=row['count_doc'],
                    coefficient=row['coefficient'],
                    count_doc_GRP=row['count_doc_GRP'],
                )
                if created:
                    print(f'Создана новая запись: {obj}')
                else:
                    print(f'Обновлена запись: {obj}')
        print(f'Импоорт {FILE_NAME} завершен.')