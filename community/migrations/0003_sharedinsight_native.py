# Generated manually — SharedInsight: agrega source_native, text, image

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0002_sharedinsight_repost_of'),
    ]

    operations = [
        # Agregar campo text (texto libre para posts nativos)
        migrations.AddField(
            model_name='sharedinsight',
            name='text',
            field=models.TextField(blank=True, help_text='Texto de la publicación'),
        ),
        # Agregar campo image (foto para posts nativos)
        migrations.AddField(
            model_name='sharedinsight',
            name='image',
            field=models.ImageField(blank=True, upload_to='community/posts/%Y/%m/'),
        ),
        # Actualizar choices de source_type para incluir 'native'
        migrations.AlterField(
            model_name='sharedinsight',
            name='source_type',
            field=models.CharField(choices=[('test_result', 'Resultado de test'), ('espejo_exchange', 'Sesión del Espejo'), ('native', 'Publicación libre')], max_length=20),
        ),
    ]
