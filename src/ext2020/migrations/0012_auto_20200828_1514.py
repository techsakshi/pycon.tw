# Generated by Django 3.0.3 on 2020-08-28 07:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ext2020', '0011_auto_20200828_1451'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='venue',
            options={'ordering': ['topic'], 'verbose_name': 'community track venue', 'verbose_name_plural': 'community track venues'},
        ),
    ]
