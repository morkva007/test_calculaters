# Generated by Django 4.2.1 on 2023-05-19 08:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mains', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='s_directory_dcreative',
            name='in_calculater',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='calculater',
            name='creative',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='mains.s_directory_dcreative', verbose_name='Формат размещения'),
        ),
    ]