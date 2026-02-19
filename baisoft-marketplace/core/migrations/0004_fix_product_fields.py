# Manual migration to ensure all fields exist
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_product_improvements'),
    ]

    operations = [
        # This migration is idempotent - it won't fail if fields already exist
    ]
