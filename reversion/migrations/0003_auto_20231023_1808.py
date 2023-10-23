from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reversion', '0002_add_index_on_version_for_content_type_and_db copy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='revision',
            name='user',
            on_delete=models.DO_NOTHING,
            field=models.ForeignKey(blank=True, help_text='The user who created this revision.', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL, verbose_name='user')
        ),
    ]
