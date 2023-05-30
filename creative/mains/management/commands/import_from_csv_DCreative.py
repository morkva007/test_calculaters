import csv
from django.core.management.base import BaseCommand
from mains.models import S_directory_DCreative

FILE_PATH = 'static/data/DCreative.csv'
FILE_NAME = FILE_PATH.split('/')[2]


class Command(BaseCommand):
    help = f'Импорт данных {FILE_PATH}'

    def handle(self, *args, **kwargs):

        print(f'Импорт из {FILE_PATH}:')

        with open(f'{FILE_PATH}', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)

            for row in reader:
                obj, created = S_directory_DCreative.objects.update_or_create(
                        name=row['name'],
                        price=row['price'],
                        link=row['link']
                    )
                if created:
                    print(f'Создана новая запись: {obj}')
                else:
                    print(f'Обновлена запись: {obj}')
        print(f'Импоорт {FILE_NAME} завершен.')