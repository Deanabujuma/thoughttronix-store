"""Lowercase every email, then refuse to go on if two accounts share one.

The next migration adds a case-insensitive unique constraint on email.
Rather than pick which account keeps a shared address, this stops with
an error naming the duplicates so a person can resolve them first.
"""

from django.db import migrations
from django.db.models import Count
from django.db.models.functions import Lower


def lowercase_emails(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    for user in User.objects.exclude(email=""):
        if user.email != user.email.lower():
            user.email = user.email.lower()
            user.save(update_fields=["email"])

    duplicates = (
        User.objects.exclude(email="")
        .values(lowered=Lower("email"))
        .annotate(accounts=Count("pk"))
        .filter(accounts__gt=1)
        .order_by("lowered")
    )
    if duplicates:
        lines = []
        for row in duplicates:
            usernames = User.objects.filter(email__iexact=row["lowered"]).order_by(
                "username"
            )
            names = ", ".join(usernames.values_list("username", flat=True))
            lines.append(f"  {row['lowered']}: {names}")
        raise RuntimeError(
            "Cannot make emails unique: these addresses belong to more than "
            "one account (ignoring capitalization):\n"
            + "\n".join(lines)
            + "\nGive each account its own email (or blank it), then migrate again."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_address"),
    ]

    operations = [
        migrations.RunPython(lowercase_emails, migrations.RunPython.noop),
    ]
