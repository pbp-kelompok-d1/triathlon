"""Empty placeholder migration to satisfy historic dependency.

This project previously had migrations 0002 and 0003 but they are missing
from this working copy. The merge migration (0004_merge_...) references
them. Adding empty placeholder migrations with the expected names resolves
the NodeNotFoundError while preserving a safe, no-op change.

If you have the original migrations in VCS, prefer restoring them. These
stubs are intended as a low-risk repair when original migrations are
unavailable.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("user_profile", "0001_initial"),
    ]

    operations = [
    ]
