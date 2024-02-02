# Generated by Django 5.0 on 2024-02-02 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eLearning', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='status',
            field=models.CharField(choices=[('draft', 'Draft'), ('official', 'Official')], default='draft', max_length=20, verbose_name='Status'),
        ),
    ]
