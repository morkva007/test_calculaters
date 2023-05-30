import csv
from django.core.management.base import BaseCommand
from mains.models import Service

FILE_PATH = 'static/data/service.csv'
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
                obj, created = Service.objects.update_or_create(
                        id=row['id'],
                        title=row['title'],
                        price_before_10000=row['price_before_10000'],
                        price_before_25000=row['price_before_25000'],
                        price_after_25000=row['price_after_25000'],
                        kpi_sd=row['kpi_sd'],
                        unit=row['unit'],
                        group=row['group'],
                        fte=row['fte'],
                        link=row['link']
                    )
                if created:
                    print(f'Создана новая запись: {obj}')
                else:
                    print(f'Обновлена запись: {obj}')
        print(f'Импоорт {FILE_NAME} завершен.')
