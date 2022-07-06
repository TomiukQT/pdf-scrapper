# Generated by Django 4.0.5 on 2022-07-06 20:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scrapping', '0005_extendedresolution_result_by_person'),
    ]

    operations = [
        migrations.AddField(
            model_name='extendedresolution',
            name='attendance',
            field=models.CharField(default='', max_length=1000),
        ),
        migrations.AddField(
            model_name='extendedresolution',
            name='vote_missing',
            field=models.IntegerField(default=0),
        ),
    ]