"""Empty placeholder migration to satisfy historic dependency.

See notes in 0002_remove_userprofile_bio.py. This is a no-op placeholder
so the existing merge migration can reference it safely.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("user_profile", "0002_remove_userprofile_bio"),
    ]

    operations = [
    ]
