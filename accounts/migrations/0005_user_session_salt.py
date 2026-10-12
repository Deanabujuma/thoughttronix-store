"""Add a per-user ``session_salt`` behind "Sign out of all other devices".

``AddField`` evaluates the callable default once, so every existing row
would share one value; the data step then gives each user their own.
Changing the session hash signs out sessions made before this migration,
once — users simply sign in again.
"""

import secrets

from django.db import migrations, models

import accounts.models


def give_each_user_their_own_salt(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.only("pk"):
        user.session_salt = secrets.token_hex(16)
        user.save(update_fields=["session_salt"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_unique_lowercase_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="session_salt",
            field=models.CharField(
                default=accounts.models.new_session_salt,
                editable=False,
                max_length=32,
            ),
        ),
        migrations.RunPython(give_each_user_their_own_salt, migrations.RunPython.noop),
    ]
